# seeder receives message from leecher

import socket 
import threading #To use multiple threads
import time

# define constants
HEADER = 64 # the size of the message will be a minimum of 64 bytes
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = '!exit'
SERVER = socket.gethostname()
ADDR = (SERVER, PORT)

# create seeder socket and bind to address (TCP connection)
seedSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
seedSocket.bind(ADDR)

# method that the initial handshake with client to initiate TCP connection
def handshake(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected = True
    while connected: #wait for connection
        
        msg_length = conn.recv(HEADER).decode(FORMAT)
        
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            
            if msg == DISCONNECT_MESSAGE:
                connected = False
            
            print(f"[{addr}] {msg}") 
            conn.send("Msg received".encode(FORMAT))
            
    conn.close()
 
#after handshake listen for messages from TCP client (leecher)   
def start():
    seedSocket.listen(1)
    print(f"[LISTENING] Server is listening on {SERVER}")
    
    while True: #Wait for msg
        conn, addr = seedSocket.accept()
        
    # use thread to run handshake in the background
        thread = threading.Thread(target=handshake, args=(conn, addr)) # create new thread for handle_clients
        thread.start()
        
        # threading count - 1 because we want to exclude main thread
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        

print("[STARTING] server is starting...")
start()
    
        
