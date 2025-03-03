# leecher send message to seeder (testing)
import socket

# Define constants
HEADER = 64 # the size of the message will be a minimum of 64 bytes
PORT = 5050
FORMAT = "utf-8"
DISCONNECT_MESSAGE = '!exit'
SERVER = socket.gethostname()
ADDR = (SERVER, PORT)

# create TCP socket and connect
leechSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
leechSocket.connect(ADDR)

# send message to seeder
def send_text(msg):
    message = msg.encode(FORMAT)
    
    #send message
    leechSocket.send(message)
    
    #print response from server (seeder)
    print(leechSocket.recv(2048).decode(FORMAT))

def get_file(filename):
    file = open(filename, "wb")
    
    try:
        while True:
            data = leechSocket.recv(4096) #recieve in chunks
            if not data:
                break
            file.write(data)
            
    finally:
        print(f"File recieved successfully and saved as '{filename}'")
        file.close()
        
    leechSocket.close()
        
        
    
input = input("What would you like to do?\n")
send_text(input)
get_file("test_out.txt")









