from threading import *
from socket import *
import time 

class Client:
   """
    Pytorrent Client Implementation.

    The client can function as either a leecher or a seeder based on its state.
    - As a leecher, it downloads file chunks from seeders and shares them with other leechers.
    - As a seeder, it hosts file chunks and serves them to leechers.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """