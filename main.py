import time
import asyncio
import sys
from datetime import datetime, timedelta
from config import ( 
    install_requirements, 
    setup_config, 
    validate_config
)
from utils import (
    wait_for_internet,
    get_mnemonic_settings,
    generate_mnemonic,
    generate_seed,
    derive_addresses,
    run_checks,
    clear_console,
    print_status,
    print_separator
)
from utils.discord_notifier import DiscordNotifier
from configparser import ConfigParser
from colorama import Fore, Style, init

# Initialize colorama
init()

def print_epic_banner():
    banner = f"""
    {Fore.BLUE}╔══════════════════════════════════════════════════════════════════════════╗
    ║     {Fore.CYAN}██████╗  █████╗ ██████╗ ██╗  ██╗███╗   ██╗███████╗███████╗███████╗{Fore.BLUE}    ║
    ║     {Fore.CYAN}██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝████╗  ██║██╔════╝██╔════╝██╔════╝{Fore.BLUE}    ║
    ║     {Fore.CYAN}██║  ██║███████║██████╔╝█████╔╝ ██╔██╗ ██║█████╗  ███████╗███████╗{Fore.BLUE}    ║
    ║     {Fore.CYAN}██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║╚██╗██║██╔══╝  ╚════██║╚════██║{Fore.BLUE}    ║
    ║     {Fore.CYAN}██████╔╝██║  ██║██║  ██║██║  ██╗██║ ╚████║███████╗███████║███████║{Fore.BLUE}    ║
    ║     {Fore.CYAN}╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝{Fore.BLUE}    ║
    ║                                                                              ║
    ║     {Fore.RED}╔════════════════════════════════════════════════════════════════════╗{Fore.BLUE}    ║
    ║     {Fore.RED}║     {Fore.YELLOW}Welcome to the Darkness - Where Magic Happens{Fore.RED}                    ║{Fore.BLUE}    ║
    ║     {Fore.RED}╚════════════════════════════════════════════════════════════════════╝{Fore.BLUE}    ║
    ║                                                                              ║
    ║     {Fore.YELLOW}Developer:{Fore.RED} Mokaram {Fore.YELLOW}| Discord:{Fore.CYAN} .69h.{Fore.BLUE}                                  ║
    ║     {Fore.YELLOW}Join our Discord:{Fore.CYAN} discord.gg/ezcpCsxYc8{Fore.BLUE}                                ║
    ║                                                                              ║
    ║     {Fore.RED}╔════════════════════════════════════════════════════════════════════╗{Fore.BLUE}    ║
    ║     {Fore.RED}║     {Fore.CYAN}Unleash the Power of Darkness{Fore.RED}                                    ║{Fore.BLUE}    ║
    ║     {Fore.RED}╚════════════════════════════════════════════════════════════════════╝{Fore.BLUE}    ║
    ╚══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

async def main():
    # Display epic banner
    print_epic_banner()

    # Check if in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "TEST_MODE":
        print_status("Running in TEST MODE...")
        await run_checks({"Bip44": {}}, "TEST_MODE")
        return

    # Step 1: Check for internet connection
    print_status(f"{Fore.CYAN} Checking for internet connection...{Style.RESET_ALL}")
    wait_for_internet()

    # Step 2: Install required packages
    print_status(f"{Fore.YELLOW} Installing dependencies...{Style.RESET_ALL}")
    install_requirements()

    # Step 3: Run configuration setup
    print_status(f"{Fore.MAGENTA} Running configuration setup...{Style.RESET_ALL}")
    config_path = setup_config()

    # Step 4: Validate configuration
    print_status(f"{Fore.BLUE} Validating configuration...{Style.RESET_ALL}")
    if not validate_config(config_path):
        print_status(f"{Fore.RED} Environment setup is incomplete. Please resolve the issues in the configuration file.{Style.RESET_ALL}")
        return

    # Initialize Discord Notifier
    config = ConfigParser()
    config.read(config_path)
    discord_webhook = config.get('Discord', 'webhook_url')
    notification_interval = config.get('Discord', 'notification_interval', fallback='1')
    discord_notifier = DiscordNotifier(discord_webhook, notification_interval)

    # Start the continuous checking loop
    checked_counter = 1
    script_start_time = time.time()
    last_check_duration = timedelta(0)
    last_api_check_duration = timedelta(0)
    last_balance_status = "No balance found"
    total_balances_found = 0

    print(f"\n{Fore.CYAN} Starting continuous wallet generation and balance checks... (Press Ctrl+C to stop)\n{Style.RESET_ALL}")

    try:
        while True:
            check_start_time = time.time()
            
            # Generate and check wallets
            word_count, address_count = get_mnemonic_settings()
            mnemonic = generate_mnemonic(word_count)
            seed_bytes = generate_seed(mnemonic)
            derived_addresses = derive_addresses(seed_bytes)

            # Check balances
            api_start_time = time.time()
            try:
                balances_found = await run_checks(derived_addresses, mnemonic, discord_notifier)
                api_end_time = time.time()
                last_api_check_duration = timedelta(seconds=(api_end_time - api_start_time))

                    # Update status
                if balances_found:
                    last_balance_status = f"{Fore.GREEN} Balance Found!{Style.RESET_ALL}"
                    total_balances_found += 1
                else:
                    last_balance_status = f"{Fore.RED} No balance found{Style.RESET_ALL}"

                # Update timing
                check_end_time = time.time()
                last_check_duration = timedelta(seconds=(check_end_time - check_start_time))
                total_elapsed_time = timedelta(seconds=(check_end_time - script_start_time))

                # Send notification if we've reached the notification interval
                if discord_notifier and checked_counter % int(discord_notifier.notification_interval) == 0:
                    await discord_notifier.send_check_complete_notification(
                        checked_counter,
                        total_elapsed_time,
                        last_check_duration,
                        last_api_check_duration,
                        last_balance_status,
                        total_balances_found
                    )

                # Display status
                clear_console()
                print_epic_banner()
                print_separator()
                print_status(f"Total Script Runtime: {Fore.CYAN}{total_elapsed_time}{Style.RESET_ALL}")
                print_status(f"Checked {Fore.YELLOW}{checked_counter}{Style.RESET_ALL} at {Fore.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
                print_status(f"Previous Check completed in {Fore.CYAN}{last_check_duration}{Style.RESET_ALL}")
                print_status(f"API Check Time: {Fore.CYAN}{last_api_check_duration}{Style.RESET_ALL}")
                print_status(f"Check Result: {last_balance_status}")
                print_status(f"Total Balances Found: {Fore.YELLOW}{total_balances_found}{Style.RESET_ALL}")
                print_separator()

                checked_counter += 1

            except Exception as e:
                print(f"{Fore.RED} Error during balance check: {e}{Style.RESET_ALL}")
                await asyncio.sleep(0.5)  # Reduced error delay
                continue

    except KeyboardInterrupt:
        print_status(f"{Fore.RED} Script manually stopped by user.{Style.RESET_ALL}")
        total_run_time = timedelta(seconds=(time.time() - script_start_time))
        print_status(f"Total script runtime: {Fore.CYAN}{total_run_time}{Style.RESET_ALL}")
        print_status(f"Total balances found during the session: {Fore.YELLOW}{total_balances_found}{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED} Program terminated by user{Style.RESET_ALL}")