import subprocess
import sys
import os

def install_requirements():
    """Install all required packages."""
    print("🛠️ Installing required packages...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        print("\n🚀 You can now run the program using the command:")
        print("python main.py")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt file not found!")
        sys.exit(1)
        
    install_requirements() 