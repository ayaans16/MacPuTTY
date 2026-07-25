import paramiko
import socket

def ssh_connection_test(host, port, username, file, timeout=5):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=port,
            username=username,
            key_filename=file,
            timeout=timeout,
        )
        return True, None
    except paramiko.AuthenticationException:
        return False, "Authentication failed"
    except paramiko.BadHostKeyException:
        return False, "Host key verification failed"
    except (paramiko.SSHException, socket.error) as e:
        return False, str(e)
    finally:
        client.close()