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


async def main():
    # Check if in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "TEST_MODE":
        print_status("Running in TEST MODE...", symbol="🧪")
        await run_checks({"Bip44": {}}, "TEST_MODE")
        return

    # Step 1: Check for internet connection
    print_status("Checking for internet connection...", symbol="🌐")
    wait_for_internet()

    # Step 2: Install required packages
    print_status("Installing dependencies...", symbol="🛠️")
    install_requirements()

    # Step 3: Run configuration setup
    print_status("Running configuration setup...", symbol="🛠️")
    config_path = setup_config()

    # Step 4: Validate configuration
    print_status("Validating configuration...", symbol="✅")
    if not validate_config(config_path):
        print_status("Environment setup is incomplete. Please resolve the issues in the configuration file.", symbol="❌")
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

    print("\n🔁 Starting continuous wallet generation and balance checks... (Press Ctrl+C to stop)\n")

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
                    last_balance_status = "Balance Found!"
                    total_balances_found += 1
                else:
                    last_balance_status = "No balance found"

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
                print_separator()
                print_status(f"Total Script Runtime: {total_elapsed_time}", symbol="⏱️")
                print_status(f"Checked {checked_counter} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", symbol="🔄")
                print_status(f"Previous Check completed in {last_check_duration}", symbol="✅")
                print_status(f"API Check Time: {last_api_check_duration}", symbol="🌐")
                print_status(f"Check Result: {last_balance_status}", symbol="💰")
                print_status(f"Total Balances Found: {total_balances_found}", symbol="📊")
                print_separator()

                checked_counter += 1

            except Exception as e:
                print(f"⚠️ Error during balance check: {e}")
                await asyncio.sleep(0.5)  # Reduced error delay
                continue

    except KeyboardInterrupt:
        print_status("Script manually stopped by user.", symbol="🛑")
        total_run_time = timedelta(seconds=(time.time() - script_start_time))
        print_status(f"Total script runtime: {total_run_time}", symbol="⏱️")
        print_status(f"Total balances found during the session: {total_balances_found}", symbol="📊")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Program terminated by user")