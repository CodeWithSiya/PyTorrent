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