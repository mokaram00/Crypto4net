import os
import subprocess
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init()

def print_epic_banner():
    banner = f"""
    {Fore.MAGENTA}╔══════════════════════════════════════════════════════════════════════════╗
    ║     {Fore.CYAN}██████╗  █████╗ ██████╗ ██╗  ██╗███╗   ██╗███████╗███████╗███████╗{Fore.MAGENTA}    ║
    ║     {Fore.CYAN}██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝████╗  ██║██╔════╝██╔════╝██╔════╝{Fore.MAGENTA}    ║
    ║     {Fore.CYAN}██║  ██║███████║██████╔╝█████╔╝ ██╔██╗ ██║█████╗  ███████╗███████╗{Fore.MAGENTA}    ║
    ║     {Fore.CYAN}██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║╚██╗██║██╔══╝  ╚════██║╚════██║{Fore.MAGENTA}    ║
    ║     {Fore.CYAN}██████╔╝██║  ██║██║  ██║██║  ██╗██║ ╚████║███████╗███████║███████║{Fore.MAGENTA}    ║
    ║     {Fore.CYAN}╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝{Fore.MAGENTA}    ║
    ║                                                                              ║
    ║     {Fore.RED}Welcome to the Darkness - Where Magic Happens{Fore.MAGENTA}                          ║
    ║                                                                              ║
    ║     {Fore.YELLOW}Developer:{Fore.RED} Mokaram {Fore.YELLOW}| Discord:{Fore.CYAN} .69h.{Fore.MAGENTA}                                  ║
    ║     {Fore.YELLOW}Join our Discord:{Fore.CYAN} discord.gg/ezcpCsxYc8{Fore.MAGENTA}                                ║
    ║                                                                              ║
    ║     {Fore.RED}Unleash the Power of Darkness{Fore.MAGENTA}                                        ║
    ╚══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def get_user_preferences():
    """Get user preferences for the build."""
    print_epic_banner()
    print("\nProgram Customization")
    print("=" * 50)
    
    # Get executable name
    exe_name = input("\nEnter program name (Press Enter to use 'Crypto4net'): ").strip()
    exe_name = exe_name if exe_name else "Crypto4net"
    
    # Get icon path
    while True:
        icon_path = input("\nProgram icon path (Press Enter to skip this option): ").strip()
        if not icon_path:
            icon_path = None
            break
        if os.path.exists(icon_path) and icon_path.endswith('.ico'):
            break
        print("Invalid path or file is not .ico format")
    
    # Get version info
    version = input("\nProgram version (Press Enter to use '1.0.0'): ").strip()
    version = version if version else "1.0.0"
    
    # Get company name
    company = input("\nCompany name (Press Enter to skip): ").strip()
    
    # Get description
    description = input("\nProgram description (Press Enter to skip): ").strip()
    
    return {
        "exe_name": exe_name,
        "icon_path": icon_path,
        "version": version,
        "company": company,
        "description": description
    }

def create_version_file(prefs):
    """Create version info file for the executable."""
    version_info = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({",".join([str(int(x)) for x in prefs["version"].split(".")] + ["0"]*(4-len(prefs["version"].split("."))))}),
    prodvers=({",".join([str(int(x)) for x in prefs["version"].split(".")] + ["0"]*(4-len(prefs["version"].split("."))))}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{prefs["company"]}'),
         StringStruct(u'FileDescription', u'{prefs["description"]}'),
         StringStruct(u'FileVersion', u'{prefs["version"]}'),
         StringStruct(u'InternalName', u'{prefs["exe_name"]}'),
         StringStruct(u'LegalCopyright', u'© {datetime.now().year} {prefs["company"]}'),
         StringStruct(u'OriginalFilename', u'{prefs["exe_name"]}.exe'),
         StringStruct(u'ProductName', u'{prefs["exe_name"]}'),
         StringStruct(u'ProductVersion', u'{prefs["version"]}')]
      )
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    return 'version_info.txt'

def install_requirements():
    """Install required packages for building."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {str(e)}")
        sys.exit(1)

def protect_source():
    """Protect source code using PyArmor."""
    try:
        print("\nProtecting source code...")
        
        # First create a spec file for PyArmor
        subprocess.check_call([
            "pyarmor", "init",
            "--src", ".",
            "--entry", "main.py"
        ])
        
        # Then build with the spec file
        subprocess.check_call([
            "pyarmor", "build",
            "--clean",
            "--no-runtime",
            "main.py"
        ])
        
        # Move the protected file to the correct location
        if os.path.exists("dist/main.py"):
            return True
            
        return False
    except Exception as e:
        print(f"Warning: Code encryption failed. Reason: {str(e)}")
        print("Continuing without additional encryption...")
        return False

def build_exe(prefs):
    """Build the executable using PyInstaller."""
    version_file = create_version_file(prefs)
    
    # Try to protect source code
    protected = protect_source()
    
    # Get bip_utils package location
    import bip_utils
    bip_utils_path = os.path.dirname(bip_utils.__file__)
    wordlist_path = os.path.join(bip_utils_path, "bip", "bip39", "wordlist")
    
    # Create build command with anti-virus bypass options
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--clean",
        "--name", prefs["exe_name"],
        "--version-file", version_file,
        # Add all necessary data files
        "--add-data", f"{wordlist_path};bip_utils/bip/bip39/wordlist",
        "--add-data", "config_setups;config_setups",
        # Add all required imports
        "--hidden-import", "aiohttp",
        "--hidden-import", "asyncio",
        "--hidden-import", "configparser",
        "--hidden-import", "datetime",
        "--hidden-import", "json",
        "--hidden-import", "bip_utils",
        "--hidden-import", "bip_utils.bip.bip39",
        "--collect-submodules", "bip_utils",
        "--strip"
    ]
    
    # Add icon if specified
    if prefs["icon_path"]:
        cmd.extend(["--icon", prefs["icon_path"]])
    
    # Add the protected script or original if protection failed
    if protected and os.path.exists("dist/main.py"):
        cmd.append("dist/main.py")
    else:
        cmd.append("main.py")
    
    try:
        print("\nBuilding program...")
        # Run PyInstaller
        subprocess.check_call(cmd)
        
        # Clean up temporary files
        cleanup_files = ['build', 'dist/main.py', version_file, '*.spec', '__pycache__']
        for file in cleanup_files:
            try:
                if os.path.isfile(file):
                    os.remove(file)
                elif os.path.isdir(file):
                    import shutil
                    shutil.rmtree(file)
            except:
                pass
            
        print("\nProgram built successfully!")
        print(f"You can find the executable in the 'dist' folder named {prefs['exe_name']}.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building program: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting build process...")
    
    # Get user preferences
    prefs = get_user_preferences()
    
    print("\nInstalling requirements...")
    install_requirements()
    
    print("\nBuilding program...")
    build_exe(prefs)