#!/usr/bin/env python3
"""Fake Mac end of the clipboard bridge (for VM-side tests): read to EOF, store, reply OK.
Usage: fake_mac.py OUTFILE [PORT]"""
import socket, sys

out, port = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 47052
srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", port)); srv.listen(8)
while True:
    c, _ = srv.accept()
    data = b""
    while True:
        chunk = c.recv(65536)
        if not chunk:
            break
        data += chunk
    with open(out, "ab") as f:
        f.write(data + b"\n---END---\n")
    c.sendall(b"OK"); c.close()
