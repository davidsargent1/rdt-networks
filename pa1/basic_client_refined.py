"""
basic_client_refined.py -- AI-refined version of basic_client.py (single query).

Written with Claude (Anthropic, model Opus 5.5) after my own basic_client.py
was working. Changes from my v1:
  - Parses the response header (CODE MESSAGE COUNT BYTES) instead of
    printing raw bytes.
  - Reads exactly BYTES bytes of body, so it does not rely on the server
    closing the connection to know the response has ended.
  - Prints the number of matches and then each word, as the assignment asks.
  - Handles the server being down or closing the connection early.
"""

import sys
from socket import socket, AF_INET, SOCK_STREAM

HOST = "localhost"
PORT = 2222
BUFSIZE = 4096


def recv_line(sock, buffer):
    """Receive until buffer holds a full line ending in \\n.

    Returns (line_without_newline, leftover_bytes). The leftover bytes are the
    start of whatever came after the line (here: the response body), which
    must not be thrown away. Raises ConnectionError if the server closes first.
    """
    while b"\n" not in buffer:
        chunk = sock.recv(BUFSIZE)
        if not chunk:                                  # server closed connection
            raise ConnectionError("server closed connection before header ended")
        buffer += chunk
    line, leftover = buffer.split(b"\n", 1)            # split at FIRST newline only
    return line, leftover


def recv_exact(sock, n, buffer):
    """Receive until buffer holds at least n bytes; return (first n, leftover)."""
    while len(buffer) < n:
        chunk = sock.recv(BUFSIZE)
        if not chunk:
            raise ConnectionError(f"server closed connection after {len(buffer)} of {n} bytes")
        buffer += chunk
    return buffer[:n], buffer[n:]


def parse_header(line):
    """Split a header line into (code, message, count, nbytes).

    COUNT and BYTES are read from the END of the line, so multi-word messages
    like 'NOT FOUND' and 'BAD REQUEST' do not shift the fields.
    """
    parts = line.decode().split()
    code = int(parts[0])
    message = " ".join(parts[1:-2])
    count = int(parts[-2])
    nbytes = int(parts[-1])
    return code, message, count, nbytes


def print_response(code, message, count, body):
    """Display a response to the user according to its status code."""
    if code == 200:
        print(f"{count} matching word(s):")
        for word in body.decode().split("\n"):
            print(word)
    elif code == 404:
        print("0 matching words (404 NOT FOUND)")
    else:
        print(f"Server error: {code} {message}")


def main():
    sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{PORT} -- is the server running?")
        sys.exit(1)

    try:
        query = input("Enter your query: ").strip()
        sock.sendall(f"GET {query}\n".encode())

        line, leftover = recv_line(sock, b"")
        code, message, count, nbytes = parse_header(line)
        body, _ = recv_exact(sock, nbytes, leftover)
        print_response(code, message, count, body)
    except (ConnectionError, ValueError, IndexError) as e:
        # ValueError/IndexError: header was not in the expected format
        print(f"Error talking to server: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
