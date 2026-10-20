import time     
from socket import *                     
                       
# Client socket
sock = socket(AF_INET, SOCK_STREAM)           
sock.connect(("localhost", 2222))
print(f'Connected to Server localhost:2222 at {time.ctime()}')

# Create and send query
query = input("Enter your query: ")
sock.sendall(f"GET {query}\n".encode())


buffer = b""
while True:
    result = sock.recv(4096)
    if result == b"":
        break
    else:
        buffer += result
        
print(buffer.decode())
sock.close()
    

