""" Upgraded version made with Claude """
import re
import sys
import threading
import time
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR

HOST = "localhost"
PORT = 2222
BUFSIZE = 4096
MAX_REQUEST = 1024 # longest request line accepted, in bytes

# Load words into a list
with open("wordlist.txt", "r") as f:
    WORDS = f.read().split()


def now():
    """Current time on the server, for log messages (from thread-server.py)."""
    return time.ctime(time.time())


def log(msg):
    """Print a log line tagged with the current thread's name."""
    print(f"[{now()}] [{threading.current_thread().name}] {msg}")


def find_matching_words(query):
    """Return all words that contain `query`, where '?' matches any one character. """
    pattern = re.compile(re.escape(query).replace("\\?", "."))
    return [word for word in WORDS if pattern.search(word)]


def make_response(code, message, words=()):
    """Build one complete response (header + body) as bytes."""
    body = "\n".join(words).encode()
    header = f"{code} {message} {len(words)} {len(body)}\n".encode()
    return header + body


def handle_request(line):
    """Turn one request line into (response_bytes, keep_connection_open)."""
    if line == "QUIT":
        return make_response(200, "BYE"), False

    if not line.startswith("GET "):
        return make_response(400, "BAD REQUEST"), True

    query = line[4:]
    if not query or "?" not in query:
        return make_response(400, "BAD REQUEST"), True

    matches = find_matching_words(query)
    if matches:
        return make_response(200, "OK", matches), True
    return make_response(404, "NOT FOUND"), True


def handle_client(connection, address):
    """Serve one client (runs in its own thread) until QUIT or disconnect. """
    log(f"connected: {address}")
    buffer = b""
    try:
        while True:
            # Read until at least one full request line is buffered.
            while b"\n" not in buffer:
                if len(buffer) > MAX_REQUEST:
                    connection.sendall(make_response(400, "BAD REQUEST"))
                    log(f"request too long from {address}, closing")
                    return
                chunk = connection.recv(BUFSIZE)
                if not chunk:  # client closed the connection
                    log(f"client {address} disconnected")
                    return
                buffer += chunk

            raw, buffer = buffer.split(b"\n", 1)
            line = raw.decode(errors="replace").strip()
            response, keep_open = handle_request(line)
            connection.sendall(response)
            log(f"{address} {line!r} -> {response.split(b' ', 1)[0].decode()}")

            if not keep_open:
                return
    except (ConnectionResetError, BrokenPipeError):
        log(f"connection to {address} lost")
    finally:
        connection.close() # always release the socket


def dispatcher(server_sock):
    """Accept clients forever, handing each to a new thread. """
    while True:
        connection, address = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(connection, address), daemon=True)
        t.start()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server_sock = socket(AF_INET, SOCK_STREAM)
    server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # allow quick restarts
    server_sock.bind((HOST, port))
    server_sock.listen(5)
    log(f"loaded {len(WORDS)} words; listening on {HOST}:{port}")
    try:
        dispatcher(server_sock)
    except KeyboardInterrupt:
        log("shutting down")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
