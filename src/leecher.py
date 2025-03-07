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
    
    #TODO: Consider using the `selectors` module for multiplexing instead of relying on threads.
     
    def __init__(self, host: str, udp_port: int, tcp_port: int, tracker_timeout: int = 30):
        """
        Initialises the Leecher with the given host, UDP port, TCP port and tracker timeout.
        
        :param host: The host address of the tracker.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        :param tracker_timeout: Time (in seconds) to wait before considering the tracker as unreachable.
        """
        # Configuring the leecher details.
        self.host = host
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.tracker_timeout = tracker_timeout
        
        # Dictionary to store downloaded file chunks.
        self.file_chunks = {}
        
        # Initialise the UDP socket for tracker communication.
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.udp_port))
        
        # Initialise the TCP socket for file sharing.
        self.tcp_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        
        # Start the TCP server in a seperate thread.
        self.tcp_server_thread = Thread(target=self.start_tcp_server, daemon=True)
        self.tcp_server_thread.start()
    
    def register_with_tracker(self) -> None:
        """
        Registers this leecher with the tracker.
        """   
        try:
            # Send a request message to the tracker.
            request_message = "REGISTER leecher"
            self.udp_socket.sentto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker.
            response_message, peer_address = udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error registering with tracker: {e}")
            
    def query_tracker_for_files(self) -> None:
        """
        Queries the tracker for files available in the network (At least one seeder has the file).
        """
        try:
            # Send a request message to the tracker.
            request_message = "LIST_FILES"
            self.udp_socket.sentto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker
            response_message, peer_address = udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error querying the tracker for files: {e}")
            
    def query_tracker_for_peers(self, filename: str) -> None:
        """
        Queries the tracker for the a list of peers (seeders) that have a specified file.
        
        :param filename: The name of the file being requested.
        """
        try:
            # Send a request message to the tracker.
            request_message = f"GET_PEERS {filename}"
        
            # Receive a response message from the tracker.
            response_message, peer_address = udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error querying the tracker for available peers: {e}")
              
    # def connect_with_seeder(self):
    #     """
    #     Establish a TCP connection with a seeder
    #     """
    #     #self.tcp_socket.connect(self.addr)
        
    
    # def connect_with_seeders():
    #     """
    #     Establish a TCP connection with multiple seeders in parallel
    #     """
    #     pass
        
        
    # def download_chunk():
    #     """
    #     Download chunk from a seeder
    #     """
    #     pass
          
    # def download_file(self):
    #     """
    #     Download download file from seeder (temporary)
    #     """
    #     #recieve filename
    #     filename = self.tcp_socket.recv(4096).decode()
        
    #     file = open(filename, "wb")
        
    #     try:
    #         while True:
    #             data = self.tcp_socket.recv(4096) #recieve in chunks
    #             if not data:
    #                 break
    #             #write recieved chunks in file
    #             file.write(data)
                
    #     finally:
    #         print(f"File recieved successfully and saved as '{filename}'")
    #         file.close()
            
    #     self.tcp_socket.close()
         
    # def resassemble_file():
    #     """
    #     Reassemble file from the downloaded chunks
    #     """
    #     pass
        
    # def become_seeder():
    #     """
    #     Become a seeder after downloading a file
    #     """
    #     pass