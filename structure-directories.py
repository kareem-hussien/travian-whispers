#!/usr/bin/env python3
"""
Script to set up the directory structure for Travian Whispers.
"""
import os
import sys

# Base directories to create
directories = [
    "database",
    "database/models",
    "auth",
    "email",
    "email/templates",
    "payment",
    "web",
    "web/routes",
    "web/static",
    "web/static/css",
    "web/static/js",
    "web/static/img",
    "web/templates",
    "web/templates/auth",
    "web/templates/admin",
    "web/templates/user",
    "web/templates/payment",
    "web/templates/errors",
    "startup",
    "tasks",
    "tasks/trainer",
    "info",
    "info/maps",
    "info/profile"
]

# Create directories
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

# Create __init__.py files in Python packages
for directory in directories:
    if "/" in directory:  # Only create in subdirectories
        init_file = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write('"""Package initialization."""\n')
            print(f"Created: {init_file}")

print("\nDirectory structure set up successfully!")
