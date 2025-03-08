import os
import subprocess
import sys

def install_requirements():
    """Install required packages for building."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_exe():
    """Build the executable using PyInstaller."""
    # Create build command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--icon=assets/icon.ico" if os.path.exists("assets/icon.ico") else None,
        "--name=Crypto4net",
        "--add-data=config_setups;config_setups",
        "--hidden-import=aiohttp",
        "--hidden-import=asyncio",
        "--hidden-import=configparser",
        "--hidden-import=datetime",
        "--hidden-import=json",
        "main.py"
    ]
    
    # Remove None values from command
    cmd = [x for x in cmd if x is not None]
    
    # Run PyInstaller
    subprocess.check_call(cmd)
    
    print("\n✅ Build completed successfully!")
    print("📁 Executable can be found in the 'dist' folder")

if __name__ == "__main__":
    print("🔨 Starting build process...")
    print("\n📦 Installing requirements...")
    install_requirements()
    print("\n🚀 Building executable...")
    build_exe() 