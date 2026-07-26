from pathlib import Path
import paramiko

def _is_wildcard_host(host: str) -> bool:
    return any(ch in host for ch in "*?")

def _resolve_identity_file(raw_path: str, ssh_directory: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        return Path(ssh_directory).expanduser() / raw_path
    if path.is_file():
        return path

    fallback = Path(ssh_directory).expanduser() / path.name
    return fallback if fallback.is_file() else path

def get_ssh_config_usage(ssh_directory: str) -> dict:
    config_path = Path(ssh_directory).expanduser() / "config"

    if not config_path.is_file():
        return {"config_path": str(config_path), "config_exists": False, "hosts": []}

    ssh_config = paramiko.config.SSHConfig()
    with config_path.open() as f:
        ssh_config.parse(f)

    hosts = []
    for host in sorted(ssh_config.get_hostnames()):
        if _is_wildcard_host(host):
            continue

        lookup = ssh_config.lookup(host)
        identity_files = [
            {
                "path": raw_path,
                "exists": _resolve_identity_file(raw_path, ssh_directory).is_file(),
            }
            for raw_path in lookup.get("identityfile", [])
        ]

        hosts.append(
            {
                "host": host,
                "hostname": lookup.get("hostname", host),
                "user": lookup.get("user"),
                "port": lookup.get("port"),
                "identity_files": identity_files,
            }
        )

    return {"config_path": str(config_path), "config_exists": True, "hosts": hosts}