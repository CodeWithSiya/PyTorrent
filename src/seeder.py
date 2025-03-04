# seeder receives message from leecher
import socket 
import time
import threading

# define constants
HEADER = 64 # the size of the message will be a minimum of 64 bytes
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = '!exit'
DOWNLOAD_MESSAGE = '!download'
SERVER = socket.gethostname()
ADDR = (SERVER, PORT)
filename = "65.png"


#send a file to the leecher
def send_file(filename, conn):

    
    wait = True
    while wait: #wait for signal to start sending
        
        #get signal
        msg = conn.recv(HEADER).decode(FORMAT)
        
        if msg == DOWNLOAD_MESSAGE:
            wait = False
            
    #send the filename of file being sent
    conn.send(filename.encode(FORMAT))
        
    
    #open file in byte mode
    file = open(filename, "rb")
    
    
    
    try:
        while True:
            # read in chunks
            chunk = file.read(4096)
            if not chunk:
                break
            #send chunks
            conn.send(chunk)
    finally:
        print("File sent successfully.")
        file.close()
        
        #after file is sent close connection
        conn.close()
        
        
    


# create seeder socket and bind to address (TCP connection)
seedSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
seedSocket.bind(ADDR)

 
#listen for messages from TCP client (leecher)   
def start():
    #listen for new connections
    seedSocket.listen(1)
    print(f"[LISTENING] Server is listening on {SERVER}")
    
    
    while True: #Wait for msg
        
        #create new socket for sending messages
        conn, addr = seedSocket.accept()
        
        #start a thread to send a file
        thread = threading.Thread(target=send_file, args=(filename, conn))
        thread.start()

        print(f"Connected by {addr} | Total leechers: {threading.active_count() - 1}")
             
        
        
        

print("[STARTING] server is starting...")
start()
    
        
