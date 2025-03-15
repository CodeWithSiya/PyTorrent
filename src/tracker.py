from datetime import datetime
import custom_shell as shell
from threading import *
from socket import *
import signal
import json
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
        shell.type_writer_effect(f"\n{shell.BRIGHT_YELLOW}Press Ctrl + C anytime to shut the tracker down ... gracefully!😉\n{shell.RESET}", 0.05)
        shell.type_writer_effect("=== Tracker Activity ===", 0.05)
         
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
            username = split_request[1] if len(split_request) == 2 else "unknown"
            self.list_active_peers(peer_address, username)
        elif request_type == "LIST_FILES":
            self.list_available_files(peer_address)
        elif request_type == "DISCONNECT":
            username = split_request[1] if len(split_request) == 2 else "unknown"
            self.remove_peer(peer_address, username)
        elif request_type == "KEEP_ALIVE":
            username = split_request[1] if len(split_request) == 2 else "unknown"
            self.keep_peer_alive(peer_address, username)
        elif request_type == "PING":
            self.handle_ping_request(peer_address)
        elif request_type == "GET_PEERS":
            self.handle_get_peers_request(split_request, peer_address)
        else:
            error_message = f"400 Bad Request: Unknown request type."
            self.tracker_socket.sendto(error_message.encode(), peer_address)
        
    def handle_register_requests(self, split_request: list, peer_address: tuple) -> None:
        """
        Handles peer registration requests.
        
        :param split_request: The split request message sent by the peer.
        :param peer_address: The address of the peer that sent the request.
        """
        # Checking if the registration request has a valid format.
        if len(split_request) < 3:
            error_message = "400 Bad Request: Usage: REGISTER <seeder|leecher> <username> [JSON file data]"
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
             
        # Extracting the peer type from the registration request.
        peer_type = split_request[1]
        if peer_type not in ["seeder", "leecher"]:
            error_message = "400 Bad Request: Invalid peer type. Use 'seeder' or 'leecher'."
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
        
        # Extract the username from the request.
        username = split_request[2]
            
        # Extract the files from the request if the requesting peer is a seeder.
        files = []
        if peer_type == "seeder":
            if len(split_request) < 4:
                error_message = "400 Bad Request: Missing JSON metadata for seeder."
                return self.tracker_socket.sendto(error_message.encode(), peer_address)
            
            try:
                # Parse the JSON file data.
                json_data_str = ' '.join(split_request[3:])
                metadata = json.loads(json_data_str)
                if "files" in metadata:
                    files = metadata["files"] 
                else:
                    error_message = "400 Bad Request: Invalid JSON metadata. 'files' field is missing."
                    return self.tracker_socket.sendto(error_message.encode(), peer_address)
            except json.JSONDecodeError:
                error_message = "400 Bad Request: Invalid JSON format in metadata."
                return self.tracker_socket.sendto(error_message.encode(), peer_address)
            
        self.register_peer(peer_address, peer_type, files, username) 
            
    def register_peer(self, peer_address: tuple, peer_type: str, files: dict, username: str = "unknown") -> None:
        """
        Registers a new peer with the tracker if the peer limit is not reached.
        
        :param peer_address: The address of the peer that sent the request.
        :param peer_type: The type of the peer, either 'seeder' or 'leecher'.
        :param files: A dictionary of files the peer has (if it's a seeder).
        """
        response_message = "500 Internal Server Error: Unexpected error occurred."
        
        with self.lock:
            # Ensure that we don't exceed the maximum peer limit and register the peer.
            if len(self.active_peers) < self.peer_limit:
                self.active_peers[peer_address] = {
                    'username': username,
                    'last_activity': time.time(), 
                    'type': peer_type,
                    'files': files if peer_type == "seeder" else []
                }
                # If the peer is a seeder, update the file_repository.
                if peer_type == 'seeder' and files:
                    for file_info in files:
                        filename = file_info.get("filename")
                        filesize = file_info.get("size")
                        checksum = file_info.get("checksum")
                        if filename:
                            if filename not in self.file_repository:
                                self.file_repository[filename] = []
                            self.file_repository[filename].append({
                                "peer_address": peer_address,
                                "size": filesize,
                                "checksum": checksum
                            })
                            response_message = f"201 Created: Client '{username}' with address {peer_address} successfully registered as a {peer_type} with files: {files}"
                else:
                    response_message = f"201 Created: Client '{username}' with address {peer_address} successfully registered as a {peer_type}"
            else:
                response_message = "403 Forbidden: Client limit reached, registration denied."
        print(f"{shell.BRIGHT_MAGENTA}{response_message}{shell.RESET}")
        self.tracker_socket.sendto(response_message.encode(), peer_address)
        
    def handle_get_peers_request(self, split_request: list, peer_address: tuple) -> None:
        """
        Handles get peers requests.
        
        :param split_request: The split request message sent by the peer.
        :param peer_address: The address of the peer that sent the request.
        """
        # Checking if the get peers request has a valid format.
        if len(split_request) < 2:
            error_message = "400 Bad Request: Usage: GET_PEERS <filename>"
            return self.tracker_socket.sendto(error_message.encode(), peer_address)
       
        filename = split_request[1]
        self.get_peers_for_file(filename, peer_address)    
        
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
                # Fix, do the mixture thing.
                response_message = {
                    'status': "200 OK",
                    'filename': filename,
                    'size': seeders[0]["size"], # double check.
                    'checksum': seeders[0]['checksum'],
                    'seeders': [seeder['peer_address'] for seeder in seeders]
                }
            else:
                # Fix for consistency.
                response_message  = f"404 Not Found: File not available: {filename}"
                      
        self.tracker_socket.sendto(json.dumps(response_message).encode(), peer_address)
                
    def list_active_peers(self, peer_address: tuple, username: str = "unknown") -> None:
        """
        Sends a list of currently active peers (seeders and leechers) to the requesting peer.
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Obtain the active seeders and leechers and list them out.
            try:
                active_seeders = [
                {'peer': peer, 'username': info.get('username', 'unknown')}
                for peer, info in self.active_peers.items() if info['type'] == 'seeder'
                ]
            
                active_leechers = [
                    {'peer': peer, 'username': info.get('username', 'unknown')}
                    for peer, info in self.active_peers.items() if info['type'] == 'leecher'
                ]
                
                active_list = {'seeders': active_seeders, 'leechers': active_leechers}
            
                # Convert dictionary into JSON format.
                response = json.dumps(active_list)       
            except Exception as e:
                print(f"{shell.BRIGHT_RED}500 Internal Server Error: Failed to retrieve active clients for Client '{username}' with address {peer_address}.{shell.RESET}")   
                         
        print(f"{shell.BRIGHT_MAGENTA}200 OK: Client '{username}' with address {peer_address} successfully obtained a list of active clients.{shell.RESET}")
        self.tracker_socket.sendto(response.encode(), peer_address)
        
    def list_available_files(self, peer_address: tuple) -> None:
        """
        Obtains a list of the files available in the tracker file repository dictionary along with their sizes.
        
        :param peer_address: The address of the peer that sent the request.
        """
        with self.lock:
            # Obtain a list of the files available in the tracker file repository.
            available_files = {
                filename: file_entries[0]["size"]
                for filename, file_entries in self.file_repository.items() if file_entries
            }
            
        # Convert dictionary to JSON string.
        json_response = json.dumps(available_files)
            
        self.tracker_socket.sendto(json_response.encode(), peer_address)
        
    def remove_peer(self, peer_address: tuple, username: str = "unknown") -> None:
        """
        Removes a peer from the active list when it disconnects.
        """
        with self.lock:
            if peer_address in self.active_peers:
                peer_info = self.active_peers[peer_address]

                # If the peer is a seeder, remove its files from the file repository.
                if peer_info['type'] == 'seeder':
                    for file_info in peer_info.get('files', []): 
                        filename = file_info['filename']
                        if filename in self.file_repository:
                            # Find and remove the specific peer's entry.
                            self.file_repository[filename] = [
                                entry for entry in self.file_repository[filename]
                                if entry['peer_address'] != peer_address
                            ]
                            # If no more seeders for the file, remove the file from the repository.
                            if not self.file_repository[filename]:
                                del self.file_repository[filename]

                # Remove peer from active peers
                del self.active_peers[peer_address]
                response_message = f"200 OK: Client '{username}' with address {peer_address} successfully disconnected from the tracker"
                print(f"{shell.BRIGHT_RED}{response_message}{shell.RESET}")
            else:
                response_message = f"403 Forbidden: Peer {peer_address} not found."
                print(f"{shell.BRIGHT_MAGENTA}{response_message}{shell.RESET}")

        self.tracker_socket.sendto(response_message.encode(), peer_address)
            
    def remove_inactive_peers(self) -> None:
        """
        Periodically removes inactive peers based on timeout.
        """
        while True:
            time.sleep(10)  # Remove inactive peers every 30 seconds.
            with self.lock:
                current_time = time.time()
                for peer in list(self.active_peers.keys()):
                    # Check if the peer has been inactive for longer than the timeout.
                    if current_time - self.active_peers[peer]['last_activity'] > self.peer_timeout:
                        # If the peer is a seeder, remove their files from the file_repository.
                        if self.active_peers[peer]['type'] == 'seeder':
                            for file_info in self.active_peers[peer]['files']: 
                                filename = file_info['filename'] 
                                if filename in self.file_repository:
                                    # Find and remove the specific peer's entry
                                    self.file_repository[filename] = [
                                        entry for entry in self.file_repository[filename]
                                        if entry['peer_address'] != peer
                                    ]
                                    # If no more seeders for the file, remove the file from the repository.
                                    if not self.file_repository[filename]:
                                        del self.file_repository[filename]
                                                
                        # Remove the inactive peer from active_peers.
                        del self.active_peers[peer]    
                            
                        # Log the cleanup action.
                        formatted_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        print(f"{shell.BRIGHT_MAGENTA}Clean-up performed at: {formatted_date}{shell.RESET}")
                        print(f"{shell.BRIGHT_RED}Removed inactive peer: {peer}{shell.RESET}")
               
    def keep_peer_alive(self, peer_address: tuple, username: str = "unknown"):
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
                response_message = f"200 OK: Successfully updated last activity time for client '{username}' with address {peer_address}."
            else:
                response_message = f"403 Forbidden: Peer not found in active list: {peer_address}"
                  
        print(response_message)      
        self.tracker_socket.sendto(response_message.encode(), peer_address)
        
    def handle_ping_request(self, peer_address: tuple) -> None:
        """
        Handles a PING request from a peer and responds with a PONG message.
        
        :param peer_address: The address of the peer sending the PING request.
        """
        response_message = "200 OK: PONG"
        self.tracker_socket.sendto(response_message.encode(), peer_address)
                                              
if __name__ == '__main__':
    try:  
        # Initialise the tracker.
        shell.clear_shell()
        tracker = Tracker('137.158.160.145', 17383) 
        
        # Clear the terminal shell and print the PyTorrent Logo.
        shell.print_logo()
            
        # Start the peer cleanup thread.
        cleanup_thread = Thread(target = tracker.remove_inactive_peers, daemon = True)
        cleanup_thread.start()
        
        # Start the tracker.
        tracker.start()
    except OSError as e:
        if e.errno == 98:
            print("😬 Oops! The tracker port is already in use. Please try a different port or stop the process using it. 🔄")