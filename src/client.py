from concurrent.futures import ThreadPoolExecutor
import custom_shell as shell
from threading import *
from socket import *
import selectors
import traceback
import hashlib
import select 
import queue
import json
import time
import os

class Client:
    """
    Pytorrent Client Implementation.

    The client can function as either a leecher or a seeder based on its state.
    - As a leecher, it downloads file chunks from seeders and shares them with other leechers.
    - As a seeder, it hosts file chunks and serves them to leechers.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """
    # GET METADATA FROM TRACKER
    
    # Defining a few class-wide variables for access throughout class.
    client = None
    username = "unknown"
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, state: str = "leecher", tracker_timeout: int = 10, file_dir: str = "user/shared_files"):
        """
        Initialises the Client with the given host, UDP port, TCP port, state and tracker timeout.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        :param state: The status of the client, either a 'seeder' or 'leecher' with default state being a leecher.
        :param tracker_timeout: Time (in seconds) to wait before considering the tracker as unreachable.
        :param file_path: Path to the directory containing files to be shared..
        """
        # Configuring the client's details.
        self.host = host
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.state = state
        self.tracker_timeout = tracker_timeout
        self.file_dir = file_dir
        self.metadata_file = os.path.join(file_dir, "shared_files.json")
        
        # Dictionary to store file metadata, a variable for the shared data path and a Lock for thread safety.
        self.file_chunks = {}
        self.lock = Lock()
        
        # Ensure that the shared directory exists and create it if it does not exists.
        os.makedirs(self.file_dir, exist_ok = True)
        
        # Load or initialise metadata.
        self.load_metadata()
        
        # Initialise the UDP socket for tracker communication.
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        
        # Initialise the TCP socket for leecher connections.
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind(("0.0.0.0", self.tcp_port))
        self.tcp_socket.listen(5)
        
        # Use a selector to manage multiple connections using multiplexing.
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.tcp_socket, selectors.EVENT_READ, self.accepted_connection)
        
        # Start a thread to handle incoming TCP connections.
        self.tcp_thread = Thread(target=self.handle_connections, daemon=True)
        self.tcp_thread.start()

        # Scan the shared directory for files and add it to the shared_file.json meta file.
        self.scan_directory_for_files()
        
    def handle_connections(self) -> None:
        """
        Handles incoming TCP connections using a selector.
        """
        while True:
            # Waits for new events (new connections & data available to read) on registered sockets.
            events = self.selector.select()
            for key, _ in events:
                # Gets and calls the callback function associated with the event.
                callback = key.data
                callback(key.fileobj)
                
    def handle_tcp_connection(self, peer_socket: socket):
        """
        Handles incoming TCP connections from peers requesting file chunks or metadata.
        
        :param peer_socket: Socket of the peer we receive a TCP message from.
        """
        try:
            # Receive the request from the peer.
            request = peer_socket.recv(1024).decode('utf-8')

            if request.startswith("REQUEST_CHUNK"):
                # Parse the request to get the filename and chunk ID.
                _, filename, chunk_id = request.split()
                chunk_id = int(chunk_id)
                
                # Retrieve the requested chunk.
                chunk_data = self.get_chunk(filename, chunk_id)
                
                if chunk_data:
                    # Send the chunk data to the peer.
                    peer_socket.sendall(chunk_data)
                else:
                    # Send an error message if the chunk is not found.
                    peer_socket.sendall(b"CHUNK_NOT_FOUND")
            elif request.startswith("REQUEST_METADATA"):
                # Parse the request to get the filename
                _, filename = request.split()
                
                # Check if the file exists in the file_chunks dictionary
                if filename in self.file_chunks:
                    # Send the file metadata
                    metadata = self.file_chunks[filename]
                    peer_socket.sendall(json.dumps(metadata).encode('utf-8'))
                else:
                    # Send an error message if the file is not found
                    peer_socket.sendall(b"FILE_NOT_FOUND")      
            else:
                print(f"Invalid request from: {request}")
        except Exception as e:
            print(f"Error handling TCP connection: {e}")
        finally:
            self.selector.unregister(peer_socket)
            peer_socket.close()
     
    def accepted_connection(self, server_socket: socket):
        """
        Accepts a new connection and registers it with the selector.
        """
        connection, address = server_socket.accept()
        print(f"Accepted connection from {address}")
        connection.setblocking(False)
        self.selector.register(connection, selectors.EVENT_READ, self.handle_tcp_connection)       
        
    def download_file(self, filename: str, seeder_address: tuple, output_dir: str = "user/downloads"):
        """
        Downloads a file from multiple seeders by requesting chunks in parallel using a ThreadPoolExecutor.
        """
        with self.lock:
            # Ensure the output directory exists.
            os.makedirs(output_dir, exist_ok = True)
            
            # Create the output file path and a .tmp file.
            output_file_path = os.path.join(output_dir, filename)
            temp_dir = os.path.join(output_dir, ".tmp")
            os.makedirs(temp_dir, exist_ok = True)
            
            # Check if download already exists.
            if os.path.exists(output_file_path):
                shell.type_writer_effect(f"File '{filename}' already exists in {output_dir}")
                choice = input("Do you want to download it again? (y/n): ").lower()
                if choice != 'y':
                    return
            
            # Query tracker for additional seeders for this file.
            response = self.query_tracker_for_peers(filename)
            if not response:
                print(f"Failed to get peer information for {filename}.")
                return
            
            # Get list of all available seeders.
            seeders = response.get("seeders", [])
            if not seeders:
                print(f"No seeders available for file '{filename}.")
                    
            # Retrieve the metadata of a specific file from the first seeder.
            seeder_metadata = self.request_file_metadata(filename, tuple(seeders[0])) if seeders else None
            if not seeder_metadata:
                print(f"Could not retrieve metadata for {filename}")
                return
            
            # Print some debugging information.
            total_chunks = len(seeder_metadata["chunks"])
            print(f"File has {total_chunks} chunk(s) to download")
            
            # Create a chunk queue for each chunk we need to download.
            chunk_queue = queue.Queue()
            for i in range(total_chunks):
                chunk_queue.put(i)
                
            # Intialise folder for downloaded chunks.
            downloaded_chunks = {}
            
            # Start parallel download.
            max_workers = min(len(seeders), os.cpu_count() * 2 or 4)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create a list of download tasks.
                futures = []
                for seeder in seeders:
                    future = executor.submit(
                        self.download_chunk_worker,
                        filename,
                        seeder,
                        chunk_queue,
                        temp_dir,
                        downloaded_chunks,
                        seeder_metadata
                    )
                    futures.append(future)
                    
                # Wait for all download tasks to complete.
                for future in futures:
                    future.result()
                
            # Verify download completion.
            if len(downloaded_chunks) != total_chunks:
                print(f"Download incomplete: {len(downloaded_chunks)}/{total_chunks} chunks downloaded")
                return
            
            # Reassemble the file on the leecher side.
            self.reassemble_file(filename, output_dir, temp_dir, downloaded_chunks)
        
    def download_chunk_worker(self, filename, seeder, chunk_queue, temp_dir, downloaded_chunks, seeder_metadata):
        """Helper method to download chunks from a seeder."""
        while not chunk_queue.empty():
            try:
                chunk_id = chunk_queue.get_nowait()
            except queue.Empty:
                return

            # Retrive the chunk size from the metadata from the seeder.
            print(f"Requesting chunk {chunk_id} from {seeder}")
            chunk_size = seeder_metadata["chunks"][chunk_id]["size"]
            chunk_data = self.request_chunk(filename, chunk_id, chunk_size, seeder)

            if chunk_data:
                chunk_path = os.path.join(temp_dir, f"{filename}.part{chunk_id}")
                with open(chunk_path, "wb") as chunk_file:
                    chunk_file.write(chunk_data)
 
                downloaded_chunks[chunk_id] = chunk_path
                print(f"Progress: {len(downloaded_chunks)}/{len(downloaded_chunks) + chunk_queue.qsize()} chunks downloaded")
            else:
                # Requeue failed chunk
                chunk_queue.put(chunk_id)

    def request_chunk(self, filename: str, chunk_id: int, chunk_size: int, seeder_address: tuple) -> bytes:
        """
        Requests a specific chunk from a seeder.
        """
        try:
            seeder_address = tuple(seeder_address)
            # Create a TCP socket and connect to the seeder.
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((seeder_address[0], 12000))
            sock.settimeout(10)
            
            # Send the request for the chunk.
            request_message = f"REQUEST_CHUNK {filename} {chunk_id}"
            sock.sendall(request_message.encode('utf-8'))
            
            # Receive the chunk data with a buffer.
            chunk_data = b""
            bytes_received = 0
            
            # Continue receiving until we have the exact number of bytes expected.
            while bytes_received < chunk_size:
                try:
                    data = sock.recv(min(64 * 1024, chunk_size - bytes_received))
                    
                    # Check if we received an error message on first data packet.
                    if bytes_received == 0 and data == b"CHUNK_NOT_FOUND":
                        print(f"Chunk {chunk_id} not found for file {filename}.")
                        return None
                    
                    # Check if connection closed prematurely.
                    if not data:  
                        print(f"Warning: Connection closed after receiving {bytes_received}/{chunk_size} bytes")
                        break
                    
                    chunk_data += data
                    bytes_received = len(chunk_data)
                    print(f"Received {bytes_received}/{chunk_size} bytes ({(bytes_received/chunk_size)*100:.1f}%)")     
                        
                except socket.timeout:
                    print(f"Timeout after receiving {bytes_received}/{chunk_size} bytes")
                    if bytes_received > 0:
                        # Return partial data if we got something
                        return chunk_data
                    return None      
               
            print(f"Successfully received chunk {chunk_id} ({bytes_received} bytes)")                   
            return chunk_data
        except Exception as e:
            print(f"Error requesting chunk {chunk_id} from {seeder_address}: {e}")
            return None
        finally:
            sock.close()
            
    def get_chunk(self, filename: str, chunk_id: int, chunk_size: int = 1024 * 1024) -> bytes:
        """
        Retrieves a specific chunk of a file from disk.
        
        :param filename: Name of the file.
        :param chunk_id: ID of the chunk to retrieve.
        
        :return: The chunk data as bytes, or None if the chunk is not found or an error occurs.
        """
        # Check if the file exists in the file_chunks dictionary.
        if filename not in self.file_chunks:
            print(f"File '{filename} not found in shared files.")
            return None
        
        # Get the full file path and chunk metadata
        file_path = os.path.join(self.file_dir, filename) 
        chunk_metadata = self.file_chunks[filename]["chunks"][chunk_id]
        chunk_size = chunk_metadata["size"]
        
        try:
            with open(file_path, "rb") as file:
                file.seek(chunk_id * chunk_size)  # Move to the start of the chunk.
                chunk_data = file.read(chunk_size)  # Read and return the chunk data.
                
                # Verify checksum for that chunk.
                if "checksum" in chunk_metadata:
                    actual_checksum = hashlib.sha256(chunk_data).hexdigest()
                    if actual_checksum != chunk_metadata["checksum"]:
                        print(f"Warning: Checksum mismatch for chunk {chunk_id} of file '{filename}'")
                        
                return chunk_data
                         
        except Exception as e:
            print(f"Error reading chunk {chunk_id} from file '{filename}': {e}")
            return None
        
    def request_file_metadata(self, filename: str, seeder_address: tuple) -> dict:
        """
        Requests metadata about a file from a seeder.
        
        :param filename: Name of the file
        :param seeder_address: Address of the seeder (host, port)
        :return: Dictionary containing file metadata or None if the request fails
        """
        try:
            # Create a TCP socket and connect to the seeder
            sock = socket(AF_INET, SOCK_STREAM)
            print(seeder_address[0])
            sock.connect((seeder_address[0], 12000))  # THIS LINE SAYS CONNECTION REFUSED!
            sock.settimeout(10)  # Set a timeout for the request
            
            # Send the request for the file metadata
            request_message = f"REQUEST_METADATA {filename}"
            sock.sendall(request_message.encode('utf-8'))
            
            # Receive the metadata
            metadata_data = sock.recv(1024 * 10)  # Increased buffer size for metadata
            print(metadata_data)
            
            if metadata_data == b"FILE_NOT_FOUND" or metadata_data == b"METADATA_NOT_AVAILABLE":
                print(f"Metadata not available for file {filename} from {seeder_address}")
                return None
            
            # Parse the metadata
            metadata = json.loads(metadata_data.decode('utf-8'))
            return metadata
        except Exception as e:
            error_message = traceback.format_exc()
            print(error_message)
            print(f"Error requesting metadata for {filename} from {seeder_address}: {e}")
            return None
        finally:
            sock.close()

    def reassemble_file(self, filename, output_dir, temp_dir, downloaded_chunks):
        """Merges all downloaded chunks into the final file and verifies integrity."""
        output_file_path = os.path.join(output_dir, filename)
        print("All chunks downloaded. Reassembling file...")

        # Merge the downloaded chunks as required.
        with open(output_file_path, "wb") as output_file:
            for i in sorted(downloaded_chunks.keys()):
                chunk_path = downloaded_chunks[i]
                with open(chunk_path, "rb") as chunk_file:
                    output_file.write(chunk_file.read())
                os.remove(chunk_path)
                
        # Verify the file integrity using checksums.

        os.rmdir(temp_dir)
        print(f"Download complete: {output_file_path}")
            
    def load_metadata(self) -> None:
        """
        Load metadata from the shared_files.json file.
        If the file doesn't exist, initialise an empty metadata dictionary.
        """
        # If the metadata file exists, open the file, read from it and load it into the file chunks dict.
        with self.lock:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r") as file:
                    self.file_chunks = json.load(file).get("files", {})
            else:
                self.file_chunks = {}
            
    def save_metadata(self):
        """
        Save metadata to the shared_files.json file.
        This ensures that changes to the shared files are stored.
        """
        with self.lock:
            # Write the changes to a temporary file before the actual file to race conditions,
            temp_file = self.metadata_file + ".tmp"
            with open(temp_file, "w") as file:
                json.dump({"files": self.file_chunks}, file, indent=4)
            os.replace(temp_file, self.metadata_file)
            
    def generate_file_metadata(self, file_path: str, chunk_size: int = 1024 * 1024):
        """
        Generates metadata for a file, including SHA-256 checksums and chunk information. 
        """
        # Initialise the metadata dictionary for later use.
        metadata = {
            "size": os.path.getsize(file_path),  # Total file size.
            "checksum": "",  # Checksum of the entire file.
            "chunks": []  # List of chunks with their metadata.
        }
 
        # Create a SHA-256 hash object, open the file in binary mode and read it in chunks.
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as file:
            chunk = file.read(chunk_size)
            while chunk:
                sha256.update(chunk)
                chunk = file.read(chunk_size)
        # Store the final checksum hash in the metadata.
        metadata["checksum"] = sha256.hexdigest()
        
        # Generate chunk metadata for the file.
        with open(file_path, "rb") as file:
            # Initialise the chunk ID and read the first chunk.
            chunk_id = 0
            chunk = file.read(chunk_size)
            
            # Loop through each chunk of the file.
            while chunk:
                # Add the current chunk's metadata.
                metadata["chunks"].append({
                    "id": chunk_id,
                    "size": len(chunk),
                    "checksum": hashlib.sha256(chunk).hexdigest()
                })
                # Move to the next chunk.
                chunk_id += 1
                chunk = file.read(chunk_size)
                
        return metadata

    # TODO: Add functionality for deleted files.
    def scan_directory_for_files(self) -> list:
        """
        Scans the shared directory for files and updates metadata.
        If a file is new or has been modified, its metadata is regenerated.
        """
        # Scanning through the specified directory for files to add into the metadata shared_files.json file.
        for filename in os.listdir(self.file_dir):
            file_path = os.path.join(self.file_dir, filename)
            # Ensure the current item is a file that's not the shared metadata itself.
            if os.path.isfile(file_path) and filename != "shared_files.json":
                # If the file is not already tracked in file_chunks, add it.
                if filename not in self.file_chunks:
                    print(f"Adding new file: {filename}")
                    self.file_chunks[filename] = self.generate_file_metadata(file_path)
                else:
                    # Check if the file has been modified or corrupted using checksums.
                    existing_checksum = self.file_chunks[filename]["checksum"]
                    new_checksum = self.generate_file_metadata(file_path)["checksum"]
                    # Check if the file has been modified, and generate new file metadata.
                    if existing_checksum != new_checksum:
                        print(f"Updating modified file: {filename}")
                        self.file_chunks[filename] = self.generate_file_metadata(file_path)           
        # Save updated metadata
        self.save_metadata()
      
    def welcoming_sequence(self) -> None:
        """
        Welcomes the user to the application and prompts for a username if it's their first time.
        - New users are always registered as leechers.
        - Returning users are registered as seeders if they have shared files, otherwise as leechers.
        
        :return: Client instance after welcoming and registration
        """
        # Defining global variables to class-wide access.
        global client
        global username
        
        # Specifying the path of the configuration file.
        config_dir = "config"
        config_file = os.path.join(config_dir, "config.txt")
        
        # Ensure the config directory exists.
        os.makedirs(config_dir, exist_ok=True)
        
        # Check if the user is a first-time user (No config file found).
        if not os.path.exists(config_file):
            # Print out the welcoming message using the type writer effect.
            shell.type_writer_effect(f"{shell.BOLD}Welcome to PyTorrent ⚡{shell.RESET}")
            shell.type_writer_effect(f"{shell.BOLD}This is a peer-to-peer file-sharing application where you can download and share files.{shell.RESET}")
            
            # Prompting the user for their username.
            shell.type_writer_effect(f"{shell.BOLD}Let's get started by setting up your username :)")
            shell.type_writer_effect("Please enter a username (Don't worry, you can change this later): ", newline = False)
            username = input().strip()
            while not username:
                print("Username cannot be empty. Please try again.")
                username = input("Please enter a username: ").strip()
                
            # Save the username to the config file.
            try:
                with open(config_file, "w") as file:
                    file.write(f"username={username}\n")
            except IOError as e:
                print(f"Error saving username to config file: {e}")
                
            # Register this client as a leecher with the tracker.
            shell.type_writer_effect(f"\nPlease wait while we set up things for you...")
            shell.type_writer_effect(f"{client.register_with_tracker()}")
            
            # Start the KEEP_ALIVE thread.
            self.keep_alive_thread = Thread(target=self.keep_alive, daemon = True)
            self.keep_alive_thread.start()
            
            # Output confirmation messages.
            shell.type_writer_effect(f"\nWelcome, {username}! You're all set to start using Pytorrent 💯")
            shell.type_writer_effect("You can now search for files, download them, and share them with others.")
            shell.type_writer_effect("\nYou'll begin as a leecher, meaning you can download files but won't be sharing yet.")
            shell.type_writer_effect("Once you have files to contribute, you can become a seeder and help distribute them 😎")
            shell.type_writer_effect("\nWe hope you enjoy using PyTorrent as much as we enjoyed making it :)")
            shell.hit_any_key_to_continue()
        else:
            # For returning users, find their username in the config file and welcome them back.
            username = ""
            with open(config_file, "r") as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith("username="):
                        username = line.split("=")[1].strip()
                        break
            
            # Ensure that "username=" is not missing from the config file.
            if username:
                shell.type_writer_effect(f"Welcome back, {username} ⚡")
            else:
                shell.type_writer_effect("Welcome back! (No username found in config file...🫤)")
                
            # If shared_files.json exists and has data, register as seeder else register as a leecher.
            if os.path.exists(self.metadata_file) and os.path.getsize(self.metadata_file) > 0:
                self.state = "seeder"
                shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}You have files available for sharing. Registering as a seeder!{shell.RESET}")
            else:
                self.state = "leecher"
                shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}You have no files available for sharing. Registering as a leecher!{shell.RESET}")
         
            # Register this client with the tracker.
            shell.type_writer_effect(f"\nPlease wait while we set up things for you...")
            shell.type_writer_effect(f"{client.register_with_tracker()}")
            
            # Start the KEEP_ALIVE thread.
            # Should only start if registration is successful!
            self.keep_alive_thread = Thread(target=self.keep_alive, daemon = True)
            self.keep_alive_thread.start()
            
            # Print confirmation messages.
            shell.type_writer_effect("\nYou're all set to start using Pytorrent again 💯")
            shell.type_writer_effect("\nType 'help' at any time to see a list of available commands.")
            shell.hit_any_key_to_continue()
                           
    def register_with_tracker(self, files: list = []) -> str:
        """
        Registers the client with the tracker as a leecher.
        
        :param files: The list of available files on this client.
        
        :return: Message retrieved from the tracker.
        """
        global username
        try:
            # Check the state of the client and create an appropriate request message.
            if self.state == "leecher":
                request_message = f"REGISTER leecher {username}"
            else:
                # If the client is a seeder, include the list of shared files.
                file_data = {
                    "files": [
                        {
                            "filename": filename, 
                            "size": metadata["size"],
                            "checksum": metadata["checksum"]
                        }
                        for filename, metadata in self.file_chunks.items()
                    ]
                }
                # Convert file_data to JSON and include it in the request message
                request_message = f"REGISTER seeder {username} {json.dumps(file_data)}"
                     
            # Send a request message to the tracker.
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            
            # Set a timeout for receiving the response from the tracker.
            self.udp_socket.settimeout(self.tracker_timeout)
            
            try:
                # Receive a response message from the tracker.
                response_message, peer_address = self.udp_socket.recvfrom(1024)
                response_message = response_message.decode('utf-8')
                
                # Extract the status code (first three characters) from the response.
                status_code = response_message[:3]
                
                # Handle the respone based on the status code.
                if status_code == "201":
                    if self.state == "leecher":
                        return f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2:]}!{shell.RESET}"
                    else:
                        return f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2 : response_message.find('seeder') + 6]}!{shell.RESET}"
                elif status_code == "400":
                    return f"Error: {response_message[4:]}"
                elif status_code == "403":
                    return f"Registration Denied: {response_message[4:]}"
                else:
                    return f"Unexpected response: {response_message}"
            except socket.timeout:
                # Tracker does not respond within the timeout time.
                return f"{shell.BRIGHT_RED}Tracker seems to be offline. Please try again later!{shell.RESET}"
        except Exception as e:
            print(f"Error registering with tracker: {e}")
    
    def disconnect_from_tracker(self) -> None:
        """
        Gracefully disconnects from the tracker.
        """  
        global username
        try:
            # Send a request message to the tracker.
            request_message = f"DISCONNECT {username}"
            
            # Aquire the lock for thread safety.
            self.lock.acquire()
            
            # Send the message to the tracker.
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            shell.type_writer_effect(f"{shell.WHITE}Disconnecting from the tracker ... Please hold on!{shell.RESET}", 0.04)
            
            # Retrieve and decode the response from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            response_message = response_message.decode()
            
            # Extract the status code (first three characters) from the response.
            status_code = response_message[:3]
                
            # Handle the respone based on the status code.
            if status_code == "200":
                shell.type_writer_effect(f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2:]}!{shell.RESET}")
            elif status_code == "400":
                return f"Error: {response_message[4:]}"
            else:
                return f"Unexpected response: {response_message}"
                    
        except Exception as e:
            print(f"Error disconnecting from the tracker: {e}")
            
        self.lock.release()
                        
    def get_active_peer_list(self) -> None:
        """
        Queries the tracker for a list of active peers in the network.
        """
        global username
        try:
            # Send a request message to the tracker.
            request_message = f"LIST_ACTIVE {username}"
            
            # Acquire the lock for thread safety.
            self.lock.acquire()
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            shell.type_writer_effect(f"{shell.WHITE}Fetching the list of active users for you... Please hold on!{shell.RESET}", 0.04)
            
            # Receive a response message from the tracker with active users and decode that message.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            active_users = json.loads(response_message.decode('utf-8'))
            shell.type_writer_effect(f"{shell.BRIGHT_GREEN}The list of active peers has been successfully retrieved!{shell.RESET}", 0.04)
    
            # Print information about the leechers in a readable way.
            if not active_users["leechers"]:
                print("⚡ Leechers:\n- No leechers currently active. 😞\n")
            else:
                print("⚡ Leechers:")
                for leecher in active_users["leechers"]:
                    ip, port = leecher['peer']
                    emoji = shell.get_random_emoji() 
                    print(f"- IP Address: {ip}")
                    print(f"- Port: {port}")
                    print(f"- Username: {leecher['username']}")
                    print(f"- Status: {emoji} Active Leecher\n")    
            if not active_users["seeders"]:
                print(f"🚀 Seeders:\n- No seeders currently active. 😞")
            else:
                print(f"🚀 Seeders:")
                # Print information about the seeders in a readable way.
                for seeder in active_users["seeders"]:
                    ip, port = seeder['peer']
                    emoji = shell.get_random_emoji() 
                    print(f"- IP Address: {ip}")
                    print(f"- Port: {port}")
                    print(f"- Username: {seeder['username']}")
                    print(f"- Status: {emoji} Active Seeder\n")
        except Exception as e:
            print(f"Error querying the tracker for active_peers: {e}")
            
        # Release the lock after execution.
        self.lock.release()
            
    def get_available_files(self) -> None:
        """
        Queries the tracker for files available in the network (At least one seeder has the file).
        """
        try:
            # Send a request message to the tracker.
            request_message = "LIST_FILES"
            
            # Acquire the lock for thread safety.
            self.lock.acquire()
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            shell.type_writer_effect(f"{shell.WHITE}Fetching the list of available files for you... Please hold on!{shell.RESET}", 0.04)
            
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(4096)  # Increase buffer size
            available_files = json.loads(response_message.decode('utf-8'))

            shell.type_writer_effect(f"{shell.BRIGHT_GREEN}The list of available files has been successfully retrieved!{shell.RESET}", 0.04)

            # Print information about available files in a readable way.
            if not available_files:
                print("📂 Available Files:\n- No files currently available. 😞")
            else:
                print("📂 Available Files:\n")
                for filename, size in available_files.items():
                    emoji = shell.get_random_emoji()
                    print(f"- Filename: {filename}")
                    print(f"- Size: {size / (1024 * 1024):.2f} MB")
                    print(f"- Status: {emoji} Available\n")
        
        except json.JSONDecodeError:
            print("Error: Received an invalid JSON response from the tracker.")
        except Exception as e:
            print(f"Error querying the tracker for available files: {e}")
        
        finally:
            # Release the lock after execution.
            self.lock.release()

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
            response = json.loads(response_message.decode('utf-8'))
            
            if response.get("status") == "200 OK":
                return response
            else:
                print(f"Error in querying for peers.")
                return None
        except Exception as e:
            print(f"Error querying the tracker for available peers: {e}")
            
    def handle_downloads(self) -> None:
        """
        Handles the file download process for the leecher.
        - Queries the tracker for available files.
        - Prompts the user to select a file to download.
        - Queries the tracker for seeders of the selected file.
        - Downloads the file from one of the seeders.
        """
        # try:
        shell.type_writer_effect(f"{shell.WHITE}Let's start the file downloading process ... {shell.get_random_emoji()}{shell.RESET}\n")
        
        # Querying the tracker for available files.
        self.get_available_files()
        shell.print_line()
        
        # Prompt the user to select a file to download.
        filename = input("Enter the name of the file you want to download:\n").strip()
        if not filename:
            print("Filename cannot be empty. Please try again.")
            
        # Query the tracker for seeders of the selected file.
        response = self.query_tracker_for_peers(filename)
        if not response:
            print(f"File '{filename}' not found or no seeders available.")
            return
        
        # Returning a list of seeders for the file.
        seeders = response.get("seeders", [])
        if not seeders:
            print(f"No seeders available for file '{filename}'.")
            return
        
        seeder_address = tuple(seeders[0])  # Select the first seeder
        shell.type_writer_effect(f"Downloading '{filename}' ...")
        
        # Step 5: Call the download_file method to start the download.
        self.download_file(filename, seeder_address)
        
        shell.type_writer_effect(f"{shell.BRIGHT_GREEN}Download of '{filename}' completed successfully.{shell.RESET}")
        # except Exception as e:
        #     print(f"Error handling downloads: {e}")
    
    def send_keep_alive(self) -> None:
        """
        Notifies the tracker that this peer is still active in the network.
        """
        global username
        self.lock.acquire()
        try:
            # Send a request message to the tracker.
            request_message = f"KEEP_ALIVE {username}"
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
        
            # Receive a response message from the tracker.
            response_message, peer_address = self.udp_socket.recvfrom(1024)
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
        finally:
            self.lock.release()
            
    def keep_alive(self) -> None:
        """
        Periodically sends a KEEP_ALIVE message to the tracker.
        This method periodically notifies the tracker that this peer is alive.
        """
        while True:
            # Send the KEEP_ALIVE message to the tracker every 5 seconds.
            self.send_keep_alive()
            time.sleep(2)
    
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
            print(f"Tracker response for request from {peer_address}: {response_message.decode('utf-8')}")
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
            
def main() -> None:
    """
    Main method which runs the PyTorrent client interface.
    """
    # Defining global variables to class-wide access.
    global client
    global username
        
    try:    
        # Instantiate the client instance, then register with the tracker though the welcoming sequence.
        client = Client(gethostbyname(gethostname()), 17383, 12001)
        
        shell.clear_shell() 
        shell.print_logo()
        client.welcoming_sequence()
         
        # Print the initial window for the client.
        shell.clear_shell() 
        shell.print_logo()
        shell.type_writer_effect(f"Hi, {username}!{shell.get_random_emoji()}", 0.05)
        shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}You are currently a {client.state.title()}!{shell.get_random_emoji()}{shell.RESET}", 0.05)
        shell.print_menu()
        
        while True:
            # Obtain the users input for their selected option.
            choice = input("Please input the number of your selected option:\n")
            
            # Process the users request.
            if choice.lower() != 'help' and choice.lower() != 'clear':
                try:
                    choice = int(choice)
                    if choice == 1:
                        client.get_active_peer_list()
                        shell.print_line()
                    elif choice == 2:
                        client.get_available_files()
                        shell.print_line()
                    elif choice == 3:
                        client.handle_downloads()
                        shell.print_line()
                    elif choice == 5:
                        client.disconnect_from_tracker()
                        break
                    else:
                        print("Invalid choice, please try again.")
                        shell.print_line()
                except ValueError:
                    print("Please enter a valid number, 'help' or 'clear'.")
                    shell.print_line()
            elif choice.lower() == 'help':
                shell.print_line()
                if username:
                    shell.type_writer_effect(f"Welcome back, {username} ⚡")
                else:
                    shell.type_writer_effect("Welcome back! (No username found in config file...🫤)")
                shell.print_menu()
            else:
                shell.reset_shell()
                
        shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}Thank you for using PyTorrent! We hope to see you again soon :) {shell.RESET}", 0.05)
        shell.hit_any_key_to_exit()
        shell.clear_shell()
    except Exception as e:
        traceback.print_exc()
        print(e)
    
if __name__ == '__main__':    
    # Print the initial window.
    main()