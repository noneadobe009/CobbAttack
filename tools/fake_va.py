"""Stands in for the WASC plugin: prints whatever would have fired in VoiceAttack."""

import socket

PORT = 65433

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", PORT))
server.listen(4)
print(f"[fake VoiceAttack] listening on 127.0.0.1:{PORT} — Ctrl+C to quit")
while True:
    conn, _ = server.accept()
    with conn:
        data = conn.recv(4096)
    print(f"[fake VoiceAttack] would execute: {data.decode('utf-8', errors='replace')!r}")
