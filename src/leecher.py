# leecher send message to seeder (testing)
import socket
import select


class Leecher:
    
    def __init__(self, peer_id, seeders):
        
        """
        :param peer_id: Identifier for the peer
        :param seeders: A list of tuples that contain the IP address and port number of the seeders that the
        leecher will connect to
        """
        
        self.peer_id = peer_id
        
        self.seeders = seeders
        self.sockets = []
        
        
    
    def register_with_tracker():
        """
        Establish a connection with the tracker
        """   
        pass
    
    
    def connect_with_seeders(self):
        """
        Establish a TCP connection with multiple seeders using .select()
        """
        
        #Connect to list of seeders in non-blocking mode
        for seeder in self.seeders:
            seederSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            try:
                #Attempt to establish a connection with a seeder
                seederSocket.connect(seeder)
                print(f"Connected to seeder at {seeder}")
                self.sockets.append(seederSocket)

            except ConnectionRefusedError:
                print(f"Failed to connect with seeder at {seeder}")
                
        if not self.sockets:
            print("No available seeders.")
            return
                
                
        
        
    def download_chunk():
        """
        Download chunk from a seeder
        """
        pass
    
        
        
    def download_file(self):
        """
        Download download file from seeder (temporary)
        """
        
        while self.sockets:
            # Wait for sockets to become writable
            _, writable, _ = select.select([], self.sockets, [])
            
            for seederSocket in writable:
                try:
                    #Try to establich connection
                    
                    seederSocket.getpeername()
                    print(f"Connection established with {seederSocket.getpeername()}")
                    
                    #indicate to seeder that leecher is ready to download file
                    seederSocket.send("DOWNLOAD".encode())
                except OSError as e:
                    print(f"Connection failed: {e}")
                    
                    #Remove socket from socket list and close connection
                    self.sockets.remove(seederSocket)
                    seederSocket.close()
                    continue
            
            
            
            #Wait for filename from seeder:
            readable, _, _ = select.select(self.sockets, [], [])
            
            for seederSocket in readable:
                try:
                    filename_length = int.from_bytes(seederSocket.recv(4), byteorder='big')
                    
                    filename = seederSocket.recv(filename_length).decode()
            
                    file = open(filename, "wb")
                    
                    try:
                        while True:
                            data = seederSocket.recv(4096) #recieve in chunks
                            if not data:
                                break
                            #write recieved chunks in file
                            file.write(data)
                            
                        #add exception later
                            
                    finally:
                        print(f"File recieved successfully and saved as '{filename}'")
                        file.close()
                        
                    #After getting file close the connection
                    self.sockets.remove(seederSocket)
                    seederSocket.close()
                except ConnectionResetError:
                    print(f"Seeder {seederSocket.getpeername()} forcefully disconnected")
                    self.sockets.remove(seederSocket)
                    seederSocket.close()
            
        
        
    def resassemble_file():
        """
        Reassemble file from the downloaded chunks
        """
        pass
        
    def become_seeder():
        """
        Become a seeder after downloading a file
        """
        pass
        
        









