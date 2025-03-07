import aiohttp
import asyncio
import os
from datetime import datetime
from utils import get_api_keys
import time


async def fetch_balance(session, url, headers):
    """Perform an asynchronous GET request to fetch balance."""
    async with session.get(url, headers=headers) as response:
        return await response.json()


async def check_balance(session, network, address, api_key):
    """Check balance for a given network and address."""
    api_urls = {
        "bsc": f"https://api.bscscan.com/api?module=account&action=balance&address={address}&apikey={api_key}",
        "ethereum": f"https://api.etherscan.io/api?module=account&action=balance&address={address}&apikey={api_key}",
        "polygon": f"https://api.polygonscan.com/api?module=account&action=balance&address={address}&apikey={api_key}",
        "tron": f"https://apilist.tronscanapi.com/api/account/token_asset_overview?address={address}",
    }

    headers = {}
    if network == "tron":
        headers["TRON-PRO-API-KEY"] = api_key  # Tron requires this header

    url = api_urls.get(network)
    if not url:
        print(f"❌ Unsupported network: {network}")
        return None

    try:
        response = await fetch_balance(session, url, headers)
        return process_balance_response(network, address, response)
    except Exception as e:
        print(f"⚠️  Error checking balance for {network} address {address}: {e}")
        return None


def process_balance_response(network, address, response):
    """Process the API response to extract balance."""
    if network == "tron":
        # Tron-specific response handling
        data = response.get("data", [])
        if data:
            for asset in data:
                if asset.get("tokenAbbr") == "trx" and int(asset.get("balance", 0)) > 0:
                    balance = int(asset["balance"]) / 1_000_000  # Convert from Sun to TRX
                    print(f"💰 Balance found for {address} on Tron: {balance} TRX")
                    return {"network": "tron", "address": address, "balance": balance}
        return None  # No balance found for Tron
    else:
        # EVM (Ethereum, BSC, Polygon) response handling
        balance_wei = int(response.get("result", 0))
        if balance_wei > 0:
            balance = balance_wei / 1e18  # Convert Wei to Ether
            print(f"💰 Balance found for {address} on {network.capitalize()}: {balance}")
            return {"network": network, "address": address, "balance": balance}
        return None  # No balance found


async def run_checks(derived_addresses, mnemonic):
    """Run balance checks for all derived addresses asynchronously."""
    api_keys = get_api_keys("ExplorerAPI")
    all_tasks = []

    # Configure session for optimized performance
    connector = aiohttp.TCPConnector(limit=20)  # Increased for parallel processing
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create tasks for all networks
        print("\n📋 Generated addresses for each network:")
        for network, addresses in derived_addresses.get("Bip44", {}).items():
            api_key = api_keys.get(f"{network}_key")  # Get API key for current network
            print(f"\n🌐 {network.upper()}:")
            for i, addr in enumerate(addresses, 1):
                print(f"  {i}. {addr}")
                task = check_balance(session, network, addr, api_key)
                all_tasks.append((network, task))
        
        if not all_tasks:
            return False

        print(f"\n✅ Starting balance check for {len(all_tasks)} addresses...\n")
        
        all_results = []
        network_counters = {network: 0 for network in derived_addresses.get("Bip44", {})}
        last_request_time = {network: 0 for network in derived_addresses.get("Bip44", {})}
        checked_count = 0
        
        # Process all tasks in parallel with rate limiting
        chunk_size = 8  # Process more tasks at once
        for i in range(0, len(all_tasks), chunk_size):
            chunk = all_tasks[i:i + chunk_size]
            chunk_results = []
            
            # Process chunk in parallel
            for network, task in chunk:
                current_time = time.time()
                time_since_last = current_time - last_request_time[network]
                
                # Reset counter if more than 1 second has passed
                if time_since_last >= 1:
                    network_counters[network] = 0
                
                # Wait if we've hit rate limit
                if network_counters[network] >= 4:  # Keep under 5 req/sec
                    wait_time = 1.0 - time_since_last
                    if wait_time > 0:
                        print(f"⏳ Rate limit for {network.upper()}, waiting {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                    network_counters[network] = 0
                    last_request_time[network] = time.time()
                
                try:
                    result = await asyncio.wait_for(task, timeout=10)
                    checked_count += 1
                    print(f"✓ Checked {checked_count}/{len(all_tasks)} addresses ({(checked_count/len(all_tasks)*100):.1f}%)")
                    if result is not None:
                        chunk_results.append(result)
                        print(f"💰 Found balance in {network.upper()}: {result['address']}")
                    network_counters[network] += 1
                    last_request_time[network] = time.time()
                except Exception as e:
                    checked_count += 1
                    if "Max rate limit reached" in str(e):
                        print(f"⚠️ Rate limit hit for {network.upper()}, retrying...")
                        await asyncio.sleep(0.5)
                        try:
                            result = await asyncio.wait_for(task, timeout=10)
                            if result is not None:
                                chunk_results.append(result)
                                print(f"💰 Found balance in {network.upper()}: {result['address']}")
                        except Exception:
                            continue
                    continue
            
            all_results.extend(chunk_results)
            await asyncio.sleep(0.1)  # Small delay between chunks

        print(f"\n✅ Finished checking all {len(all_tasks)} addresses!")
        
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

    print(f"✅ Balance information saved to {filename}")