#!/usr/bin/env python3
"""
Script to verify imports and check for potential issues.
"""
import os
import sys
import importlib
import traceback

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)

def print_step(message):
    """Print a step message."""
    print(f"\n➡️  {message}")

def print_success(message):
    """Print a success message."""
    print(f"✅  {message}")

def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌  {message}")

def find_python_files():
    """Find all Python files in the project."""
    print_step("Finding Python files...")
    
    python_files = []
    for root, dirs, files in os.walk("."):
        if "/venv/" in root or root.startswith("./.") or "/backups/" in root:
            continue
        
        for file in files:
            if file.endswith(".py") and file != "check_imports.py" and file != "setup.py":
                python_files.append(os.path.join(root, file))
    
    print_success(f"Found {len(python_files)} Python files")
    return python_files

def extract_imports(file_path):
    """Extract import statements from a Python file."""
    imports = []
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                # Skip standard library imports
                if not any(lib in line for lib in ["os", "sys", "datetime", "json", "logging", "re", "time", "uuid", "functools", "threading", "pathlib"]):
                    imports.append(line)
    except Exception as e:
        print_error(f"Error reading {file_path}: {e}")
    
    return imports

def check_import(import_statement):
    """Check if an import statement works."""
    # Extract module name
    if import_statement.startswith("import "):
        # Handle multiple imports (import x, y, z)
        modules = [m.strip() for m in import_statement[7:].split(",")]
        module_name = modules[0].split(" as ")[0].strip()
    elif import_statement.startswith("from "):
        # Extract the "from" part
        module_name = import_statement.split("import")[0].replace("from", "").strip()
    else:
        return False, f"Unrecognized import statement: {import_statement}"
    
    # Skip third-party libraries
    third_party_libs = [
        "selenium", "pymongo", "flask", "bcrypt", "jwt", "requests", 
        "webdriver_manager", "gunicorn", "cryptography", "dotenv", "schedule"
    ]
    if module_name in third_party_libs or any(module_name.startswith(f"{lib}.") for lib in third_party_libs):
        return True, f"Skipped third-party library: {module_name}"
    
    # Try to import the module
    try:
        importlib.import_module(module_name)
        return True, f"Successfully imported {module_name}"
    except ModuleNotFoundError as e:
        return False, f"Module not found: {module_name}"
    except ImportError as e:
        return False, f"Import error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def check_file_imports(file_path):
    """Check imports in a Python file."""
    imports = extract_imports(file_path)
    
    if not imports:
        return True, [], []
    
    successful_imports = []
    failed_imports = []
    
    for import_statement in imports:
        success, message = check_import(import_statement)
        if success:
            successful_imports.append((import_statement, message))
        else:
            failed_imports.append((import_statement, message))
    
    return len(failed_imports) == 0, successful_imports, failed_imports

def main():
    """Main function."""
    print_header("Travian Whispers - Import Verification")
    
    # Find Python files
    python_files = find_python_files()
    
    # Check imports
    print_step("Checking imports...")
    
    all_successful = True
    total_failed = 0
    
    for file_path in python_files:
        success, successful_imports, failed_imports = check_file_imports(file_path)
        
        if failed_imports:
            print_error(f"Issues in {file_path}:")
            for import_statement, message in failed_imports:
                print(f"  • {import_statement} -> {message}")
            total_failed += len(failed_imports)
            all_successful = False
        else:
            print_success(f"All imports in {file_path} are valid")
    
    print_header("Import Verification Results")
    if all_successful:
        print_success("All imports are valid!")
    else:
        print_error(f"Found {total_failed} import issues")
        print("\nPossible solutions:")
        print("  1. Run setup.py to create missing directories and __init__.py files")
        print("  2. Check for typos in import statements")
        print("  3. Ensure all required packages are installed")

if __name__ == "__main__":
    main()