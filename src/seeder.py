from threading import *
from socket import *

class Seeder:
    """
    Pytorrent Seeder Implementation.

    The seeder supports multiple leecher TCP connections and is responsible for:
    1. Registering with the tracker via UDP.
    2. Hosting a TCP server to send file chunks to leechers.
    3. Notifying the tracker of its availablity.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """    
    
    #TODO: Speak to group about the home directory apporach.
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, tracker_timeout: int = 30, file_path: str):
        """
        Initialises the Seeder with the given host, UDP port, TCP port, tracker timeout and file path.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        :param tracker_timeout: Time (in seconds) to wait before considering the tracker as unreachable.
        :param file_path: Path to the file to be shared.
        """
        # Configuring the leecher details.
        self.host = host
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.tracker_timeout = tracker_timeout
        self.file_path = file_path # TO BE CHANGED SO DON'T WORRY ABOUT IT TOO MUCH.
        
        # Initialise the UDP socket for tracker communication.
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.udp_port))
        
        # Initialise the TCP socket for leecher connections.
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        
        # Start the TCP server in a seperate thread.
        self.tcp_server_thread = Thread(target=self.start_tcp_server, daemon=True)
        self.tcp_server_thread.start()
        
    def register_with_tracker(self, files: list) -> None:
        """
        Registers this leecher with the tracker.
        
        :param files: The list of available files with this seeder.
        """   
        try:
            # Send a request message to the tracker.
            request_message = f"REGISTER seeder {files}"
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error registering with tracker: {e}")
            
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