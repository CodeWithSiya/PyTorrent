from getch import getch, pause
import random
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
        
def print_at_left(text: str) -> None:
    """
    Aligns the given text string on the right of the terminal.
    
    :param text: The string text to be printed on the right of the terminal.
    """
    type_writer_effect(f"{BOLD}{text}{RESET}")
    
def print_at_right(text: str) -> None:
    """
    Aligns the given text string on the left of the terminal.
    
    :param text: The string text to be printed on the left of the terminal.
    """
    # Calculate the width of the terminal window.
    terminal_width = shutil.get_terminal_size().columns
    
    # Calculate the padding for right alignment.
    padding = terminal_width - len(text)
    
    # Print the text with the padding if not too long.
    if padding > 0:
        print(' ' * padding, end = "")
        type_writer_effect(f"{BOLD}{GREEN}{text}{RESET}")
    else:
        type_writer_effect(f"{BOLD}{GREEN}{GREEN}{RESET}")
          
def get_random_emoji() -> str:
    """
    Gets a random emoji from a list of predefined emojis.
    
    :return: The random
    """
    # List of emojis to choose from
    emojis = ['😀', '😎', '🔥', '🌟', '🛸', '🚀', '⚡', '👽', '👾', '👻', '🛹', '🤖', '🎸', 
              '🎮', '🕹️', '💻', '📡', '🔮', '🧠', '🎧', '🥷', '🦾', '🛸', '🌌']
    
    # Randomly select an emoji from the list
    random_emoji = random.choice(emojis)
    
    # Return the selected emoji
    return random_emoji
                
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
    
def print_menu() -> None:
    """
    Prints the PyTorrent menu for user interaction.
    """
    # Calculate the width of the terminal window
    terminal_width = shutil.get_terminal_size().columns
    
    # Print the menu with the provided options.
    menu_options = f"{BOLD}1. View Connected Peers 👥\n2. View your Shared Files 📂\n3. Download a File ⬇️\n4. Change Your Username ✏️\n5. Disconnect from PyTorrent 🚪{RESET}"
    type_writer_effect(f"\n{BOLD}Please select an option from the menu below:\n{menu_options}", 0.03)
    type_writer_effect(f"\n{BOLD}{BRIGHT_YELLOW}Type 'help' at any time to see a list of available commands or 'clear' to reset the interface :){RESET}", 0.03)
    print(f"{BRIGHT_BLUE}{'_' * terminal_width}{RESET}")
    
def reset_shell() -> None:
    """
    Clears and resets the shell to a 'blank' state.
    """
    clear_shell()
    print_logo()
    print_menu()
    
def print_line() -> None:
    """
    Prints the blue line used in the PyTorrent interface.
    """
    # Calculate the width of the terminal window and print the line.
    terminal_width = shutil.get_terminal_size().columns
    print(f"{BRIGHT_BLUE}{'_' * terminal_width}{RESET}")
    
def type_writer_effect(text:str, delay: int = 0.05, newline: bool = True) -> None:   
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
    # Only print a newline if nessesary.
    if newline:
        print()
        
def hit_any_key_to_continue() -> None:
    """
    Waits for the user to press any key before continuing.
    """
    type_writer_effect(f"\n{BRIGHT_YELLOW}HIT ANY KEY TO CONTINUE...🙂‍{RESET}")
    pause("")
    
def hit_any_key_to_exit() -> None:
    """
    Waits for the user to press any key before continuing.
    """
    type_writer_effect(f"\n{BRIGHT_YELLOW}HIT ANY KEY TO EXIT PYTORRENT...🙂‍{RESET}")
    pause("")