from socket import *
from threading import *

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
     
    def __init__(self, host: str, port: int, peer_timeout: int = 100, peer_limit: int = 10):
        """
        Initialises the Tracker server with the given host, port, peer timeout, and peer limit.
        """
        # Configuring the tracker.
        self.host = host
        self.port = port
        self.peer_timeout = peer_timeout
        self.peer_limit = peer_limit
         
        # Dictionary storing active peers and their last activity time.
        self.active_peers = {}
        self.lock = Lock()
        
        # Initialise the UDP tracker socket using given host and port.
        # TODO: Move this into its own method at some stage!
        self.tracker_socket = socket(AF_INET, SOCK_DGRAM)
        self.tracker_socket.bind((self.host, self.port))
        
    def start(self):
        """
        Starts the tracker server and listens for incoming peer requests.
        """
        print(f"Tracker started on {self.host}:{self.port}")
        
        while True:
            try:
                message, peer_address = self.tracker_socket.recvfrom(2048)
                request_message = message.decode()
                self.process_peer_requests(request_message, peer_address)
            except Exception as e:
                print(f"Error receiving data: {e}")
             
if __name__ == '__main__':
    tracker = Tracker(gethostbyname(gethostname()), 55555)
    tracker.start()