import pytest
import subprocess
import shlex
import os
from pathlib import Path
import time

'''
curl -X POST "http://localhost:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@bob_student_example.json"   -F "pdf_form=@/home/rovitotv/code/taxes/2024/f1040_blank.pdf" --output processed_form.pdf
'''
def test_perfect_arguments():
    try:
        command_string = 'curl -X POST "http://mse-8:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@../bob_student_example.json"   -F "pdf_form=@/workspace/code/taxes/2024/f1040_blank.pdf" --output /workspace/temp/processed_form.pdf'
        command_list = shlex.split(command_string)
        result = subprocess.run(command_list, 
                capture_output=True, text=True, check=True)
        # check to make sure the output of processed_form.pdf exists
        file_path = Path("/workspace/temp/processed_form.pdf")
        assert file_path.exists(), f"Output file {file_path} does not exist"
        file_path.unlink()
        # Check to make sure the background tasks removed the job_dir
        time.sleep(2)
        job_directory = Path('/workspace/temp/uploads')
        for file_path in job_directory.glob('**/*'):
            if file_path.is_file():
                pytest.fail(f"There should be no files in the {job_directory} but the file {file_path} exists")
            elif file_path.is_dir():
                pytest.fail(f"There should be no directories in the {job_directory} but the directory {file_path} exists")
        
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        assert e.returncode == 2

def test_missing_arguments():
    try:
        command_string = 'curl -v -X POST "http://mse-8:8000/api/process-tax-form"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "config_file=@../bob_student_example.json"   --output /workspace/temp/processed_form.pdf'
        command_list = shlex.split(command_string)
        result = subprocess.run(command_list, 
                capture_output=True, text=True, check=True)
        #assert "HTTP/1.1 422 Unprocessable Entity" in result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        assert e.returncode == 2
