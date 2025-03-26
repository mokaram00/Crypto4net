import aiohttp
import asyncio
import json
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init()

class DiscordNotifier:
    def __init__(self, webhook_url, notification_interval, mnemonic=None):
        self.webhook_url = webhook_url
        self.notification_interval = int(notification_interval)
        self.operation_count = 0
        self.found_wallets = []
        self.start_time = datetime.now()
        self.mnemonic = mnemonic
        
    async def send_notification(self, message, embeds=None):
        """Send a notification to Discord webhook."""
        if not self.webhook_url:
            return
            
        payload = {
            "content": message,
            "username": "Crypto4net Scanner",
            "avatar_url": "https://i.imgur.com/your-icon.png"  # Add your icon URL here
        }
        
        if embeds:
            payload["embeds"] = embeds
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status not in [200, 204]:
                        print(f"{Fore.RED} Failed to send Discord notification: {response.status}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED} Error sending Discord notification: {str(e)}{Style.RESET_ALL}")

    async def send_check_complete_notification(self, checked_count, total_time, check_duration, api_duration, balance_status, total_balances):
        """Send notification when completing a batch of checks."""
        embeds = [{
            "title": "🔍 Batch Complete",
            "color": 0x2b2d31,  # Dark theme color
            "fields": [
                {
                    "name": "📊 Checked Count",
                    "value": f"```{checked_count}```",
                    "inline": True
                },
                {
                    "name": "⏱️ Total Time",
                    "value": f"```{str(total_time).split('.')[0]}```",
                    "inline": True
                },
                {
                    "name": "⚡ Last Check Duration",
                    "value": f"```{str(check_duration).split('.')[0]}```",
                    "inline": True
                },
                {
                    "name": "🌐 API Check Time",
                    "value": f"```{str(api_duration).split('.')[0]}```",
                    "inline": True
                },
                {
                    "name": "💰 Balance Status",
                    "value": "```✅ Found Balance```" if "Found" in balance_status else "```❌ No Balance```",
                    "inline": True
                },
                {
                    "name": "💎 Total Wallets",
                    "value": f"```{total_balances}```",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Crypto4net Scanner - Batch Complete",
            },
            "timestamp": datetime.now().isoformat()
        }]
        
        await self.send_notification("", embeds)

    async def notify_wallet_found(self, wallet_info):
        """Send immediate notification when a wallet is found and add it to the list."""
        self.found_wallets.append(wallet_info)
        
        # Create embed for the found wallet
        embeds = [
            {
                "title": "💎 New Wallet Found!",
                "color": 0xffd700,  # Gold color
                "fields": [
                    {
                        "name": "🌐 Network",
                        "value": f"```{wallet_info['network'].upper()}```",
                        "inline": True
                    },
                    {
                        "name": "🔑 Address",
                        "value": f"```{wallet_info['address']}```",
                        "inline": True
                    },
                    {
                        "name": "💰 Balance",
                        "value": f"```{wallet_info['balance']}```",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Crypto4net Scanner - Wallet Found",
                },
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Add seed phrase in a separate embed with warning color
        if self.mnemonic:
            embeds.append({
                "title": "🔑 Seed Phrase",
                "description": f"```{self.mnemonic}```",
                "color": 0xff0000,  # Red color for emphasis
                "footer": {
                    "text": "⚠️ Store this seed phrase securely!",
                }
            })
        
        await self.send_notification("🎉 New wallet with balance found!", embeds)
    
    async def increment_and_notify(self, total_addresses):
        """Increment operation count and send notification if interval is reached."""
        self.operation_count += 1
        
        # Send notification only when reaching notification_interval count
        if self.operation_count % int(self.notification_interval) == 0:
            await self.send_progress_update(total_addresses)
    
    async def send_progress_update(self, total_addresses):
        """Send a progress update to Discord."""
        duration = datetime.now() - self.start_time
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        seconds = duration.total_seconds() % 60
        
        # Calculate speed (addresses per minute)
        addresses_per_minute = (self.operation_count / duration.total_seconds()) * 60
        
        progress_percent = (self.operation_count / total_addresses) * 100
        
        embeds = [{
            "title": "🚀 Progress Update",
            "color": 0x2b2d31,  # Dark theme color
            "fields": [
                {
                    "name": "📊 Checked Addresses",
                    "value": f"```{self.notification_interval} addresses```",
                    "inline": True
                },
                {
                    "name": "📈 Total Progress",
                    "value": f"```{self.operation_count}/{total_addresses} ({progress_percent:.1f}%)```",
                    "inline": True
                },
                {
                    "name": "⏱️ Duration",
                    "value": f"```{int(hours)}h {int(minutes)}m {int(seconds)}s```",
                    "inline": True
                },
                {
                    "name": "⚡ Speed",
                    "value": f"```{addresses_per_minute:.1f} addresses/minute```",
                    "inline": True
                },
                {
                    "name": "💎 Found Wallets",
                    "value": f"```{len(self.found_wallets):,}```",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Crypto4net Scanner - Progress Update",
            },
            "timestamp": datetime.now().isoformat()
        }]
        
        await self.send_notification("", embeds) 