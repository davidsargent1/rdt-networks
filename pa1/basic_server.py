import re
import time
from socket import *

# Read wordlist.txt into a list
with open("wordlist.txt", 'r') as file:
    words = file.read().split()


def find_matching_words(query):
    """ This takes a query and uses regex to find the words that match, returning a list of matching words. """
    clean_query = re.escape(query).replace("\\?", ".")
    matches = [word for word in words if re.search(clean_query, word) is not None]
    return matches


# Server Below - referenced thread-server.py

myHost = "localhost"
myPort = 2222

sock = socket(AF_INET, SOCK_STREAM)        # Socket setup   
sock.bind((myHost, myPort))                   
sock.listen(5)

def dispatcher():
    """ Listens and accepts a connection. Splits into header and query, checks for valid format, and returns
    matching words in the following format: CODE NUM_MATCHES BYTE_LENGTH \n"""
    while True:
        connection, address = sock.accept() # Connection is the incoming data socket  
        print(f'Server connected by {address} at {time.ctime()}')
        msg = connection.recv(1024).decode().strip() # Need to remove whitespace and convert to text
        query = msg[4:]
        
        if "GET " == msg[0:4] and '?' in query:
            matches = find_matching_words(query)
            if len(matches) > 0: # If there is at least one match, we have to send the matches back with the correct code
                encoded_matches = '\n'.join(matches).encode()
                header = f"200 OK {len(matches)} {len(encoded_matches)}\n"
                connection.sendall(header.encode() + encoded_matches)
            else:
                connection.send("404 NOT FOUND 0 0\n".encode()) # No matches
        else:
            connection.send("400 BAD REQUEST 0 0\n".encode()) # Bad format
        
        connection.close()
   
   
dispatcher()