from datetime import datetime
import custom_shell as shell
from threading import *
from socket import *
import signal
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
    
    #TODO: Implement a simple checksum for the request messages.   
     
    def __init__(self, host: str, port: int, peer_timeout: int = 30, peer_limit: int = 10) -> None:
        """
        Initialises the Tracker server with the given host, port, peer timeout, and peer limit.
        
        :param host: The host address of the tracker.
        :param port: The port on which the tracker listens for incoming connections.
        :param peer_timeout: Time (in seconds) to wait before considering a peer (Seeder or Leecher) as inactive.
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
        
        # Flag to manage tracker shutdown.
        self.running = True
        
        # Register signal handler for graceful shutdown.
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
    def calculate_checksum(message: str) -> str:
        """
        Calculates the SHA-256 checksum for a given message.

        :param message: The input string message.
        :return: The SHA-256 hexadecimal checksum as a string (256-bits).
        """
        return hashlib.sha256(message.encode()).hexdigest()
    
    def shutdown_handler(self, signum: int, frame: None) -> None:
        """
        Handles graceful shutdown when Ctrl+C is pressed.
        
        :param signum: The signal number received.
        :param frame: The current stack frame (unused).
        """
        shell.type_writer_effect(f"\n{shell.BRIGHT_RED}Shutting the tracker down...{shell.RESET}", 0.05)
        tracker.running = False  # Stop the tracker running loop.
        tracker.tracker_socket.close()  # Close the socket.
        shell.type_writer_effect(f"{shell.BRIGHT_GREEN}Tracker shut down successfully! 🚀{shell.RESET}", 0.05)
        
    def start(self) -> None:
        """
        Starts the tracker server and listens for incoming UDP requests from peers.
        Supports graceful shutdown.
        """
        # Display tracker startup messages.
        shell.type_writer_effect("=== PyTorrent Tracker ===", 0.05)
        shell.type_writer_effect(f"{shell.BRIGHT_GREEN}Tracker initialised successfully! 🚀{shell.RESET}", 0.05)
        shell.type_writer_effect(f"Host: {self.host}", 0.05)
        shell.type_writer_effect(f"Port: {self.port}", 0.05)
        shell.type_writer_effect("\nThe tracker is now running and listening for incoming peer requests.", 0.05)
        shell.type_writer_effect("Peers can register, query for files, or request peer lists.", 0.05)
        shell.type_writer_effect("Waiting for connections...", 0.05)
        shell.type_writer_effect(f"\n{shell.BRIGHT_YELLOW}Press Ctrl + C anytime to shut the tracker down ... gracefully!😉{shell.RESET}", 0.05)
         
        while self.running:
            try:
                # Read and decode the message from the UDP socket and get the peer's address.
                message, peer_address = self.tracker_socket.recvfrom(1024)
                request_message = message.decode()
                
                # Create a new thread to process each new peer request.
                request_thread = Thread(target=self.process_peer_requests, args=(request_message, self.tracker_socket, peer_address))
                request_thread.start()
            except OSError:
                break  
            except Exception as e:
                error_message = f"Error receiving data: {e}"
                self.tracker_socket.sendto(error_message.encode(), peer_address)# This will happen when the socket is closed during shutdown.
        
        self.tracker_socket.close()
                
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
                    
        # Checking the request type and processing accordingly.
        request_type = split_request[0]
        if request_type == "REGISTER":
            self.handle_register_requests(split_request, peer_address)
        elif request_type == "LIST_ACTIVE":
            self.list_active_peers(peer_address)
        elif request_type == "LIST_FILES":
            self.list_available_files(peer_address)
        elif request_type == "DISCONNECT":
            self.remove_peer(peer_address)
        elif request_type == "KEEP_ALIVE":
            self.keep_peer_alive(peer_address)
        elif request_type == "PING":
            self.handle_ping_request(peer_address)
        elif request_type == "GET_PEERS":
            self.handle_get_peers_request(split_request, peer_address)
        else:
            error_message = f"400 Unknown request from peer: {request_message}"
            self.tracker_socket.sendto(error_message.encode(), peer_address)
        
    def handle_register_requests(self, split_request: list, peer_address: tuple) -> None:
        """
        Handles peer registration requests.
        
        :param split_request: The split request message sent by the peer.
        :param peer_address: The address of the peer that sent the request.
        """
        # Checking if the registration request has a valid format.
        if len(split_request) < 2:
            error_message = "400 Invalid registration request. Usage: REGISTER <seeder|leecher> [file1, file2, ...]"
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
             
        # Extracting the peer type from the registration request.
        peer_type = split_request[1]
        if peer_type not in ["seeder", "leecher"]:
            error_message = "400 Invalid peer type. Use 'seeder' or 'leecher'."
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
            
        # Extract the files from the request if the requesting peer is a seeder.
        files = split_request[2].split(',') if peer_type == "seeder" and len(split_request) > 2 else []
        self.register_peer(peer_address, peer_type, files) 
        
    def handle_get_peers_request(self, split_request: list, peer_address: tuple) -> None:
        """
        Handles get peers requests.
        
        :param split_request: The split request message sent by the peer.
        :param peer_address: The address of the peer that sent the request.
        """
        # Checking if the get peers request has a valid format.
        if len(split_request) < 2:
            error_message = "400 Invalid request. Usage: GET_PEERS <filename>"
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
       
        filename = split_request[1]
        self.get_peers_for_file(filename, peer_address)    
            
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
        print(response_message)
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
            
    def remove_inactive_peers(self) -> None:
        """
        Periodically removes inactive peers based on timeout.
        """
        while True:
            time.sleep(30)  # Remove inactive peers every 30 seconds.
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
                        
    def get_peers_for_file(self, filename: str, peer_address: tuple) -> None:
        """
        Retrieves a list of peers (seeders) that have the requested file and sends it to the requesting peer.
        
        :param filename: The name of the file being requested.
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Check if the file exists in the file_repository.
            if filename in self.file_repository:
                # Get the list of seeders for the file.
                seeders = self.file_repository[filename]
                response_message = f"200 Peers with {filename}: {seeders}"
            else:
                response_message  = f"404 File not found: {filename}"
                
        # Send the response to the requesting peer.       
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                     
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
        
        :param peer_address: The address of the peer sending the PING request.
        """
        response_message = "200 PONG"
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                                              
if __name__ == '__main__':   
    # Clear the terminal shell and print the PyTorrent Logo.
    shell.clear_shell()
    shell.print_logo()
    
    # Initialise the tracker.
    tracker = Tracker(gethostbyname(gethostname()), 17380)
    
    # Start the peer cleanup thread.
    cleanup_thread = Thread(target = tracker.remove_inactive_peers, daemon = True)
    cleanup_thread.start()
    
    # Start the tracker.
    tracker.start()