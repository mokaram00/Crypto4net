# utils/__init__.py

# This file makes the utils directory a Python package

from .console_helpers import ( 
    clear_console, 
    print_status, 
    print_separator 
)
from .network import wait_for_internet
from .config_helpers import (
    get_active_config_path,
    load_config,
    get_word_count,
    get_address_count,
    get_mnemonic_settings,
    get_selected_networks,
    get_supported_networks,
    get_api_keys,
)
from .mnemonic_generator import ( 
    generate_mnemonic, 
    generate_seed, 
    derive_addresses, 
    print_derived_addresses 
)
from .api_requests import run_checks

UTILS_VERSION = "1.0.0"

def get_api_keys(provider, network=None):
    """Get API keys from config file.
    If network is specified, returns list of API keys for that network.
    Otherwise returns dict of all API keys."""
    config = load_config()
    
    if network:
        # Get all keys for specific network
        keys = []
        i = 1
        while True:
            key = config[provider].get(f"{network}_key{i}")
            if not key or key.startswith("YOUR_"):
                break
            keys.append(key)
            i += 1
        return keys if keys else [config[provider].get(f"{network}_key1")]
    else:
        # Get all keys for all networks
        keys = {}
        networks = config["DEFAULT"][f"{provider}_NETWORKS"].split(",")
        for network in networks:
            network_keys = []
            i = 1
            while True:
                key = config[provider].get(f"{network}_key{i}")
                if not key or key.startswith("YOUR_"):
                    break
                network_keys.append(key)
                i += 1
            keys[f"{network}_key"] = network_keys[0] if network_keys else config[provider].get(f"{network}_key1")
        return keys