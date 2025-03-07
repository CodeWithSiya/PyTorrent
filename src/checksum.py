import hashlib

"""
Pytorrent checksum implementation using SHA-256 encryption to verify the integrity of peer messages.

:author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
:version: 17/03/2025
""" 

def compute_checksum(message: str) -> str:
    """
    Computes a SHA-256 checksum for a given message.
    
    :param message: The input string message.
    :return: The hexadecimal checksum (256-bits).
    """
    return hashlib.sha256(message.encode()).hexidigest()