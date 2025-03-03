# seeder receives message from leecher

import socket 
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

 
#after handshake listen for messages from TCP client (leecher)   
def start():
    seedSocket.listen(1)
    print(f"[LISTENING] Server is listening on {SERVER}")
    
    #count number of active connections
    activeCount = 0
    
    while True: #Wait for msg
        
        #create new socket for sending messages
        conn, addr = seedSocket.accept()
        activeCount += 1
        print(f"Connected by {addr} | Total leechers: {activeCount}")
    
        
        message = conn.recv(1024).decode(FORMAT)
        
        print(f"Client said '{message}'")
        conn.send("Msg recieved :)".encode(FORMAT))
         
        conn.close()
        
        
        

print("[STARTING] server is starting...")
start()
    
        
