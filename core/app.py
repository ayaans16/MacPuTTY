import io
import sys
import zipfile
import tempfile
import importlib.util
from pathlib import Path

from paths import resource_path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from key_pair_gen import (
    generate_rsa_key_pair,
    generate_ecdsa_key_pair,
    generate_ed25519_key_pair,
    ssh_directory,
)
from load_existing_key import get_key_type, pubkey_generation
from comment import add_comment_to_file
from ssh_config_visualizer import get_ssh_config_usage

# redis
import redis, json, os
r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379/0"))

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

# "ssh-connection-test.py" has a hyphen, so it can't be imported with a normal
# `import` statement; load it directly from its file path instead.
_SSH_TEST_PATH = resource_path("ssh", "ssh-connection-test.py")
_ssh_test_spec = importlib.util.spec_from_file_location("ssh_connection_test_module", _SSH_TEST_PATH)
_ssh_test_module = importlib.util.module_from_spec(_ssh_test_spec)
_ssh_test_spec.loader.exec_module(_ssh_test_module)
ssh_connection_test = _ssh_test_module.ssh_connection_test

GENERATORS = {
    "rsa": (generate_rsa_key_pair, "id_rsa", "id_rsa.pub"),
    "ecdsa": (generate_ecdsa_key_pair, "id_ecdsa", "id_ecdsa.pub"),
    "ed25519": (generate_ed25519_key_pair, "id_ed25519", "id_ed25519.pub"),
}


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/generate", methods=["POST"])
def generate_key():
    data = request.get_json(silent=True) or {}
    key_type = (data.get("key_type") or "").lower()

    if key_type not in GENERATORS:
        return jsonify({"error": f"key_type must be one of {list(GENERATORS)}"}), 400

    generate_fn, private_name, public_name = GENERATORS[key_type]
    generate_fn()

    key_dir = Path(ssh_directory).expanduser()
    private_bytes = (key_dir / private_name).read_bytes()
    public_bytes = (key_dir / public_name).read_bytes()

    comment = data.get("comment")
    if comment:
        public_bytes = public_bytes.rstrip(b"\n") + b" " + comment.encode() + b"\n"

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(private_name, private_bytes)
        zf.writestr(public_name, public_bytes)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{key_type}_pair.zip",
    )


@app.route("/upload", methods=["POST"])
def upload_key():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded (expected form field 'file')"}), 400

    uploaded = request.files["file"]
    key_bytes = uploaded.read()
    password = request.form.get("password") or None
    password_bytes = password.encode() if password else None

    try:
        key_type = get_key_type(key_bytes, password_bytes)
        public_key = pubkey_generation(key_bytes, password_bytes)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"key_type": key_type, "public_key": public_key})


@app.route("/comment", methods=["POST"])
def comment_key():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded (expected form field 'file')"}), 400

    comment = request.form.get("comment")
    if not comment:
        return jsonify({"error": "Missing form field 'comment'"}), 400

    uploaded = request.files["file"]

    with tempfile.NamedTemporaryFile(suffix=".pub", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    try:
        add_comment_to_file(tmp_path, comment)
        updated_bytes = Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    buffer = io.BytesIO(updated_bytes)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="text/plain",
        as_attachment=True,
        download_name=uploaded.filename or "id_key.pub",
    )


@app.route("/test-connection", methods=["POST"])
def test_connection():
    host = request.form.get("host")
    username = request.form.get("username")
    port = request.form.get("port")
    timeout = request.form.get("timeout")

    if not host or not username or not port:
        return jsonify({"error": "Missing required field(s): host, port, username"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No key file uploaded (expected form field 'file')"}), 400

    try:
        port = int(port)
    except ValueError:
        return jsonify({"error": "Port must be a number"}), 400

    try:
        timeout = float(timeout) if timeout else 5
    except ValueError:
        return jsonify({"error": "Timeout must be a number"}), 400

    uploaded = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    try:
        Path(tmp_path).chmod(0o600)
        success, error = ssh_connection_test(host, port, username, tmp_path, timeout)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return jsonify({"success": success, "error": error})

@app.route("/ssh-config-usage")
def ssh_config_usage_route():
    mtime = Path(ssh_directory).expanduser().joinpath("config").stat().st_mtime
    key = f"ssh-config-usage:{mtime}"
    cached = r.get(key)
    if cached:
        return jsonify(json.loads(cached))
    result = get_ssh_config_usage(ssh_directory)
    r.setex(key, 10, json.dumps(result))
    return jsonify(result)