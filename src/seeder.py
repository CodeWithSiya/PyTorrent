# seeder receives message from leecher
import socket 
import select


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
        self.serverSocket = None
        self.sockets_list = []

        
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
    
    
    
    def connect_with_leechers(self):
        """
        Establish a TCP connection with leechers
        """
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.setblocking(False)
        self.serverSocket.bind(self.addr)
        
         #listen for new connections
        self.serverSocket.listen(5)
        
        
        while True: #Wait for msg
            
            # Wait for sockets to becomme readable
            readable, _, exceptional = select.select(self.sockets_list, [], self.sockets_list)
            
            for sock in readable:
                
                if sock == self.serverSocket:
                
                    #create new socket for sending messages
                    conn, addr = self.serverSocket.accept()
                    
                    print(f"Connected to {addr}")
                    
                    conn.setblocking(False)
                    
                    self.sockets_list.append(conn)
                    
                else:
                    self.send_file(self.file_path, conn)
                    
            
    def close_leecher_connection(self):
        """
        Close connection with leecher
        """
    

    
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
                
        print(f"Sending file {filename}...")
                
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
            self.sockets_list.remove(conn)
            conn.close()
        
        
    
    def send_chuncks():
        """
        Serve file chuncks to the leecher
        """
        pass

    
        
