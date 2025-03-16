import pytest
import subprocess
import os
import shlex                                                                    
from pathlib import Path                                                        
import time


def test_bad_json():
    # create a bad json file with fstring
    bad_json_block = """
    {
        "name": "Bad Json
    }
    """

    try:
        with open("bad_json.json", 'w') as f:  # 'w' for write mode (overwrites if file exists)
            f.write(bad_json_block)
    except Exception as e:
        print(f"Error: error creating file: {e}") 
    
    try:
        command_string = 'curl -v "http://mse-8:8000/api/process-tax-form" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "config_file=@bad_json.json" -F "W_2_config_file=@../bob_student_W2.json" -F "pdf_form=@/workspace/code/taxes/2024/f1040_blank.pdf" --output /workspace/temp/processed_form.pdf'
        command_list = shlex.split(command_string)                              
        result = subprocess.run(command_list,                                   
                capture_output=True, text=True, check=True)
        os.remove("bad_json.json")
        assert "HTTP/1.1 400 Bad Request" in result.stderr, "result code of 400 was not found in curl output"
                                                                    
        # check to make sure the background tasks removed the job_dir           
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
        assert e.returncode == 4

def test_bad_w2_json():
    # Create a bad W2 JSON file
    bad_w2_json_block = """
    {
        "configuration": {
            "tax_year": 2024,
            "form": "W2
        }
    }
    """

    try:
        with open("bad_w2_json.json", 'w') as f:
            f.write(bad_w2_json_block)
    except Exception as e:
        print(f"Error: error creating file: {e}")
    
    try:
        command_string = 'curl -v "http://mse-8:8000/api/process-tax-form" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "config_file=@../bob_student_F1040.json" -F "W_2_config_file=@bad_w2_json.json" -F "pdf_form=@/workspace/code/taxes/2024/f1040_blank.pdf" --output /workspace/temp/processed_form.pdf'
        command_list = shlex.split(command_string)
        result = subprocess.run(command_list,
                capture_output=True, text=True, check=True)
        os.remove("bad_w2_json.json")
        assert "HTTP/1.1 400 Bad Request" in result.stderr, "result code of 400 was not found in curl output"
        
        # check to make sure the background tasks removed the job_dir
        time.sleep(2)
        job_directory = Path('/workspace/temp/uploads')
        for file_path in job_directory.glob('**/*'):
            if file_path.is_file():
                pytest.fail(f"There should be no files in the {job_directory} but the file {file_path} exists")
            elif file_path.is_dir():
                pytest.fail(f"There should be no directories in the {job_directory} but the directory {file_path} exists")
                
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        assert e.returncode == 4

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
        "configuration": {                                                            
            "tax_year": 2024,                                                          
            "template_1040_pdf": "../FILE_IS_NOT_HERE_EVER.pdf",                              
            "output_file_name": "/home/rovitotv/temp/bob_student_f1040.pdf"            
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
        "configuration": {                                                            
            "tax_year": 2024,                                                          
            "template_1040_pdf": "../f1040_template.pdf",                              
            "output_file_name": "/home/rovitotv/DIRECTORY_IS_NOT_REAL/bob_student_f1040.pdf"            
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
