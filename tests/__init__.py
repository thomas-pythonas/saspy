import subprocess
import sys
from pathlib import Path
import importlib


def get_required_packages():
    project_root = Path(__file__).parent.parent
    main_module_path = project_root

    with open(main_module_path / "sas.py", "r") as file:
        content = file.read()

    # Extract import statements from the file content
    imports = [
        line.split()[1]
        for line in content.splitlines()
        if line.startswith("import") or line.startswith("from")
    ]
    return imports
