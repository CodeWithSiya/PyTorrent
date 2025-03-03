# seeder receives message from leecher
import socket 
import time

# define constants
HEADER = 64 # the size of the message will be a minimum of 64 bytes
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = '!exit'
GET_FILE_MESSAGE = "file"
SERVER = socket.gethostname()
ADDR = (SERVER, PORT)
filename = "test_in.txt"


#send a file to the leecher
def send_file(filename, conn):
    #open file in byte mode
    file = open(filename, "rb")
    
    try:
        while True:
            # read in chunks
            chunk = file.read(4096)
            if not chunk:
                break
            conn.send(chunk)
    finally:
        print("File sent successfully.")
        file.close()
        
        
    


# create seeder socket and bind to address (TCP connection)
seedSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
seedSocket.bind(ADDR)

 
#listen for messages from TCP client (leecher)   
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
        
        
        if (message == GET_FILE_MESSAGE):
            conn.send("Sending file...".encode(FORMAT))
                
            send_file(filename, conn)
        
         
        conn.close()
        
        
        

print("[STARTING] server is starting...")
start()
    
        
