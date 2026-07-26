"""Drives the control port like the WASC plugin does: send_ctl.py start|stop|shutdown"""

import socket
import sys

msg = sys.argv[1] if len(sys.argv) > 1 else "start"
with socket.create_connection(("127.0.0.1", 65432), timeout=3) as s:
    s.sendall(msg.encode("utf-8"))
print(f"sent {msg!r}")
