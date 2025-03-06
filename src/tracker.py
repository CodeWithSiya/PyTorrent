from datetime import datetime
from threading import *
from socket import *
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
    
    # TODO: Refactor code to minimize nested if statements.
    # TODO: Specify that when registering a seeder, must provide files.
    # TODO: Implement functionality to GET_PEERS.
    # TODO: Implement some way to verify that a message has been received correctly -> VERIFICATION & RELIABILITY BASICALLY.
    # TODO: Where should the files be stored? This is the most confusing part to me!
    # TODO: Fix commenting and respose messages (Should be of a proper format!)
    # TODO: Implement some type of way to know which peers have which files.
    # TODO: Implement some fixed length hashing for verification
    # TODO: Scan through a specific directory upon registration, then add the files to the request message while registering.
    
    def __init__(self, host: str, port: int, peer_timeout: int = 5, peer_limit: int = 10) -> None:
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
         
        # Dictionary storing active peers and their last activity time, file repository and lock for thread safety.
        self.active_peers = {}
        self.file_repository = {}
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
                # Read and decode the message from the UDP socket and get the peer's address.
                message, peer_address = self.tracker_socket.recvfrom(1024)
                request_message = message.decode()
                
                # Create a new thread to process each new peer request.
                request_thread = Thread(target=self.process_peer_requests, args=(request_message, self.tracker_socket, peer_address))
                request_thread.start()
            except Exception as e:
                error_message = f"Error receiving data: {e}"
                self.tracker_socket.sendto(error_message.encode(), peer_address)
                
    def process_peer_requests(self, request_message: str, peer_socket: socket, peer_address: tuple) -> None:
        """
        Processes incoming peer requests based on the request message string.
        
        :param request_message: The message sent by the peer.
        :param peer_socket: The socket of the peer that sent the request.
        :param peer_address: The address of the peer that sent the request.
        """
        # Split the incoming request into its different sections.
        split_request = request_message.split()
        
        # Ensure that the request is not empty.
        if not split_request:
            error_message = f"400 Empty request from peer: {request_message}"
            self.tracker_socket.sendto(error_message.encode(), peer_address)
            return
        
        # Extracting the request type from the received message.
        request_type = split_request[0]
            
        # Checking the request type and processing accordingly.
        if request_type == "REGISTER":
            # Checking if the registration request has a valid format.
            if len(split_request) < 2:
                error_message = "400 Invalid registration request. Usage: REGISTER <seeder|leecher> [file1, file2, ...]"
                self.tracker_socket.sendto(error_message.encode(), peer_address)
                return       
            # Extracting the peer type from the registration request.
            peer_type = split_request[1]
            if peer_type not in ["seeder", "leecher"]:
                error_message = "400 Invalid peer type. Use 'seeder' or 'leecher'."
                self.tracker_socket.sendto(error_message.encode(), peer_address)
                return
            # Extract the files from the request if the requesting peer is a seeder.
            files = split_request[2].split(',') if peer_type == "seeder" and len(split_request) > 2 else []
            self.register_peer(peer_address, peer_type, files)
            return                   
        if request_type == "LIST_ACTIVE":
            self.list_active_peers(peer_address)
            return
        if request_type == "LIST_FILES":
            self.list_available_files(peer_address)
            return
        if request_type == "DISCONNECT":
            self.remove_peer(peer_address)
            return
        if request_type == "KEEP_ALIVE":
            self.keep_peer_alive(peer_address)
            return
        if request_type == "PING":
            self.handle_ping_request(peer_address)
            return
        if request_type == "GET_PEERS":
            if len(split_message) < 2:
                error_message = "400 Invalid request. Usage: GET_PEERS <filename>"
                self.tracker_socket.sendto(error_message.encode(), peer_address)
            else:
                filename = split_message[1]
                self.get_peers_for_file(filename, peer_address)
        error_message = f"400 Unknown request from peer: {request_message}"
        self.tracker_socket.sendto(error_message.encode(), peer_address)
            
    def register_peer(self, peer_address: tuple, peer_type: str, files: list) -> None:
        """
        Registers a new peer with the tracker if the peer limit is not reached.
        
        :param peer_address: The address of the peer that sent the request.
        :param peer_type: The type of the peer, either 'seeder' or 'leecher'.
        :param files: A list of files the peer has (if it's a seeder).
        """
        with self.lock:
            # Ensure that we don't exceed the maximum peer limit and register the peer.
            if len(self.active_peers) < self.peer_limit:
                self.active_peers[peer_address] = {
                    'last_activity': time.time(), 
                    'type': peer_type,
                    'files': files if peer_type == "seeder" else []
                }
                # If the peer is a seeder, update the file_repository.
                if peer_type == 'seeder' and files:
                    for file in files:
                        if file not in self.file_repository:
                            self.file_repository[file] = []
                        self.file_repository[file].append(peer_address)
                    response_message = f"200 Peer registered: {peer_address} as {peer_type} with files: {files}"
                else:
                    response_message = f"200 Peer registered: {peer_address} as {peer_type}"
            else:
                response_message = "403 Peer limit reached, registration denied."
                
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                
    def list_active_peers(self, peer_address: tuple) -> None:
        """
        Sends a list of currently active peers (seeders and leechers) to the requesting peer.
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Obtain the active seeders and leechers and list them out.
            active_seeders = [peer for peer, info in self.active_peers.items() if info['type'] == 'seeder']
            active_leechers = [peer for peer, info in self.active_peers.items() if info['type'] == 'leecher']
            active_list = {'seeders': active_seeders, 'leechers': active_leechers}
            
        self.tracker_socket.sendto(str(active_list).encode(), peer_address)
        
    def list_available_files(self, peer_address: tuple) -> None:
        """
        Obtains a list of the files available in the tracker file repository.
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Obtain a list of the files available in the tracker file repository.
            available_files = list(self.file_repository.keys())
            
        self.tracker_socket.sendto(str(available_files).encode(), peer_address)
        
    def remove_peer(self, peer_address: tuple) -> None:
        """
        Removes a peer from the active list when it disconnects.
        """
        with self.lock:
            # Only remove the peer from the network if found in active peers.
            if peer_address in self.active_peers:
                # Remove the peer from the file repository for each file it had.
                if self.active_peers[peer_address]['type'] == 'seeder':
                    for file in self.active_peers[peer_address]['files']:
                        if file in self.file_repository and peer_address in self.file_repository[file]:
                            self.file_repository[file].remove(peer_address)
                            # If no more seeders, remove the file from the repository.
                            if not self.file_repository[file]:
                                del self.file_repository[file]
                del self.active_peers[peer_address]
                response_message = f"400 Peer successfully removed: {peer_address}"
            else:
                response_message = f"403 Peer not found in active list: {peer_address}"
                
        self.tracker_socket.sendto(response_message.encode(), peer_address)
            
    # TODO: FIX!
    def remove_inactive_peers(self) -> None:
        """
        Periodically removes inactive peers based on timeout.
        """
        while True:
            time.sleep(30)  # Remove inactive peers every 5 seconds.
            with self.lock:
                current_time = time.time()
                for peer in list(self.active_peers.keys()):
                    if current_time - self.active_peers[peer]['last_activity'] > self.peer_timeout:
                        # TODO: Alert the user that their device is going to timeout before timing out!
                        if self.active_peers[peer]['type'] == 'seeder':
                            for file in self.active_peers[peer]['files']:
                                if file in self.file_repository and peer in self.file_repository[file]:
                                    self.file_repository[file].remove(peer)
                                    # If no more seeders, remove the file from the repository.
                                    if not self.file_repository[file]:
                                        del self.file_repository[file]
                        del self.active_peers[peer]
                        print("Clean-up performed at: " + str(datetime.now()))
    
    # TODO: ENSURE THAT ALL METHODS HAVE THIS TYPE OF DOCUMENTATION.                   
    def keep_peer_alive(self, peer_address: tuple):
        """
        Updates the last activity time of a peer to keep it active in the tracker.
        If the peer is found, its timestamp is refreshed; otherwise, an error is returned.

        :param peer_address: The address of the peer that sent the "KEEP_ALIVE" request.
    
        Sends a response:
        - "400 Peer's last activity time updated" if the peer is active.
        - "403 Peer not found" if the peer is not in the active list.
        """
        with self.lock:
            # Update the peer's last activity time to avoid time out if found in the active list.
            if peer_address in self.active_peers:
                self.active_peers[peer_address]['last_activity'] = time.time()
                response_message = f"400 Peer's last activity time successfully updated: {peer_address}"
            else:
                response_message = f"403 Peer not found in active list: {peer_address}"
                        
        self.tracker_socket.sendto(response_message.encode(), peer_address)
        
    def handle_ping_request(self, peer_address: tuple) -> None:
        """
        Handles a PING request from a peer and responds with a PONG message.
        - Ensures that the tracker is active before attempting to send any messages.
        
        :param peer_address: The address of the peer sending the PING request.
        """
        response_message = "200 PONG"
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                                       
if __name__ == '__main__':    
    # Initialise the tracker.
    tracker = Tracker(gethostbyname(gethostname()), 55555)
    
    # Start the peer cleanup thread.
    cleanup_thread = Thread(target = tracker.remove_inactive_peers, daemon = True)
    cleanup_thread.start()
    
    # Start the tracker.
    tracker.start()