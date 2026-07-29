import io
import zipfile

import pytest


@pytest.fixture
def client():
    import core.app as app_module

    return app_module.app.test_client()


def test_health_endpoint(client):
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_generate_invalid_key_type(client, fake_ssh_dir):
    resp = client.post("/generate", json={"key_type": "not-a-real-type"})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_generate_returns_zip_with_both_files(client, fake_ssh_dir):
    resp = client.post("/generate", json={"key_type": "ed25519"})

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    assert set(zf.namelist()) == {"id_ed25519", "id_ed25519.pub"}


def test_generate_applies_comment_to_public_key(client, fake_ssh_dir):
    resp = client.post(
        "/generate", json={"key_type": "ed25519", "comment": "ayaan@macbook"}
    )

    zf = zipfile.ZipFile(io.BytesIO(resp.data))
    public_key_text = zf.read("id_ed25519.pub").decode()
    assert public_key_text.strip().endswith("ayaan@macbook")


def test_upload_missing_file_field(client):
    resp = client.post("/upload", data={})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_upload_valid_ed25519_key_returns_type_and_pubkey(client, fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ed25519_key_pair()
    private_bytes = (fake_ssh_dir / "id_ed25519").read_bytes()

    resp = client.post(
        "/upload",
        data={"file": (io.BytesIO(private_bytes), "id_ed25519")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["key_type"] == "ED25519"
    assert body["public_key"].startswith("ssh-ed25519 ")


def test_comment_missing_file_field(client):
    resp = client.post("/comment", data={"comment": "ayaan@macbook"})

    assert resp.status_code == 400


def test_comment_missing_comment_field(client, fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ed25519_key_pair()
    public_bytes = (fake_ssh_dir / "id_ed25519.pub").read_bytes()

    resp = client.post(
        "/comment",
        data={"file": (io.BytesIO(public_bytes), "id_ed25519.pub")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400


def test_comment_appends_comment_to_uploaded_key(client, fake_ssh_dir):
    import core.key_pair_gen

    core.key_pair_gen.generate_ed25519_key_pair()
    public_bytes = (fake_ssh_dir / "id_ed25519.pub").read_bytes()

    resp = client.post(
        "/comment",
        data={
            "file": (io.BytesIO(public_bytes), "id_ed25519.pub"),
            "comment": "ayaan@macbook",
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.data.decode().strip().endswith("ayaan@macbook")


def test_test_connection_missing_required_fields(client):
    resp = client.post("/test-connection", data={})

    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_test_connection_missing_key_file(client):
    resp = client.post(
        "/test-connection",
        data={"host": "example.com", "port": "22", "username": "user"},
    )

    assert resp.status_code == 400


def test_test_connection_invalid_port(client):
    resp = client.post(
        "/test-connection",
        data={
            "host": "example.com",
            "port": "not-a-number",
            "username": "user",
            "file": (io.BytesIO(b"fake key content"), "id_ed25519"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "Port" in resp.get_json()["error"]


def test_test_connection_invalid_timeout(client):
    resp = client.post(
        "/test-connection",
        data={
            "host": "example.com",
            "port": "22",
            "username": "user",
            "timeout": "not-a-number",
            "file": (io.BytesIO(b"fake key content"), "id_ed25519"),
        },
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert "Timeout" in resp.get_json()["error"]


def test_ssh_config_usage_endpoint(client, fake_ssh_dir):
    (fake_ssh_dir / "id_ed25519").touch()
    (fake_ssh_dir / "config").write_text(
        "Host github.com\n"
        "    HostName github.com\n"
        "    User git\n"
        f"    IdentityFile {fake_ssh_dir}/id_ed25519\n"
    )

    resp = client.get("/ssh-config-usage")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["config_exists"] is True
    assert body["hosts"][0]["host"] == "github.com"
    assert body["hosts"][0]["identity_files"][0]["exists"] is True


def test_ssh_config_usage_endpoint_no_config_file(client, fake_ssh_dir):
    resp = client.get("/ssh-config-usage")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["config_exists"] is False
    assert body["hosts"] == []