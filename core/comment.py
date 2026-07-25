from pathlib import Path

def add_comment_to_file(pubkey_filepath, comment: str) -> None:
    pubkey_filepath = Path(pubkey_filepath).expanduser()
    content = pubkey_filepath.read_text().rstrip("\n")
    updated = f"{content} {comment}\n"
    pubkey_filepath.write_text(updated)

"""
add_comment_to_file("~/test_ssh/id_ed25519.pub", "ayaan@macbook")
"""