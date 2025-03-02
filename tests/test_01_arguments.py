import pytest
import subprocess
import os

def test_no_arguments():
    try:
        result = subprocess.run(["python3", "../opentaxliberty.py"], 
                capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        assert e.returncode == 2

def test_bad_input_file_arguments():
    try:
        result = subprocess.run(["python3", "../opentaxliberty.py","file_no_exists.json"], 
                capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        assert e.returncode == 3
