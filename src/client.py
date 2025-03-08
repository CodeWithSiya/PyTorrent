from threading import *
from socket import *
import time 

class Client:
    """
    Pytorrent Client Implementation.

    The client can function as either a leecher or a seeder based on its state.
    - As a leecher, it downloads file chunks from seeders and shares them with other leechers.
    - As a seeder, it hosts file chunks and serves them to leechers.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, state: str = "leecher", tracker_timeout: int = 30):
        """
        Initialises the Client with the given host, UDP port, TCP port, state and tracker timeout.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        "param state: The status of the client, either a 'seeder' or 'leecher'
        :param tracker_timeout: Time (in seconds) to wait before considering the tracker as unreachable.
        :param file_path: Path to the file to be shared.
        """
        # Configuring the leecher details.
        self.host = host
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.state = state
        self.tracker_timeout = tracker_timeout
        
        # Dictionary to store downloaded file chunks.
        self.file_chunks = {}
        
        # Initialise the UDP socket for tracker communication.
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.udp_port))
        
        # Initialise the TCP socket for leecher connections.
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        
        # Start the TCP server in a seperate thread.
        self.tcp_server_thread = Thread(target=self.start_tcp_server, daemon=True)
        self.tcp_server_thread.start()
        
    def register_with_tracker(self, files: list = []) -> None:
        """
        Registers the client with the tracker as a leecher.
        
        :param files: The list of available files on this client.
        """
        try:
            # Check the state of the client and create an appropriate request message.
            if self.state == "leecher":
                request_message = f"REGISTER leecher"
            else:
                request_message = f"REGISTER seeder {files}"
            
            # Send a request message to the tracker.
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
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
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker
            response_message, peer_address = self.udp_socket.recvfrom(1024)
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
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
        
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error querying the tracker for available peers: {e}")\
    
    def notify_tracker_alive(self) -> None:
        """
        Notifies the tracker that the leecher is still alive.
        """
        try:
            # Send a request message to the tracker.
            request_message = f"KEEP_ALIVE"
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
        
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
    
    def ping_tracker(self) -> bool:
        """
        Ensures that the tracker is active before attempting to send any messages.
        """
        try:
            # Send a request message to the tracker.
            request_message = f"PING"
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
        
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
            
def main() -> None:
    """
    Main method which runs the PyTorrent client interface.
    """
    