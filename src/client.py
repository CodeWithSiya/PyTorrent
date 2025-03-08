import custom_shell as shell
from threading import *
from socket import *
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
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, state: str = "leecher", tracker_timeout: int = 30):
        """
        Initialises the Client with the given host, UDP port, TCP port, state and tracker timeout.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        "param state: The status of the client, either a 'seeder' or 'leecher' with default state being a leecher.
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
        
        # Initialise the TCP socket for leecher connections.
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        
        # # Start the TCP server in a seperate thread.
        # self.tcp_server_thread = Thread(target=self.start_tcp_server, daemon=True)
        # self.tcp_server_thread.start()
    
    def welcoming_sequence(self) -> 'Client':
        """
        Welcomes the user to the application and prompts for a username if it's their first time.
        Registers the client as a leecher during the welcoming sequence.
        
        :return: Client instance after welcoming and registration
        """
        # Defining global variables to class-wide access.
        global client
        
        # Specifying the path of the configuration file.
        config_dir = "config"
        config_file = os.path.join(config_dir, "config.txt")
        
        # Ensure the config directory exists
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
                
            # Register this client as a leecher with the client.
            #TODO: Set up a timer with the tracker here with a message saying it seems like the tracker is offline. Please try again later.
            shell.type_writer_effect(f"\nPlease wait while we set up things for you...")
            client.register_with_tracker()
            
            # Output confirmation messages.
            shell.type_writer_effect(f"\nWelcome, {username}! You're all set to start using Pytorrent 💯")
            shell.type_writer_effect("You can now search for files, download them, and share them with others.")
            shell.type_writer_effect("\nYou'll begin as a leecher, meaning you can download files but won't be sharing yet.")
            shell.type_writer_effect("Once you have files to contribute, you can become a seeder and help distribute them 😎")
            shell.type_writer_effect("\nWe hope you enjoy using PyTorrent just as much as we enjoyed making it :)\n")
            time.sleep(1.5)
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
            
            # Register this client as a leecher with the client.
            shell.type_writer_effect(f"\nPlease wait while we set up things for you...") 
            client.register_with_tracker()
            shell.type_writer_effect("You're all set to start using Pytorrent again 💯")
            shell.type_writer_effect("\nType 'help' at any time to see a list of available commands.\n")
            time.sleep(1.5)
                           
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
            
    def get_active_peer_list(self) -> None:
        """
        Queries the tracker for a list of active peers in the network.
        """
        try:
            # Send a request message to the tracker.
            request_message = "LIST_ACTIVE"
            self.udp_socket.sendto(request_message.encode(), (self.host, self.udp_port))
            
            # Receive a response message from the tracker
            response_message, peer_address = self.udp_socket.recvfrom(1024)
            print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error querying the tracker for active_peers: {e}")
            
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
    # Defining global variables to class-wide access.
    global client
    
    # Clear the terminal and print the PyTorrent logo.
    shell.clear_shell() 
    shell.print_logo()
    
    try:    
        # Register the user with the client as a leecher.
        client = Client(gethostbyname(gethostname()), 17380, 0)
        client.welcoming_sequence()
        
        # Print the initial window for the client.
        shell.clear_shell() 
        shell.print_logo()
        shell.print_menu()
        choice = int(input("Enter your choice:\n"))
        
        if (choice == 1):
            client.get_active_peer_list()
    except Exception as e:
        print(e)
    
if __name__ == '__main__':    
    # Print the initial window.
    main()