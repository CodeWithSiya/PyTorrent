from threading import *
from socket import *

class Leecher:
    """
    Pytorrent Leecher Implementation.

    The leecher can connect to multiple seeders via a TCP connection and is responsible for:
    1. Registering with the tracker via UDP.
    2. Querying the tracker with its availability.
    2. Hosting a TCP server to send file chunks to leechers.
    3. Notifying the tracker of its availablity.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """    
    def __init__(self, peer_id, ip_address, port):
        
        """
        :param peer_id: Identifier for the peer
        :param ip_address: IP address for the leecher
        :param port: The port number the leecher is listening on
        """
        
        self.peer_id = peer_id
        self.ip_address = ip_address
        self.port = port
        
        self.addr = (self.ip_address, self.port)
        
        #Socket for TCP connection with a seeder
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def register_with_tracker():
        """
        Establish a connection with the tracker
        """   
        pass
    
    def connect_with_seeder(self):
        """
        Establish a TCP connection with a seeder
        """
        self.tcp_socket.connect(self.addr)
        
    
    def connect_with_seeders():
        """
        Establish a TCP connection with multiple seeders in parallel
        """
        pass
        
        
    def download_chunk():
        """
        Download chunk from a seeder
        """
        pass
          
    def download_file(self):
        """
        Download download file from seeder (temporary)
        """
        #recieve filename
        filename = self.tcp_socket.recv(4096).decode()
        
        file = open(filename, "wb")
        
        try:
            while True:
                data = self.tcp_socket.recv(4096) #recieve in chunks
                if not data:
                    break
                #write recieved chunks in file
                file.write(data)
                
        finally:
            print(f"File recieved successfully and saved as '{filename}'")
            file.close()
            
        self.tcp_socket.close()
         
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