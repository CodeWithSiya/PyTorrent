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
def send(msg):
    message = msg.encode(FORMAT)
    
    #send message
    leechSocket.send(message)
    
    #print response from server (seeder)
    print(leechSocket.recv(2048).decode(FORMAT))
    

    
    
input = input("Input something:\n")
send(input)









