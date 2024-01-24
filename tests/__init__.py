import os
import subprocess
import sys
from pathlib import Path
import importlib

def get_required_packages():
    project_root = Path(__file__).parent.parent  # Assuming tests directory is one level below the project root
    main_module_path = project_root / 'sas'  # Replace 'your_module' with the actual module name

    with open(main_module_path / 'sas.py', 'r') as file:
        content = file.read()

    # Extract import statements from the file content
    imports = [line.split()[1] for line in content.splitlines() if line.startswith('import') or line.startswith('from')]
    return imports

def check_and_install_dependencies():
    required_packages = get_required_packages()

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            print(f"Package {package} is not installed. Installing...")
            try:
                subprocess.check_output([sys.executable, '-m', 'pip', 'install', package])
            except subprocess.CalledProcessError as e:
                print(f"Error installing {package}: {e}")
                sys.exit(1)


print("Checking for config file....")

config_file = os.path.join(os.path.dirname(__file__), '../config.yml')
if not os.path.exists(config_file):
    print("Config File not found, exiting...")
    sys.exit(1)

print("Config file found ! Moving on...")
print("Checking for required python modules...")
check_and_install_dependencies()
print()