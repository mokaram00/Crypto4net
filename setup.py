import subprocess
import sys
import os
from colorama import Fore, Style, init

# Initialize colorama
init()

def print_banner():
    """Print stylized banner with developer info."""
    banner = f"""
    {Fore.MAGENTA}╔═══════════════════════════════════════════════════════════════╗
    ║     {Fore.CYAN}  ____           _                          {Fore.MAGENTA}              ║
    ║     {Fore.CYAN} |  _ \  __ _ __| | ___ __   ___  ___ ___  {Fore.MAGENTA}              ║
    ║     {Fore.CYAN} | | | |/ _` / _` |/ | '_ \ / _ \/ __/ __| {Fore.MAGENTA}              ║
    ║     {Fore.CYAN} | |_| | (_| | (_| | || | | |  __/\__ \__ \ {Fore.MAGENTA}             ║
    ║     {Fore.CYAN} |____/ \__,_|\__,_|_||_| |_|\___||___/___/ {Fore.MAGENTA}             ║
    ║                                                               ║
    ║     {Fore.YELLOW}Developer:{Fore.RED} Mokaram {Fore.YELLOW}| Discord:{Fore.CYAN} .69h.{Fore.MAGENTA}                ║
    ║     {Fore.YELLOW}Join our Discord:{Fore.CYAN} discord.gg/ezcpCsxYc8{Fore.MAGENTA}              ║
    ╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def install_requirements():
    """Install all required packages."""
    print(f"{Fore.CYAN} Installing required packages...{Style.RESET_ALL}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print(f"{Fore.GREEN} All packages installed successfully!{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW} You can now run the program using the command:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}python main.py{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED} Error installing packages: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    print_banner()
    if not os.path.exists("requirements.txt"):
        print(f"{Fore.RED} requirements.txt file not found!{Style.RESET_ALL}")
        sys.exit(1)
        
    install_requirements()