import os
import subprocess
import configparser
from utils import get_supported_networks
from colorama import Fore, Style, init

# Initialize colorama
init()

def install_requirements():
    """Check if required packages are installed without attempting to install them."""
    try:
        # Just try to import the required packages
        import aiohttp
        import bip_utils
        import pycryptodome
        import pywin32
        return True
    except ImportError:
        print(f"{Fore.RED} Required packages are not installed. Please install them manually.{Style.RESET_ALL}")
        return False


def set_active_config(config_path):
    """Save the selected configuration file path as active."""
    active_config_file = os.path.join("config_setups", "active_setup.ini")
    with open(active_config_file, "w") as file:
        file.write(config_path)


def setup_config():
    """Setup configuration for API keys, token networks, mnemonic, and address count."""
    config_folder = "config_setups"
    os.makedirs(config_folder, exist_ok=True)

    existing_setups = [f for f in os.listdir(config_folder) if f.endswith(".ini") and f != "active_setup.ini"]

    print(f"\n{Fore.CYAN} Available setup options:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   0. {Fore.WHITE}Create a new setup{Style.RESET_ALL}")
    for i, setup in enumerate(existing_setups, 1):
        print(f"{Fore.YELLOW}   {i}. {Fore.WHITE}{setup}{Style.RESET_ALL}")

    while True:
        choice = input(f"{Fore.CYAN} Choose a setup to load or create a new one (enter the number): {Style.RESET_ALL}").strip()
        try:
            choice = int(choice)
            if choice == 0:
                print(f"{Fore.GREEN} Creating a new setup.{Style.RESET_ALL}")
                break
            elif 1 <= choice <= len(existing_setups):
                config_path = os.path.join(config_folder, existing_setups[choice - 1])
                set_active_config(config_path)  # Save selected config as active
                print(f"{Fore.GREEN} Loaded setup: {existing_setups[choice - 1]}{Style.RESET_ALL}")
                return config_path
            else:
                print(f"{Fore.RED} Invalid choice. Please try again.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED} Invalid input. Please enter a valid number.{Style.RESET_ALL}")

    config_path = os.path.join(config_folder, input(f"{Fore.CYAN} Enter a name for the new setup file (e.g., explorer_setup.ini): {Style.RESET_ALL}").strip())
    if not config_path.endswith(".ini"):
        config_path += ".ini"

    config = configparser.ConfigParser()
    config["DEFAULT"] = {"API_PROVIDERS": "ExplorerAPI"}

    # Setup Discord notifications
    while True:
        use_discord = input(f"\n{Fore.CYAN} Do you want to enable Discord notifications? (yes/no): {Style.RESET_ALL}").strip().lower()
        if use_discord in ['yes', 'no']:
            break
        print(f"{Fore.RED} Please enter 'yes' or 'no'{Style.RESET_ALL}")

    if use_discord == 'yes':
        config["Discord"] = {}
        while True:
            webhook_url = input(f"{Fore.CYAN} Enter your Discord webhook URL: {Style.RESET_ALL}").strip()
            if webhook_url.startswith('https://discord.com/api/webhooks/'):
                config["Discord"]["webhook_url"] = webhook_url
                break
            print(f"{Fore.RED} Invalid Discord webhook URL. It should start with 'https://discord.com/api/webhooks/'{Style.RESET_ALL}")
        
        while True:
            try:
                notification_interval = int(input(f"{Fore.CYAN} Enter notification interval (number of operations before sending update, e.g. 100): {Style.RESET_ALL}"))
                if notification_interval > 0:
                    config["Discord"]["notification_interval"] = str(notification_interval)
                    break
                print(f"{Fore.RED} Please enter a positive number{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED} Please enter a valid number{Style.RESET_ALL}")
    else:
        config["Discord"] = {"enabled": "false"}

    # Fetch supported networks using get_supported_networks()
    explorer_networks = list(get_supported_networks()['Bip44'].keys())

    print(f"\n{Fore.CYAN} Available networks for ExplorerAPI:{Style.RESET_ALL}")
    for i, network in enumerate(explorer_networks, 1):
        print(f"{Fore.YELLOW}   {i}. {Fore.WHITE}{network.capitalize()}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}   all. {Fore.WHITE}Select all networks for ExplorerAPI{Style.RESET_ALL}")

    chosen_networks = []
    while True:
        network_choices = input(f"{Fore.CYAN} Enter the numbers of the networks you want to use (comma-separated, or 'all'): {Style.RESET_ALL}").strip()
        if network_choices.lower() == "all":
            chosen_networks = explorer_networks
            break
        else:
            valid_selection = True
            for choice in network_choices.split(","):
                try:
                    selected_network = explorer_networks[int(choice) - 1]
                    if selected_network not in chosen_networks:
                        chosen_networks.append(selected_network)
                except (IndexError, ValueError):
                    print(f"{Fore.RED} Invalid selection: {choice}{Style.RESET_ALL}")
                    valid_selection = False

            if valid_selection and chosen_networks:
                break
            print(f"{Fore.RED} Invalid input. Please enter valid numbers or type 'all'.{Style.RESET_ALL}")

    config["DEFAULT"]["ExplorerAPI_NETWORKS"] = ",".join(chosen_networks)

    # Add multiple API keys for each chosen network
    config["ExplorerAPI"] = {}
    for network in chosen_networks:
        print(f"\n{Fore.CYAN} Setup API keys for {network.upper()}:{Style.RESET_ALL}")
        while True:
            try:
                num_keys = int(input(f"{Fore.YELLOW}   How many API keys do you want to add for {network}? (1-5): {Style.RESET_ALL}"))
                if 1 <= num_keys <= 5:
                    break
                print(f"{Fore.RED} Please enter a number between 1 and 5.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED} Please enter a valid number.{Style.RESET_ALL}")

        for i in range(1, num_keys + 1):
            while True:
                key = input(f"{Fore.CYAN}   Enter API key #{i} for {network}: {Style.RESET_ALL}").strip()
                if key:
                    config["ExplorerAPI"][f"{network}_key{i}"] = key
                    break
                else:
                    print(f"{Fore.RED} API key #{i} for {network} is required. Please provide a valid key.{Style.RESET_ALL}")

    # Setup for mnemonic word count
    while True:
        try:
            word_count = int(input(f"\n{Fore.CYAN} Enter the number of words for the mnemonic (12, 15, 18, 21, 24): {Style.RESET_ALL}"))
            if word_count not in [12, 15, 18, 21, 24]:
                raise ValueError("Word count must be one of 12, 15, 18, 21, 24.")
            break
        except ValueError as e:
            print(f"{Fore.RED} Invalid input: {e}{Style.RESET_ALL}")
    config["DEFAULT"]["MNEMONIC_WORD_COUNT"] = str(word_count)

    # Setup for number of addresses
    while True:
        try:
            num_addresses = int(input(f"{Fore.CYAN} Enter the number of addresses to generate (minimum 1): {Style.RESET_ALL}"))
            if num_addresses < 1:
                raise ValueError("Number of addresses must be at least 1.")
            break
        except ValueError as e:
            print(f"{Fore.RED} Invalid input: {e}{Style.RESET_ALL}")
    config["DEFAULT"]["ADDRESS_COUNT"] = str(num_addresses)

    # Save configuration
    with open(config_path, "w") as config_file:
        config.write(config_file)

    set_active_config(config_path)  # Save new config as active
    print(f"\n{Fore.GREEN} Configuration setup is complete.{Style.RESET_ALL}")
    return config_path


def validate_config(config_path):
    """Validate the configuration and add placeholders for missing or invalid values."""
    if not os.path.exists(config_path):
        print(f"{Fore.RED} Configuration file not found. Please run the setup first.{Style.RESET_ALL}")
        return False

    config = configparser.ConfigParser()
    config.read(config_path)

    config_updated = False
    all_valid = True

    # Validate Discord settings
    if "Discord" in config:
        if config["Discord"].get("enabled", "").lower() == "false":
            pass  # Discord is explicitly disabled
        else:
            webhook_url = config["Discord"].get("webhook_url", "").strip()
            if not webhook_url.startswith("https://discord.com/api/webhooks/"):
                print(f"{Fore.RED} Invalid Discord webhook URL{Style.RESET_ALL}")
                all_valid = False
            
            try:
                notification_interval = int(config["Discord"].get("notification_interval", "0"))
                if notification_interval <= 0:
                    raise ValueError
            except ValueError:
                print(f"{Fore.YELLOW} Invalid Discord notification interval. Setting default to 100.{Style.RESET_ALL}")
                config["Discord"]["notification_interval"] = "100"
                config_updated = True
    else:
        # Add default Discord section if missing
        config["Discord"] = {"enabled": "false"}
        config_updated = True

    # Validate mnemonic word count
    word_count = config["DEFAULT"].get("MNEMONIC_WORD_COUNT", "").strip()
    if word_count not in ["12", "15", "18", "21", "24"]:
        print(f"{Fore.YELLOW} Invalid or missing mnemonic word count. Setting default to 12.{Style.RESET_ALL}")
        config["DEFAULT"]["MNEMONIC_WORD_COUNT"] = "12"
        config_updated = True
        all_valid = False

    # Validate address count
    try:
        address_count = int(config["DEFAULT"].get("ADDRESS_COUNT", "0").strip())
        if address_count < 1:
            raise ValueError
    except ValueError:
        print(f"{Fore.YELLOW} Invalid or missing address count. Setting default to 1.{Style.RESET_ALL}")
        config["DEFAULT"]["ADDRESS_COUNT"] = "1"
        config_updated = True
        all_valid = False

    # Validate API keys and networks
    networks = config["DEFAULT"].get("ExplorerAPI_NETWORKS", "").split(",")
    missing_networks = []
    
    for network in networks:
        # Check for at least one valid API key per network
        has_valid_key = False
        for i in range(1, 6):  # Check up to 5 possible keys
            key_name = f"{network}_key{i}"
            key_value = config["ExplorerAPI"].get(key_name, "").strip()
            if key_value and not key_value.startswith("<") and not key_value.startswith("YOUR_"):
                has_valid_key = True
                break
        
        if not has_valid_key:
            missing_networks.append(network)
        
        # Remove old-style single key if present
        old_key = f"{network}_key"
        if old_key in config["ExplorerAPI"]:
            del config["ExplorerAPI"][old_key]
            config_updated = True

    if missing_networks:
        print(f"{Fore.RED} No valid API keys found for networks: {', '.join(missing_networks)}{Style.RESET_ALL}")
        all_valid = False

    # Save updated configuration if any changes were made
    if config_updated:
        with open(config_path, "w") as config_file:
            config.write(config_file)
        print(f"{Fore.YELLOW} Configuration file updated.{Style.RESET_ALL}")

    if all_valid:
        print(f"{Fore.GREEN} Configuration is valid.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED} Configuration is incomplete. Please add valid API keys for all networks.{Style.RESET_ALL}")

    return all_valid