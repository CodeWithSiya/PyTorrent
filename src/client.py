import sys
import custom_shell as shell
from threading import *
from socket import *
import hashlib
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
    # Defining a few class-wide variables for access throughout class.
    client = None
    username = "unknown"
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, state: str = "leecher", tracker_timeout: int = 10, file_dir: str = "user/shared_files"):
        """
        Initialises the Client with the given host, UDP port, TCP port, state and tracker timeout.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        "param state: The status of the client, either a 'seeder' or 'leecher' with default state being a leecher.
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
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        
        # if os.path.exists(self.metadata_file) and os.path.getsize(self.metadata_file) > 0:
        self.scan_directory_for_files()
        
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
          
    # TODO: SCAN BEFORE REGISTERING
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
        
    def get_chunk(self, filename: str, chunk_id: int, chunk_size: int = 1024 * 1024) -> bytes:
        """
        Retrieves a specific chunk of a file from disk.
        
        :param filename: Name of the file.
        :param chunk_id: ID of the chunk to retrieve.
        :param chunk_size: Size of each chunk in bytes (default: 1 MB).
        
        :return: The chunk data as bytes, or None if the chunk is not found or an error occurs.
        """
        # Check if the file exists in the file_chunks dictionary.
        if filename not in self.file_chunks:
            print(f"File '{filename} not found in shared files.")
            return None
        
        # Get the full file path.
        file_path = os.path.join(self.file_dir, filename) 
        try:
            with open(file_path, "rb") as file:
                file.seek(chunk_id * chunk_size)  # Move to the start of the chunk.
                return file.read(chunk_size)  # Read and return the chunk data.
        except Exception as e:
            print(f"Error reading chunk {chunk_id} from file '{filename}': {e}")
            return None
        
    def handle_tcp_connection(self, peer_socket: socket):
        """
        Handles incoming TCP connections from peers requesting file chunks or metadata.
        """
        
    def download_file(self, filename:str, seeder_address: tuple, output_dir: str = "user/downloads") -> None:
        """
        Downloads a file from a seeder by requesting chunks one by one.
        """     
        
    def request_chunk(self, filename: str, chunk_id: int, seeder_address: tuple) -> bytes:
        """
        Requests a specific chunk from a seeder.
        """
      
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
            client.register_with_tracker()
            
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
                shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}You have shared files. Registering as a seeder!{shell.RESET}")
            else:
                self.state = "leecher"
                shell.type_writer_effect(f"{shell.BRIGHT_MAGENTA}You have no shared files. Registering as a leecher!{shell.RESET}")
         
            # Register this client with the tracker.
            shell.type_writer_effect(f"\nPlease wait while we set up things for you...")
            client.register_with_tracker()
            
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
        # try:
        # Check the state of the client and create an appropriate request message.
        if self.state == "leecher":
            request_message = f"REGISTER leecher {username}"
            
                        
        else:
            # If the client is a seeder, include the list of shared files.
            file_data = {
                "files": [
                    {
                        "filename": filename, 
                        "size": metadata["size"]
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
            response_message = response_message.decode()
            
            # Extract the status code (first three characters) from the response.
            status_code = response_message[:3]
            
            # Handle the respone based on the status code.
            if status_code == "201":
                if self.state == "leecher":
                    shell.type_writer_effect(f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2:]}!{shell.RESET}")
                else:
                    shell.type_writer_effect(f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2 : response_message.find('seeder') + 6]}!{shell.RESET}")
            elif status_code == "400":
                shell.type_writer_effect(f"Error: {response_message[4:]}")
                shell.type_writer_effect(f"{shell.BOLD}{shell.BRIGHT_MAGENTA}Exiting...{shell.RESET}")
                sys.exit(1)
            elif status_code == "403":
                shell.type_writer_effect(f"Registration Denied: {response_message[4:]}")
                shell.type_writer_effect(f"{shell.BOLD}{shell.BRIGHT_MAGENTA}Exiting...{shell.RESET}")
                sys.exit(1)
            else:
                shell.type_writer_effect(f"Unexpected response: {response_message}")
                shell.type_writer_effect(f"{shell.BOLD}{shell.BRIGHT_MAGENTA}Exiting...{shell.RESET}")
                sys.exit(1)
                
                
        except Exception as e:
            # Tracker does not respond within the timeout time.
            shell.type_writer_effect(f"{shell.BRIGHT_RED}Tracker seems to be offline. Please try again later! 😱{shell.RESET}")
            shell.type_writer_effect(f"{shell.BOLD}{shell.BRIGHT_MAGENTA}Exiting...{shell.RESET}")
            sys.exit(1)
        
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
            active_users = json.loads(response_message.decode())
            shell.type_writer_effect(f"{shell.BRIGHT_GREEN}The list of active peers has been successfully retrieved!{shell.RESET}", 0.04)
    
            # Print information about the a leechers in a readable way.
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
                # Print information about our seeders.
                for seeder in active_users["seeders"]:
                    ip, port = seeder['peer']
                    emoji = shell.get_random_emoji() 
                    print(f"- IP Address: {ip}")
                    print(f"- Port: {port}")
                    print(f"- Username: {seeder['username']}")
                    print(f"- Status: {emoji} Active Seeder")
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
            available_files = json.loads(response_message.decode())

            shell.type_writer_effect(f"{shell.BRIGHT_GREEN}The list of available files has been successfully retrieved!{shell.RESET}", 0.04)

            # Print information about available files in a readable way.
            if not available_files:
                print("📂 Available Files:\n- No files currently available. 😞")
            else:
                print("📂 Available Files:")
                for filename, size in available_files.items():
                    emoji = shell.get_random_emoji()
                    print(f"- Filename: {filename}")
                    print(f"- Size: {size / (1024 * 1024):.2f} MB")
                    print(f"- Status: {emoji} Available")
        
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
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error querying the tracker for available peers: {e}")
    
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
            shell.clear_shell()
            shell.print_logo()
            
            shell.type_writer_effect(f"{shell.BOLD}{shell.RED}FATAL ERROR: Cannot notify the tracker that this peer is alive: {e} {shell.RESET}")
            shell.type_writer_effect(f"{shell.BOLD}{shell.RED}Tracker Disconnected!! Please try again later 😭{shell.RESET}")
            shell.type_writer_effect(f"{shell.BLUE}Exiting...{shell.RESET}")
            os._exit(1)
            
            
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
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
            
    def change_username(self):
        """
        Changes the username of the client. Also allows them to reset their data
        """
        
        shell.type_writer_effect(f"{shell.WHITE}Changing your Username...{shell.RESET}", 0.04)
        print("")
        shell.type_writer_effect(f"{shell.BLUE}Leave your new Username empty if you would like to delete your data 🗑️{shell.RESET}", 0.04)
        print("")
        
        shell.type_writer_effect(f"{shell.WHITE}Enter your new username:{shell.RESET}", 0.04)
        
        new_username = input().strip()
        
        
        try:
            
            if new_username:
                
                self.udp_socket.settimeout(self.tracker_timeout)
                
                request_message = f"CHANGE_USERNAME {username} {new_username} {(self.host, self.udp_port)}"
                
                self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
                
                response_message, peer_address = self.udp_socket.recvfrom(1024)
                
                if (response_message.decode() == "USERNAME_CHANGED"):
                    with open("config/config.txt", "w") as file:
                
                        file.write(f"username={new_username}")
                    
                    shell.type_writer_effect(f"{shell.GREEN}Username for {peer_address} successfully changed to '{new_username}' 😀{shell.RESET}", 0.04)
                    shell.type_writer_effect(f"{shell.WHITE}Returning to main menu...{shell.RESET}", 0.04)
                    
                else:
                    shell.type_writer_effect(f"{shell.RED}Unable to confirm if username changed on tracker. Aborting...{shell.RESET}", 0.04)
                    shell.type_writer_effect(f"{shell.WHITE}Returning to main menu...{shell.RESET}", 0.04)
            else:
                shell.type_writer_effect(f"{shell.RED}You are about reset your data!!! This cannot be undone!!! Are you sure? (Y/N){shell.RESET}", 0.04)
                
                final_prompt = input("")
                if final_prompt.lower() == "y":
                    
                    with open("config.txt", "w") as file: 
                        file.write(f"username=")
                    shell.type_writer_effect(f"{shell.GREEN}Username has been successfully reset (I don't know who you are now 💀){shell.RESET}", 0.04)
                    shell.type_writer_effect(f"{shell.WHITE}Returning to main menu...{shell.RESET}", 0.04)
                elif final_prompt.lower() == "n":
                    shell.type_writer_effect(f"{shell.WHITE}That was close 💀{shell.RESET}", 0.04)
                    shell.type_writer_effect(f"{shell.WHITE}Returning to main menu...{shell.RESET}", 0.04)
                else:
                    shell.type_writer_effect(f"{shell.WHITE}Incorrect input❌{shell.RESET}", 0.04)
                    shell.type_writer_effect(f"{shell.WHITE}Returning to main menu...{shell.RESET}", 0.04)
                        
        except Exception as e:
            print(f"Error while trying to change username: {e}")
            
def main() -> None:
    """
    Main method which runs the PyTorrent client interface.
    """
    # Defining global variables to class-wide access.
    global client
    global username
        
    try:    
        # Instantiate the client instance, then register with the tracker though the welcoming sequence.
        client = Client(gethostbyname(gethostname()), 17385, 0)
        
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
            
            # Process the users request -> Add a clear command.
            if choice.lower() != 'help':
                try:
                    choice = int(choice)
                    if choice == 1:
                        client.get_active_peer_list()
                    elif choice == 2:
                        client.get_available_files()
                    elif choice == 5:
                        client.change_username()
                    else:
                        shell.type_writer_effect(f"{shell.BOLD}{shell.RED}Please input a valid choice number or 'help'.{shell.RESET}", 0.04)
                except ValueError:
                    shell.type_writer_effect(f"{shell.BOLD}{shell.RED}Please input a valid choice number or 'help'.{shell.RESET}", 0.04)
            else:
                shell.print_menu()
            shell.print_line()
     
    except Exception as e:
        print(e)
    
if __name__ == '__main__':    
    # Print the initial window.
    main()