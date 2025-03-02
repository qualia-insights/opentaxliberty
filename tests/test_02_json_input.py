import pytest
import subprocess
import os

'''
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
        result = subprocess.run(["python3", "../opentaxliberty.py", "bad_json.json"], 
                capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Stdout: {e.stdout}")  # If capture_output was True
        print(f"Stderr: {e.stderr}")  # If capture_output was True
        os.remove("bad_json.json")
        assert e.returncode == 4

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
