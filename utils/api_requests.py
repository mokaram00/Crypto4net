import aiohttp
import asyncio
import os
from datetime import datetime
from utils import get_api_keys
import time
from collections import deque
from urllib.parse import urlencode
from colorama import Fore, Style, init

# Initialize colorama
init()

# Rate limiter class for better API request management
class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()
            
            # If we've hit the limit, wait
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.time_window - now
                if wait_time > 0:
                    return wait_time
            
            # Add new request
            self.requests.append(now)
            return 0

class MultiKeyRateLimiter:
    def __init__(self, api_keys, max_requests_per_key=5, time_window=1.0):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.limiters = {key: RateLimiter(max_requests_per_key, time_window) for key in api_keys}
        self.lock = asyncio.Lock()
        self.last_used = {key: 0 for key in api_keys}  # Track last usage time for each key
    
    async def get_next_available_key(self):
        async with self.lock:
            now = time.time()
            best_key = None
            min_wait_time = float('inf')
            
            # Try all keys to find the one with minimum wait time
            for i in range(len(self.api_keys)):
                key = self.api_keys[(self.current_key_index + i) % len(self.api_keys)]
                wait_time = await self.limiters[key].acquire()
                
                # Consider both rate limit wait time and time since last use
                total_wait = wait_time + max(0, 1.0 - (now - self.last_used[key]))
                
                if total_wait < min_wait_time:
                    min_wait_time = total_wait
                    best_key = key
            
            if min_wait_time > 0:
                await asyncio.sleep(min_wait_time)
            
            self.last_used[best_key] = now
            self.current_key_index = (self.api_keys.index(best_key) + 1) % len(self.api_keys)
            return best_key

# Network-specific rate limiters
NETWORK_RATE_LIMITERS = {}

# Define network-specific rate limits
RATE_LIMITS = {
    "tron": {
        "max_requests_per_key": 5,  # Updated to match Tron's official limit
        "time_window": 1.0
    },
    "default": {
        "max_requests_per_key": 5,
        "time_window": 1.0
    }
}

async def fetch_balance(session, url, headers, network, api_keys):
    """Perform an asynchronous GET request to fetch balance with improved rate limiting."""
    # Get or create rate limiter for network
    if network not in NETWORK_RATE_LIMITERS:
        # Get network-specific rate limits
        rate_limit = RATE_LIMITS.get(network, RATE_LIMITS["default"])
        NETWORK_RATE_LIMITERS[network] = MultiKeyRateLimiter(
            api_keys,
            max_requests_per_key=rate_limit["max_requests_per_key"],
            time_window=rate_limit["time_window"]
        )
    
    # Get next available key
    api_key = await NETWORK_RATE_LIMITERS[network].get_next_available_key()
    
    # Update URL or headers with the selected key
    if network == "tron":
        headers["TRON-PRO-API-KEY"] = api_key
    else:
        url = url.split("apikey=")[0] + "apikey=" + api_key
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 429:  # Rate limit hit
                print(f"{Fore.YELLOW} Rate limit hit for {network} with key {api_key[:6]}...{Style.RESET_ALL}")
                return {"error": "rate_limit"}
            return await response.json()
    except Exception as e:
        return {"error": str(e)}

async def check_balance(session, network, address, rate_limiter):
    """Check balance for a single address on a specific network."""
    
    # Get the next available API key from the rate limiter
    api_key = await rate_limiter.get_next_available_key()
    
    # API endpoints and parameters for each network
    api_endpoints = {
        "bsc": {
            "url": "https://api.bscscan.com/api",
            "params": {
                "module": "account",
                "action": "balance",
                "address": address,
                "apikey": api_key
            }
        },
        "ethereum": {
            "url": "https://api.etherscan.io/api",
            "params": {
                "module": "account",
                "action": "balance",
                "address": address,
                "apikey": api_key
            }
        },
        "polygon": {
            "url": "https://api.polygonscan.com/api",
            "params": {
                "module": "account",
                "action": "balance",
                "address": address,
                "apikey": api_key
            }
        },
        "tron": {
            "url": "https://api.trongrid.io/v1/accounts",
            "params": {
                "address": address
            },
            "headers": {
                "TRON-PRO-API-KEY": api_key
            }
        }
    }

    if network not in api_endpoints:
        print(f"{Fore.RED} Unsupported network: {network}{Style.RESET_ALL}")
        return None

    endpoint = api_endpoints[network]
    
    try:
        # Configure timeout
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=30)
        
        # Add headers for Tron network
        headers = endpoint.get("headers", {})
        
        async with session.get(
            endpoint["url"],
            params=endpoint["params"],
            headers=headers,
            timeout=timeout,
            ssl=False
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                # Handle different API response formats
                if network == "tron":
                    if data and len(data["data"]) > 0 and data["data"][0]["balance"] > 0:
                        return {
                            "network": network,
                            "address": address,
                            "balance": data["data"][0]["balance"]
                        }
                else:
                    if data["status"] == "1" and int(data["result"]) > 0:
                        return {
                            "network": network,
                            "address": address,
                            "balance": data["result"]
                        }
            return None
            
    except asyncio.TimeoutError:
        print(f"{Fore.RED} API error for {network}: Connection timeout{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED} API error for {network}: {str(e)}{Style.RESET_ALL}")
        return None


def process_balance_response(network, address, response):
    """Process the API response to extract balance."""
    if network == "tron":
        # Tron-specific response handling
        if "data" in response and response["data"]:
            data = response["data"][0]  # Get first account data
            balance = float(data.get("balance", 0)) / 1_000_000  # Convert from SUN to TRX
            if balance > 0:
                print(f"{Fore.GREEN} Balance found for {address} on Tron: {balance} TRX{Style.RESET_ALL}")
                return {"network": "tron", "address": address, "balance": balance}
        return None  # No balance found for Tron
    else:
        # EVM (Ethereum, BSC, Polygon) response handling
        balance_wei = int(response.get("result", 0))
        if balance_wei > 0:
            balance = balance_wei / 1e18  # Convert Wei to Ether
            print(f"{Fore.GREEN} Balance found for {address} on {network.capitalize()}: {balance}{Style.RESET_ALL}")
            return {"network": network, "address": address, "balance": balance}
        return None  # No balance found


async def test_balance_fetching():
    """Test balance fetching functionality with known addresses."""
    print(f"\n{Fore.CYAN} Starting balance fetching test...{Style.RESET_ALL}")
    
    # Test addresses with known balances
    test_addresses = {
        "bsc": [
            "0x8894e0a0c962cb723c1976a4421c95949be2d4e3",  # Binance Hot Wallet
            "0xca503a7ed99eca485da2e875aedf7758472c378c"   # PancakeSwap: Syrup Pool
        ],
        "ethereum": [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Binance Hot Wallet
            "0xDA9dfA130Df4dE4673b89022EE50ff26f6EA73Cf"   # Wintermute
        ],
        "polygon": [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Binance Hot Wallet
            "0x7b8133f51717e8a652ec13d87cdc0b02c493c705"   # Polygon Foundation
        ],
        "tron": [
            "TMuA6YqfCeX8EhbfYEg5y7S4DqzSJireY9",  # Binance Hot Wallet
            "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"   # TRON Foundation
        ]
    }

    # Configure session for maximum performance
    connector = aiohttp.TCPConnector(
        limit=100,
        force_close=False,
        enable_cleanup_closed=True,
        ssl=False
    )
    timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=30)
    
    # Initialize rate limiters for test
    rate_limiters = {}
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:
        tasks = []
        for network, addresses in test_addresses.items():
            network_keys = get_api_keys("ExplorerAPI", network)
            if not network_keys:
                print(f"{Fore.RED} No API keys available for {network}{Style.RESET_ALL}")
                continue
            
            # Create rate limiter for this network using the unified rate limits
            rate_limit = RATE_LIMITS.get(network, RATE_LIMITS["default"])
            rate_limiters[network] = MultiKeyRateLimiter(
                network_keys,
                max_requests_per_key=rate_limit["max_requests_per_key"],
                time_window=rate_limit["time_window"]
            )
            
            print(f"{Fore.CYAN} {network.upper()}: Using {len(network_keys)} API keys with {rate_limit['max_requests_per_key']} requests/second per key{Style.RESET_ALL}")
            
            for address in addresses:
                tasks.append(check_balance(session, network, address, rate_limiters[network]))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"{Fore.RED} Test error: {str(result)}{Style.RESET_ALL}")
                elif result:
                    print(f"{Fore.GREEN} Test balance found: {result}{Style.RESET_ALL}")
        
        return True


async def run_checks(derived_addresses, mnemonic, discord_notifier=None):
    """Run balance checks for all derived addresses asynchronously."""
    if mnemonic == "TEST_MODE":
        await test_balance_fetching()
        return True
        
    all_results = []
    checked_count = 0
    batch_count = 0  # Counter for batch notifications
    network_progress = {}
    total_addresses = 0

    # Configure session for maximum performance
    connector = aiohttp.TCPConnector(
        limit=100,
        force_close=False,
        enable_cleanup_closed=True,
        ssl=False
    )
    timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=30)
    
    # Calculate total addresses
    for network, addresses in derived_addresses.get("Bip44", {}).items():
        total_addresses += len(addresses)
    
    # Set mnemonic for notifications if Discord is enabled
    if discord_notifier:
        discord_notifier.mnemonic = mnemonic  # Set mnemonic for notifications
    
    # Initialize rate limiters for each network
    rate_limiters = {}
    for network in derived_addresses.get("Bip44", {}).keys():
        network_keys = get_api_keys("ExplorerAPI", network)
        if network_keys:
            rate_limit = RATE_LIMITS.get(network, RATE_LIMITS["default"])
            rate_limiters[network] = MultiKeyRateLimiter(
                network_keys,
                max_requests_per_key=rate_limit["max_requests_per_key"],
                time_window=rate_limit["time_window"]
            )
            print(f"{Fore.CYAN} {network.upper()}: Rate limit set to {rate_limit['max_requests_per_key']} requests per {rate_limit['time_window']}s per key{Style.RESET_ALL}")
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:
        print(f"\n{Fore.CYAN} Starting balance checks...{Style.RESET_ALL}")
        
        # Initialize progress tracking and create tasks for all networks simultaneously
        network_tasks = {}
        
        for network, addresses in derived_addresses.get("Bip44", {}).items():
            if network not in rate_limiters:
                print(f"{Fore.RED} No valid API keys found for {network.upper()}{Style.RESET_ALL}")
                continue

            network_progress[network] = {
                "total": len(addresses),
                "checked": 0,
                "with_balance": 0
            }
            
            print(f"{Fore.CYAN} {network.upper()}: {len(addresses)} addresses using {len(rate_limiters[network].api_keys)} API keys{Style.RESET_ALL}")
            
            # Create tasks for this network
            network_tasks[network] = []
            for addr in addresses:
                task = check_balance(session, network, addr, rate_limiters[network])
                network_tasks[network].append(task)

        if not network_tasks:
            return False

        print(f"\n{Fore.CYAN} Processing {total_addresses} total addresses across all networks simultaneously...\n{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Progress by network:{Style.RESET_ALL}")
        for network, progress in network_progress.items():
            print(f"  {network.upper()}: 0/{progress['total']} (0%)")
        print(f"\n{Fore.CYAN}Starting parallel checks...\n{Style.RESET_ALL}")

        # Process all networks in parallel with rate limiting
        async def process_network(network, tasks):
            chunk_size = len(rate_limiters[network].api_keys) * 2  # Optimize chunk size based on available API keys
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i:i + chunk_size]
                
                # Process chunk with rate limiting
                responses = await asyncio.gather(*chunk, return_exceptions=True)
                
                for response in responses:
                    nonlocal checked_count
                    checked_count += 1
                    network_progress[network]["checked"] += 1
                    
                    if isinstance(response, Exception):
                        print(f"{Fore.RED} Error checking address on {network}: {str(response)}{Style.RESET_ALL}")
                        continue
                        
                    if response is not None:
                        all_results.append(response)
                        network_progress[network]["with_balance"] += 1
                        print(f"{Fore.GREEN} Found balance: {response['address']} on {network.upper()}: {response['balance']}{Style.RESET_ALL}")
                        
                        # Send immediate notification for found wallet if Discord is enabled
                        if discord_notifier:
                            await discord_notifier.notify_wallet_found(response)
                    
                    # Update progress every 10 addresses without Discord notification
                    if checked_count % 10 == 0:
                        print(f"\n{Fore.CYAN} Current Progress:{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Overall: {checked_count}/{total_addresses} ({(checked_count/total_addresses*100):.1f}%){Style.RESET_ALL}")
                        print(f"\n{Fore.CYAN}By Network:{Style.RESET_ALL}")
                        for net, prog in network_progress.items():
                            checked_pct = (prog["checked"] / prog["total"]) * 100
                            print(f"  {net.upper()}: {prog['checked']}/{prog['total']} ({checked_pct:.1f}%) - Found {prog['with_balance']} with balance")
                        print("\n")

        # Create and run tasks for all networks in parallel
        network_processors = [
            process_network(network, tasks)
            for network, tasks in network_tasks.items()
        ]
        
        # Wait for all networks to complete
        await asyncio.gather(*network_processors)

        print(f"\n{Fore.CYAN} Final Results:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Total addresses checked: {checked_count}/{total_addresses}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}By Network:{Style.RESET_ALL}")
        for network, progress in network_progress.items():
            checked_pct = (progress["checked"] / progress["total"]) * 100
            print(f"  {network.upper()}: {progress['checked']}/{progress['total']} ({checked_pct:.1f}%)")
            print(f"    Found {progress['with_balance']} addresses with balance")
        
        print(f"\n{Fore.YELLOW}Total addresses with balance: {len(all_results)}{Style.RESET_ALL}")
        
        if all_results:
            save_balances(all_results, mnemonic)
            return True
        return False


def save_balances(balances, mnemonic):
    """Save mnemonic and balance details to a file if balance is found."""
    if not os.path.exists("found_wallets"):
        os.makedirs("found_wallets")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"found_wallets/balance_found_{timestamp}.txt"

    with open(filename, "w") as file:
        file.write(f"Mnemonic Phrase: {mnemonic}\n\n")
        file.write("Found Balances:\n")
        for balance_info in balances:
            file.write(f"Network: {balance_info['network'].capitalize()}, Address: {balance_info['address']}, "
                       f"Balance: {balance_info['balance']}\n")

    print(f"{Fore.GREEN} Balance information saved to {filename}{Style.RESET_ALL}")