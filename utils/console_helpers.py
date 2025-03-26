import os
import time
from colorama import Fore, Style, init

# Initialize colorama
init()

def clear_console():
    """Clears the console output for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_status(message, value=None):
    """Print a status message with optional value."""
    if value is not None:
        if "Total Script Runtime" in message:
            print(f"{Fore.CYAN}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
        elif "Checked" in message:
            print(f"{Fore.YELLOW}{message}: {Fore.GREEN}{value}{Style.RESET_ALL}")
        elif "Previous Check" in message:
            print(f"{Fore.MAGENTA}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
        elif "API Check Time" in message:
            print(f"{Fore.CYAN}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
        elif "Balance Found" in message:
            print(f"{Fore.GREEN}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
        elif "No balance found" in message:
            print(f"{Fore.RED}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
        elif "Total Balances Found" in message:
            print(f"{Fore.YELLOW}{message}: {Fore.GREEN}{value}{Style.RESET_ALL}")
        else:
            print(f"{Fore.WHITE}{message}: {Fore.YELLOW}{value}{Style.RESET_ALL}")
    else:
        print(f"{Fore.WHITE}{message}{Style.RESET_ALL}")


def print_separator():
    """Print a decorative separator line."""
    print(f"{Fore.BLUE}╔══════════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.BLUE}║{Fore.CYAN}                                                                              {Fore.BLUE}║{Style.RESET_ALL}")
    print(f"{Fore.BLUE}╚══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
