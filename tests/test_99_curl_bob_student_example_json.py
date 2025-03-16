import pytest
import subprocess
import os
import json
from pathlib import Path
import time
import contextlib
from io import StringIO

def test_process_tax_form_with_curl():
    """
    Test the OpenTaxLiberty API by executing a curl command to process a tax form.
    This test verifies:
    1. The API responds with a 200 OK status
    2. The output PDF file is created
    3. The temporary job directory is cleaned up after processing
    4. If debug_json_output is specified in the config, the debug JSON file exists
    
    Detailed debug information is only printed if the test fails.
    The output PDF file is kept after the test for inspection.
    """
    # In the container, the home directory is mounted to /workspace
    workspace_dir = "/workspace"
    
    # Save debug information
    debug_logs = []
    def log_debug(message):
        debug_logs.append(message)
    
    # Define paths using the workspace directory
    output_dir = f"{workspace_dir}/temp"
    output_filename = "processed_form.pdf"
    output_path = f"{output_dir}/{output_filename}"
    pdf_form_path = f"{workspace_dir}/code/taxes/2024/f1040_blank.pdf"
    config_file_path = "../bob_student_F1040.json"
    w2_config_file_path = "../bob_student_W-2.json"
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Delete the output file if it already exists
        output_file = Path(output_path)
        if output_file.exists():
            output_file.unlink()
            log_debug(f"Deleted existing output file: {output_path}")
        
        # Verify files exist
        pdf_form = Path(pdf_form_path)
        log_debug(f"PDF form exists: {pdf_form.exists()} at {pdf_form_path}")
        assert pdf_form.exists(), f"PDF form template does not exist at {pdf_form_path}"
        
        config_file = Path(config_file_path)
        log_debug(f"Config file exists: {config_file.exists()} at {config_file_path}")
        assert config_file.exists(), f"Config file does not exist at {config_file_path}"
        
        w2_config_file = Path(w2_config_file_path)
        log_debug(f"W-2 config file exists: {w2_config_file.exists()} at {w2_config_file_path}")
        assert w2_config_file.exists(), f"W-2 config file does not exist at {w2_config_file_path}"
        
        # Parse the JSON configuration to check for debug_json_output
        with open(config_file_path, 'r') as f:
            config_data = json.load(f)
        
        debug_json_path = None
        if 'configuration' in config_data and 'debug_json_output' in config_data['configuration']:
            debug_json_path = config_data['configuration']['debug_json_output']
            log_debug(f"Debug JSON output is configured at: {debug_json_path}")
            
            # Delete the debug JSON file if it already exists
            debug_json_file = Path(debug_json_path)
            if debug_json_file.exists():
                debug_json_file.unlink()
                log_debug(f"Deleted existing debug JSON file: {debug_json_path}")
        
        # Log the current working directory
        cwd = os.getcwd()
        log_debug(f"Current working directory: {cwd}")
        
        # Execute the curl command with properly expanded paths
        command = [
            'curl', '-v', 'http://mse-8:8000/api/process-tax-form',
            '-H', 'accept: application/json',
            '-H', 'Content-Type: multipart/form-data',
            '-F', f'config_file=@{config_file_path}',
            '-F', f'W_2_config_file=@{w2_config_file_path}',
            '-F', f'pdf_form=@{pdf_form_path}',
            '--output', output_path
        ]
        
        log_debug(f"Executing command: {' '.join(command)}")
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Store command results
        log_debug(f"Command exit code: {result.returncode}")
        log_debug(f"Command stdout: {result.stdout}")
        log_debug(f"Command stderr: {result.stderr}")
        
        # Check for successful execution
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Check for successful HTTP response
        assert "HTTP/1.1 200 OK" in result.stderr, "Expected 200 OK response was not found in curl output"
        
        # Check if output file exists
        time.sleep(1)  # Brief pause to allow file system to update
        log_debug(f"Checking for output file at: {output_path}")
        if output_file.exists():
            log_debug(f"Output file found with size: {output_file.stat().st_size} bytes")
        else:
            log_debug(f"Output file NOT found at: {output_path}")
            
            # List files in output directory
            log_debug(f"Files in {output_dir}:")
            for file in Path(output_dir).glob("*"):
                log_debug(f"  {file.name} ({file.stat().st_size} bytes)")
        
        # Check that the output file was created
        assert output_file.exists(), f"Output file {output_path} was not created"
        
        # Check the file size to ensure it's not empty
        assert output_file.stat().st_size > 0, f"Output file {output_path} exists but is empty"
        
        # Check for debug JSON file if it was configured
        if debug_json_path:
            debug_json_file = Path(debug_json_path)
            log_debug(f"Checking for debug JSON file at: {debug_json_path}")
            if debug_json_file.exists():
                log_debug(f"Debug JSON file found with size: {debug_json_file.stat().st_size} bytes")
            else:
                log_debug(f"Debug JSON file NOT found at: {debug_json_path}")
            
            # Assert that the debug JSON file exists
            assert debug_json_file.exists(), f"Debug JSON file was not created at {debug_json_path}"
            
            # Assert that the debug JSON file is not empty
            assert debug_json_file.stat().st_size > 0, f"Debug JSON file exists but is empty at {debug_json_path}"
            
            # Verify the JSON file is valid
            try:
                with open(debug_json_path, 'r') as f:
                    debug_json_content = json.load(f)
                log_debug("Debug JSON file contains valid JSON")
            except json.JSONDecodeError as e:
                log_debug(f"Debug JSON file contains invalid JSON: {str(e)}")
                assert False, f"Debug JSON file contains invalid JSON: {str(e)}"
        
        # Wait for background task to complete (file cleanup)
        time.sleep(2)
        
        # Verify that the job directory was cleaned up
        job_directory = Path(f"{workspace_dir}/temp/uploads")
        
        log_debug(f"Uploads directory exists: {job_directory.exists()} at {job_directory}")
        if job_directory.exists():
            files_in_directory = list(job_directory.glob("**/*"))
            if files_in_directory:
                log_debug(f"Files found in uploads directory: {[str(f) for f in files_in_directory]}")
            else:
                log_debug("Uploads directory is empty")
        
        assert job_directory.exists(), "Uploads directory should exist"
        
        # The job directory should be empty (no files or subdirectories)
        files_in_directory = list(job_directory.glob("**/*"))
        assert len(files_in_directory) == 0, f"Expected empty uploads directory, found: {files_in_directory}"
        
        # Just print a simple success message
        print("OpenTaxLiberty API test successful")
        print(f"Output PDF saved at: {output_path}")
        if debug_json_path and Path(debug_json_path).exists():
            print(f"Debug JSON saved at: {debug_json_path}")
        
    except Exception as e:
        # Print all debug logs if the test fails
        print("\n--- DEBUG INFORMATION ---")
        for log in debug_logs:
            print(log)
        print("\n--- END DEBUG INFORMATION ---")
        
        raise
    # No cleanup to allow inspection of output files
