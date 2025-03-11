import custom_shell as shell
from threading import *
from socket import *
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
    
    def __init__(self, host: str, udp_port: int, tcp_port: int, state: str = "leecher", tracker_timeout: int = 10):
        """
        Initialises the Client with the given host, UDP port, TCP port, state and tracker timeout.
        
        :param host: The host address of the seeder.
        :param udp_port: The UDP port on which the tracker listens for incoming connections.
        :param tcp_port: The TCP port on which the leecher listens for incoming file requests.
        "param state: The status of the client, either a 'seeder' or 'leecher' with default state being a leecher.
        :param tracker_timeout: Time (in seconds) to wait before considering the tracker as unreachable.
        :param file_path: Path to the file to be shared.
        """
        # Configuring the client's details.
        self.host = host
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.state = state
        self.tracker_timeout = tracker_timeout
        
        # Dictionary to store downloaded file chunks and a Lock for thread safety.
        self.file_chunks = {}
        self.lock = Lock()
        
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
        global username
        
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
            
            # Register this client as a leecher with the client.
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
                # Handle for leecher.
                request_message = f"REGISTER seeder {username} {files}"
                
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
                    return f"{shell.BRIGHT_GREEN}{response_message[response_message.find(':') + 2:]}!{shell.RESET}"
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
                    emoji = shell.get_random_emoji() 
                    print(f"- IP Address: {ip}")
                    print(f"- Port: {port}")
                    print(f"- Username: {leecher['username']}")
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
            #print(f"Tracker response for request from {peer_address}: {response_message.decode()}")
        except Exception as e:
            print(f"Error notifying the tracker that this peer is alive: {e}")
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
            
def main() -> None:
    """
    Main method which runs the PyTorrent client interface.
    """
    # Defining global variables to class-wide access.
    global client
    global username
        
    try:    
        # Instanciate the client instance, then register with the tracker though the welcoming sequence.
        client = Client(gethostbyname(gethostname()), 17380, 0)
        
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
                    else:
                        print("Invalid choice, please try again.")
                except ValueError:
                    print("Please enter a valid number or 'help'.")
            else:
                shell.print_menu()
            shell.print_line()
     
    except Exception as e:
        print(e)
    
if __name__ == '__main__':    
    # Print the initial window.
    main()