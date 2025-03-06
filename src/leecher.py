# leecher send message to seeder (testing)
import socket


class Leecher:
    
    def __init__(self, peer_id, ip_address, port):
        
        self.peer_id = peer_id
        self.ip_address = ip_address
        self.port = port
    
    def register_with_tracker():
        """
        Establish a connection with the tracker
        """   
        pass
        
    def request_seeder_list():
        """
        Request a list of seeders from the tracker
        """
        pass
        
        
    def download_chunk():
        """
        Download chunk from a seeder
        """
        pass
        
        
    def download_file():
        """
        Download chuncks from different seeders in parallel
        """
        pass
        
    def resassemble_file():
        """
        Reassemble file from the downloaded chunks
        """
        pass
        
    def become_seeder():
        """
        Become a seeder after downloading a file
        """
        pass
        
        
        
        
        
        

    # Define constants
    HEADER = 64 # the size of the message will be a minimum of 64 bytes
    PORT = 5050
    FORMAT = "utf-8"
    DISCONNECT_MESSAGE = '!exit'
    DOWNLOAD_MESSAGE = '!download'
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
        

    def get_file():
        
        #recieve filename
        filename = leechSocket.recv(HEADER).decode(FORMAT)
        
        file = open(filename, "wb")
        
        try:
            while True:
                data = leechSocket.recv(4096) #recieve in chunks
                if not data:
                    break
                #write recieved chunks in file
                file.write(data)
                
        finally:
            print(f"File recieved successfully and saved as '{filename}'")
            file.close()
            
        leechSocket.close()
            
            
    input()
    send_text(DOWNLOAD_MESSAGE)
    get_file()









