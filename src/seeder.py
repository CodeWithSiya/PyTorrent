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
               
    # def split_into_chuncks():
    #     """
    #     Host a file and divide it into chuncks
    #     """
    #     pass
    
    # def register_with_tracker():
    #     """
    #     Establish a connection with the tracker
    #     """
    #     pass
    
    # def connect_with_leecher(self):
    #     """
    #     Establish a TCP connection with a leecher
    #     """
    #     self.tcp_socket.bind(self.addr)
        
    #      #listen for new connections
    #     self.tcp_socket.listen(1)
    #     print(f"[LISTENING] Server is listening on {self.ip_address}")
              
    #     while True: #Wait for msg
            
    #         #create new socket for sending messages
    #         conn, addr = self.tcp_socket.accept()
            
    #         #start a thread to send a file
    #         thread = threading.Thread(target=send_file, args=(self.file_path, conn))
    #         thread.start()

    #         print(f"Connected by {addr} | Total leechers: {threading.active_count() - 1}")
 
    # def send_file(filename, conn):
    #     """
    #     Send a file to the leecher (temporary)
    #     """
    #     wait = True
    #     while wait: #wait for signal to start sending
            
    #         #get signal to start sending
    #         msg = conn.recv(4096).decode()
            
    #         if msg == DOWNLOAD_MESSAGE:
    #             wait = False
                
    #     #send the filename of file being sent
    #     conn.send(filename.encode())
                 
    #     #open file in byte mode
    #     file = open(filename, "rb")
              
    #     try:
    #         while True:
    #             # read in chunks
    #             chunk = file.read(4096)
    #             if not chunk:
    #                 break
    #             #send chunks
    #             conn.send(chunk)
    #     finally:
    #         print("File sent successfully.")
    #         file.close()
            
    #         #after file is sent close connection
    #         conn.close()
        
    # def send_chuncks():
    #     """
    #     Serve file chuncks to the leecher
    #     """
    #     pass