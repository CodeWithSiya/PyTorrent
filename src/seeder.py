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
    def __init__(self, host:  peer_id, ip_address, port, file_path):
        
        
        self.peer_id = peer_id
        self.ip_address = ip_address
        self.port = port
        self.file_path = file_path
        
        self.addr = (self.ip_address, self.port)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               
    def split_into_chuncks():
        """
        Host a file and divide it into chuncks
        """
        pass
    
    def register_with_tracker():
        """
        Establish a connection with the tracker
        """
        pass
    
    def connect_with_leecher(self):
        """
        Establish a TCP connection with a leecher
        """
        self.tcp_socket.bind(self.addr)
        
         #listen for new connections
        self.tcp_socket.listen(1)
        print(f"[LISTENING] Server is listening on {self.ip_address}")
              
        while True: #Wait for msg
            
            #create new socket for sending messages
            conn, addr = self.tcp_socket.accept()
            
            #start a thread to send a file
            thread = threading.Thread(target=send_file, args=(self.file_path, conn))
            thread.start()

            print(f"Connected by {addr} | Total leechers: {threading.active_count() - 1}")
 
    def send_file(filename, conn):
        """
        Send a file to the leecher (temporary)
        """
        wait = True
        while wait: #wait for signal to start sending
            
            #get signal to start sending
            msg = conn.recv(4096).decode()
            
            if msg == DOWNLOAD_MESSAGE:
                wait = False
                
        #send the filename of file being sent
        conn.send(filename.encode())
                 
        #open file in byte mode
        file = open(filename, "rb")
              
        try:
            while True:
                # read in chunks
                chunk = file.read(4096)
                if not chunk:
                    break
                #send chunks
                conn.send(chunk)
        finally:
            print("File sent successfully.")
            file.close()
            
            #after file is sent close connection
            conn.close()
        
    def send_chuncks():
        """
        Serve file chuncks to the leecher
        """
        pass