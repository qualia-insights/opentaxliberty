import pytest
import subprocess
import os
import shlex                                                                    
from pathlib import Path                                                        
import time
import requests

# Helper function to check if the server is running
def is_server_running(url, timeout=1):
    """Check if the FastAPI server is running by making a request to it."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

# Add skipif decorator that checks if the server is running
@pytest.mark.skipif(
    # Try to connect to the server, skip if it fails
    not is_server_running("http://mse-8:8000"),
    reason="OpenTaxLiberty server is not running"
)
def test_bad_json():
    # create a bad json file with fstring
    bad_json_block = """
    {
        "name": "Bad Json
    }
    """

    # Save debug information                                                    
    debug_logs = []                                                             
    def log_debug(message):                                                     
        debug_logs.append(message)

    try:
        with open("bad_json.json", 'w') as f:  # 'w' for write mode (overwrites if file exists)
            f.write(bad_json_block)
    except Exception as e:
        print(f"Error: error creating file: {e}") 
    
    try:
        # Execute the curl command with properly expanded paths                 
        command = [                                                             
            'curl', '-v', 'http://mse-8:8000/api/process-F1040',             
            '-H', 'accept: application/json',                                   
            '-H', 'Content-Type: multipart/form-data',                          
            '-F', f'config_file=@bad_json.json',                           
            '-F', f'pdf_form=@/workspace/code/taxes/2024/f1040_blank.pdf',                                 
            '--output', f'/worksace/temp/processed_form.pdf'
        ]                                                                       
                                                                                
        log_debug(f"Executing command: {' '.join(command)}")                    
                                                                                
        result = subprocess.run(command, capture_output=True, text=True)        
                                                                                
        # Store command results                                                 
        log_debug(f"Command exit code: {result.returncode}")                    
        log_debug(f"Command stdout: {result.stdout}")                           
        log_debug(f"Command stderr: {result.stderr}")                           
                                                                                
        # Check for successful execution                                        
        # assert result.returncode == 0, f"Command failed with return code {result.returncode}"
                                                                                
        # Check for successful HTTP response                                    
        os.remove("bad_json.json")
        assert "HTTP/1.1 400 Bad Request" in result.stderr, "Expected 400 Bad Request response was not found in curl output"

                                                                    
        # check to make sure the background tasks removed the job_dir           
        time.sleep(2)                                                           
        job_directory = Path('/workspace/temp/uploads')                         
        for file_path in job_directory.glob('**/*'):                            
            if file_path.is_file():                                             
                pytest.fail(f"There should be no files in the {job_directory} but the file {file_path} exists")
            elif file_path.is_dir():                                            
                pytest.fail(f"There should be no directories in the {job_directory} but the directory {file_path} exists")
    except Exception as e:                                                      
        # Print all debug logs if the test fails                                
        print("\n--- DEBUG INFORMATION ---")                                    
        for log in debug_logs:                                                  
            print(log)                                                          
        print("\n--- END DEBUG INFORMATION ---")                                
                                                                                
        raise

'''
def test_good_json():
    try:
        result = subprocess.run(["python3", "../opentaxliberty.py", "../bob_student_example.json"], 
                capture_output=True, text=True, check=True)
        print(f"Stdout: {result.stdout}")  # If capture_output was True
        assert result.returncode == 0
    except subprocess.CalledProcessError as e:
        # this test should never get to this point in the code
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        os.remove("bad_json.json")
        assert e.returncode == 4

def test_json_with_bad_template_file_name():
    # create a json file with fstring
    json_block = """
    {
        "F1040": {
            "configuration": {                                                            
                "tax_year": 2024,                                                          
                "template_1040_pdf": "../FILE_IS_NOT_HERE_EVER.pdf",                              
                "output_file_name": "/home/rovitotv/temp/bob_student_f1040.pdf"            
            }
        }   
    }
    """

    try:
        with open("bad_json.json", 'w') as f:  # 'w' for write mode (overwrites if file exists)
            f.write(json_block)
    except Exception as e:
        print(f"Error: error creating file: {e}") 
    
    try:
        result = subprocess.run(["python3", "../opentaxliberty.py", "bad_json.json"], 
                capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        os.remove("bad_json.json")
        assert e.returncode == 3

def test_json_with_bad_output_directory():
    # create a json file with fstring
    json_block = """
    {
        F1040": {
            "configuration": {                                                            
                "tax_year": 2024,                                                          
                "template_1040_pdf": "../f1040_template.pdf",                              
                "output_file_name": "/home/rovitotv/DIRECTORY_IS_NOT_REAL/bob_student_f1040.pdf"            
            }   
        }
    }
    """

    try:
        with open("bad_json.json", 'w') as f:  # 'w' for write mode (overwrites if file exists)
            f.write(json_block)
    except Exception as e:
        print(f"Error: error creating file: {e}") 
    
    try:
        result = subprocess.run(["python3", "../opentaxliberty.py", "bad_json.json"], 
                capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        os.remove("bad_json.json")
        assert e.returncode == 3
'''
