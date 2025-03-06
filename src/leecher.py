from threading import *
from socket import *

class Leecher:
    """
    Pytorrent Leecher Implementation.

    The leecher can connect to multiple seeders via a TCP connection and is responsible for:
    1. Registering with the tracker via UDP.
    2. Querying the tracker with its availability.
    2. Hosting a TCP server to send file chunks to leechers.
    3. Notifying the tracker of its availablity.

    :author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
    :version: 17/03/2025
    """    