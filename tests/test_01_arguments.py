import pytest
import subprocess
import shlex
import os

'''
curl -X POST "http://localhost:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@bob_student_example.json"   -F "pdf_form=@/home/rovitotv/code/taxes/2024/f1040_blank.pdf" --output processed_form.pdf
'''
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
