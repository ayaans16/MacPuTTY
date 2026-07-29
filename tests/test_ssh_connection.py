import socket

import paramiko


def test_ssh_connection_test_success(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    success, error = ssh_connection_test_module.ssh_connection_test(
        "example.com", 22, "user", "/path/to/key"
    )

    assert success is True
    assert error is None
    mock_client.connect.assert_called_once_with(
        hostname="example.com",
        port=22,
        username="user",
        key_filename="/path/to/key",
        timeout=5,
    )


def test_ssh_connection_test_authentication_failure(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mock_client.connect.side_effect = paramiko.AuthenticationException()
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    success, error = ssh_connection_test_module.ssh_connection_test(
        "example.com", 22, "user", "/path/to/key"
    )

    assert success is False
    assert error == "Authentication failed"


def test_ssh_connection_test_bad_host_key(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mock_client.connect.side_effect = paramiko.BadHostKeyException(
        "example.com", mocker.Mock(), mocker.Mock()
    )
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    success, error = ssh_connection_test_module.ssh_connection_test(
        "example.com", 22, "user", "/path/to/key"
    )

    assert success is False
    assert error == "Host key verification failed"


def test_ssh_connection_test_generic_ssh_exception(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mock_client.connect.side_effect = paramiko.SSHException("connection reset")
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    success, error = ssh_connection_test_module.ssh_connection_test(
        "example.com", 22, "user", "/path/to/key"
    )

    assert success is False
    assert error == "connection reset"


def test_ssh_connection_test_socket_error(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mock_client.connect.side_effect = socket.error("unreachable")
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    success, error = ssh_connection_test_module.ssh_connection_test(
        "example.com", 22, "user", "/path/to/key"
    )

    assert success is False
    assert "unreachable" in error


def test_ssh_connection_test_always_closes_client(ssh_connection_test_module, mocker):
    # Regression test for the very first bug fixed this session:
    # `client.close` with no parentheses never actually closed the connection.
    mock_client = mocker.Mock()
    mock_client.connect.side_effect = paramiko.AuthenticationException()
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    ssh_connection_test_module.ssh_connection_test("example.com", 22, "user", "/path/to/key")

    mock_client.close.assert_called_once()


def test_ssh_connection_test_closes_client_on_success_too(ssh_connection_test_module, mocker):
    mock_client = mocker.Mock()
    mocker.patch.object(
        ssh_connection_test_module.paramiko, "SSHClient", return_value=mock_client
    )

    ssh_connection_test_module.ssh_connection_test("example.com", 22, "user", "/path/to/key")

    mock_client.close.assert_called_once()