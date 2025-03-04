from socket import *
from threading import *
import time 

class Tracker:
    """
    Pytorrent Tracker Implementation.

    The tracker supports multiple peer UDP connections is responsible for:
    1. Maintaining a list of active network peers.
    2. Responding to leechers with a list of available seeders.
    3. Periodically removing inactive peers from the network.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """    
    
    def __init__(self, host: str, port: int, peer_timeout: int = 100, peer_limit: int = 10) -> None:
        """
        Initialises the Tracker server with the given host, port, peer timeout, and peer limit.
        
        :param host: The host address of the tracker.
        :param port: The port on which the tracker listens for incoming connections.
        :param peer_timeout: Time (in seconds) to wait before considering a peer as inactive.
        :param peer_limit: Maximum number of peers that can be registered with the tracker.
        """
        # Configuring the tracker details.
        self.host = host
        self.port = port
        self.peer_timeout = peer_timeout
        self.peer_limit = peer_limit
         
        # Dictionary storing active peers and their last activity time and lock for thread safety.
        self.active_peers = {}
        self.lock = Lock()
        
        # Initialise the UDP tracker socket using given the host and port.
        self.tracker_socket = socket(AF_INET, SOCK_DGRAM)
        self.tracker_socket.bind((self.host, self.port))
        
    def start(self) -> None:
        """
        Starts the tracker server and listens for incoming UDP requests from peers.
        """
        print(f"Tracker initialized successfully :)")
        print(f"Host: {self.host}, Port: {self.port}")
        print(f"Tracker is now listening for incoming peer requests on UDP port {self.port}!")
         
        while True:
            try:
                # Read and decode the message from the UDP socket and get the peer's address (IP and port).
                message, peer_address = self.tracker_socket.recvfrom(1024)
                request_message = message.decode()
                
                # Create a new thread to process a new request from the peer.
                thread = Thread(target=self.process_peer_requests, args=(request_message, self.tracker_socket, peer_address))
                thread.start()
            except Exception as e:
                self.tracker_socket.sendto("Error receiving data: {e}")
                
    def process_peer_requests(self, request_message: str, peer_socket: socket, peer_address: tuple) -> None:
        """
        Processes incoming peer requests based on the request message string.
        
        :param request_message: The message sent by the peer.
        :param peer_address: The address of the peer that sent the request.
        """
        # Split the incoming request into its different sections.
        split_message = request_message.split()
            
        # Checking the request type and processing accordingly.
        if split_message[0] == "REGISTER":
            self.register_peer(peer_address)
        elif split_message[0] == "LIST_ACTIVE":
            self.list_active_peers(peer_address)
        else:
            error_message = f"400 Unknown request from peer: {request_message}"
            self.tracker_socket.sendto(error_message.encode(), peer_address)
            
    def register_peer(self, peer_address: tuple) -> None:
        """
        Registers a new peer with the tracker if the peer limit is not reached.
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Ensure that we don't exceed the maximum peer limit and register the peer.
            if len(self.active_peers) < self.peer_limit:
                self.active_peers[peer_address] = time.time()
                response_message = f"200 Peer registered: {peer_address} at {time.time()}"
            else:
                response_message = "403 Peer limit reached, registration denied."
        
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                
    def list_active_peers(self, peer_address: tuple):
        """
        Sends a list of currently active peers to the requesting peer. 
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            active_list = list(self.active_peers.keys())
            
        self.tracker_socket.sendto(str(active_list).encode(), peer_address)
                                    
if __name__ == '__main__':
    tracker = Tracker(gethostbyname(gethostname()), 55555)
    tracker.start()