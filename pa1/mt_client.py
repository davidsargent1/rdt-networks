""" Upgraded version made with Claude """
import sys
from socket import socket, AF_INET, SOCK_STREAM

HOST = "localhost"
PORT = 2222
BUFSIZE = 4096


class ResponseReader:
    """Reads protocol responses from a TCP socket. Keeps leftover bytes between calls: since TCP is a byte stream, a recv()
    can return the end of one message together with the start of the next.
    """

    def __init__(self, sock):
        self.sock = sock
        self.buffer = b""

    def _fill(self):
        """Receive one more chunk into the buffer; error if server closed."""
        chunk = self.sock.recv(BUFSIZE)
        if not chunk:
            raise ConnectionError("server closed the connection")
        self.buffer += chunk

    def read_line(self):
        """Return the next line (without its \\n)."""
        while b"\n" not in self.buffer:
            self._fill()
        line, self.buffer = self.buffer.split(b"\n", 1)
        return line

    def read_exact(self, n):
        """Return exactly the next n bytes."""
        while len(self.buffer) < n:
            self._fill()
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def read_response(self):
        """Read one full response; return (code, message, count, body_bytes). COUNT and BYTES are taken from the end of the header so that
        multi-word messages ('NOT FOUND', 'BAD REQUEST') parse correctly.
        """
        parts = self.read_line().decode().split()
        code, message = int(parts[0]), " ".join(parts[1:-2])
        count, nbytes = int(parts[-2]), int(parts[-1])
        body = self.read_exact(nbytes)
        return code, message, count, body


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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    sock = socket(AF_INET, SOCK_STREAM)
    try:
        sock.connect((HOST, port))
    except ConnectionRefusedError:
        print(f"Could not connect to {HOST}:{port} -- is the server running?")
        sys.exit(1)
    print(f"Connected to {HOST}:{port}. Type a query, or 'quit' to exit.")

    reader = ResponseReader(sock)
    try:
        while True:
            try:
                query = input("Enter your query: ").strip()
            except EOFError: # Ctrl+D / end of piped input
                query = "quit"

            if query.lower() == "quit":
                sock.sendall(b"QUIT\n")
                reader.read_response() # wait for "200 BYE" so the server logs a clean exit
                print("Goodbye.")
                break

            sock.sendall(f"GET {query}\n".encode())
            print_response(*reader.read_response())
    except (ConnectionError, ValueError, IndexError) as e:
        # ConnectionError: server went away; ValueError/IndexError: bad header
        print(f"Error talking to server: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
