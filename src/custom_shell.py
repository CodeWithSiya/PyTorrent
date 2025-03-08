import shutil
import time
import sys
import os

"""
A utility program that enhances the PyTorrent client with a visually appealing and user-friendly terminal interface.
    
:author: Siyabonga Madondo, Ethan Ngwetjana, Lindokuhle Mdlalose
:version: 17/03/2025
"""

# Stores the PyTorrent logo used throughout the interface.
PYTORRENT_LOGO = """
   ___      _____                          _   
  / _ \_   /__   \___  _ __ _ __ ___ _ __ | |_ 
 / /_)/ | | |/ /\/ _ \| '__| '__/ _ \ '_ \| __|
/ ___/| |_| / / | (_) | |  | | |  __/ | | | |_ 
\/     \__, \/   \___/|_|  |_|  \___|_| |_|\__|
       |___/                                   
"""

# Constants which define the different colours and aspects used in the UI.
BOLD = "\033[1m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_WHITE = "\033[97m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_RED="\033[91m"
BRIGHT_CYAN= "\033[96m"
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
GREY = "\033[90m"
WHITE="\033[37m"   
RESET = "\033[0m"

def clear_shell() -> None:
    """
    Clears the terminal screen to provide a clean interface for the PyTorrent client.
    """
    # Check if the user is using a Windows or Linux/macOS machine and clear the terminal.
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
        
def print_at_centre(text: str) -> None:
    """
    Aligns the given text string at the centre of the terminal.
    
    :param text: The string text to be centred.
    """
    # Calculate the width of the terminal window.
    terminal_width = shutil.get_terminal_size().columns
    
    # Split the text into lines and center each line individually.
    for line in text.splitlines():
        centered_line = line.center(terminal_width)
        print(centered_line)
               
def print_logo() -> None:
    """
    Prints the PyTorrent logo and disclaimer.
    """
    # Change the colour of the logo to blue and print it.
    print_at_centre(f"{BOLD}{BRIGHT_BLUE}{PYTORRENT_LOGO}{RESET}")
    print_at_centre(f"{BOLD}{' ' * 20}{WHITE}Disclaimer: All files hosted on PyTorrent are 100% legal... or so we're told.{BRIGHT_BLUE}👀{RESET}")
    
    # Print a centered blue line
    terminal_width = shutil.get_terminal_size().columns
    print_at_centre(f"{BRIGHT_BLUE}{'_' * terminal_width}{RESET}")
    
def print_menu():
    """
    Prints the PyTorrent menu for user interaction.
    """
    terminal_width = shutil.get_terminal_size().columns
    menu_options = f"{BOLD}1. 👥 View Connected Peers\n2. 📂 View Available Files\n3. ⬇️  Download a File\n4. 🚪 Disconnect from PyTorrent{RESET}"
    print(f"{BOLD}Choose an option from the menu:\n{menu_options}")
    print(f"{BRIGHT_BLUE}{'_' * terminal_width}")
    
def type_writer_effect(text:str, delay: int = 0.10):
    """
    Prints text to the terminal with a typewriter effect by printing one character at a time.
    
    :param text: The text to display.
    :param delay: The delay between each character (in seconds).
    """
    # Print one character at a time with a short delay between characters, and flush stout after each character.
    for char in text:
        sys.stdout.write(char) 
        sys.stdout.flush()  
        time.sleep(delay)  
    print()