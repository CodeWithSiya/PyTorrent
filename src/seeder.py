# seeder receives message from leecher
import socket 
import threading


class Seeder:
        
    def __init__(self, peer_id, ip_address, port, file_path):
        
        """
        :param peer_id: Identifier for the peer
        :param ip_address: IP address for the seeder
        :param port: The port number the seeder is listening on
        :param file_path: The path for the file the seeder is hosting
        """
        
        self.peer_id = peer_id
        self.ip_address = ip_address
        self.port = port
        self.file_path = file_path
        
        self.addr = (self.ip_address, self.port)
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind(self.addr)
        
    def get_addr(self):
        return self.addr
    

    def get_ip_address(self):
        return self.ip_address
    
        
        
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
         #listen for new connections
        self.tcp_socket.listen(1)
        
        
        while True: #Wait for msg
            
            #create new socket for sending messages
            conn, addr = self.tcp_socket.accept()
            
            #start a thread to send a file
            thread = threading.Thread(target=self.send_file, args=(self.file_path, conn))
            thread.start()

            print(f"Connected by {addr} | Total leechers: {threading.active_count() - 1}")

    
    def send_file(self, filename, conn):
        """
        Send a file to the leecher (temporary)
        """
        wait = True
        while wait: #wait for signal to start sending
            
            #get signal to start sending
            msg = conn.recv(4096).decode()
            
            if msg == "DOWNLOAD":
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

    
        
