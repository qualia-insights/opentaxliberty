import pytest
import subprocess
import os
from pathlib import Path
import time
import logging

# Set up logging - use a higher level to make sure messages are shown
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_process_tax_form_with_curl(caplog):
    """
    Test the OpenTaxLiberty API by executing a curl command to process a tax form.
    """
    # Set the log level for this test
    caplog.set_level(logging.DEBUG)
    
    # In the container, the home directory is mounted to /workspace
    workspace_dir = "/workspace"
    print(f"Workspace directory: {workspace_dir}")
    logger.info(f"Workspace directory: {workspace_dir}")
    
    # Define paths using the workspace directory
    output_dir = f"{workspace_dir}/temp"
    output_filename = "processed_form.pdf"
    output_path = f"{output_dir}/{output_filename}"
    pdf_form_path = f"{workspace_dir}/code/taxes/2024/f1040_blank.pdf"
    config_file_path = "../bob_student_example.json"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Delete the output file if it already exists
    output_file = Path(output_path)
    if output_file.exists():
        output_file.unlink()
        print(f"Deleted existing output file: {output_path}")
    
    # Verify files exist
    pdf_form = Path(pdf_form_path)
    print(f"PDF form exists: {pdf_form.exists()} at {pdf_form_path}")
    
    config_file = Path(config_file_path)
    print(f"Config file exists: {config_file.exists()} at {config_file_path}")
    
    # Log the current working directory
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")
    
    # Fail with helpful message if files don't exist
    assert pdf_form.exists(), f"PDF form template does not exist at {pdf_form_path}"
    assert config_file.exists(), f"Config file does not exist at {config_file_path}"
    
    try:
        # Execute the curl command with properly expanded paths
        command = [
            'curl', '-v', 'http://mse-8:8000/api/process-tax-form',
            '-H', 'accept: application/json',
            '-H', 'Content-Type: multipart/form-data',
            '-F', f'config_file=@{config_file_path}',
            '-F', f'pdf_form=@{pdf_form_path}',
            '--output', output_path
        ]
        
        print(f"Executing command: {' '.join(command)}")
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Print the command result
        print(f"Command exit code: {result.returncode}")
        if result.stdout:
            print(f"Command stdout: {result.stdout}")
        if result.stderr:
            print(f"Command stderr: {result.stderr}")
        
        # Check for successful execution
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Check for successful HTTP response
        assert "HTTP/1.1 200 OK" in result.stderr, "Expected 200 OK response was not found in curl output"
        
        # Check if output file exists
        time.sleep(1)  # Brief pause to allow file system to update
        print(f"Checking for output file at: {output_path}")
        if output_file.exists():
            print(f"Output file found with size: {output_file.stat().st_size} bytes")
        else:
            print(f"Output file NOT found at: {output_path}")
            
            # List files in output directory
            print(f"Files in {output_dir}:")
            for file in Path(output_dir).glob("*"):
                print(f"  {file.name} ({file.stat().st_size} bytes)")
        
        # Check that the output file was created
        assert output_file.exists(), f"Output file {output_path} was not created"
        
        # Check the file size to ensure it's not empty
        assert output_file.stat().st_size > 0, f"Output file {output_path} exists but is empty"
        
        # Wait for background task to complete (file cleanup)
        time.sleep(2)
        
        # Verify that the job directory was cleaned up
        job_directory = Path(f"{workspace_dir}/temp/uploads")
        
        print(f"Uploads directory exists: {job_directory.exists()} at {job_directory}")
        if job_directory.exists():
            files_in_directory = list(job_directory.glob("**/*"))
            if files_in_directory:
                print(f"Files found in uploads directory: {[str(f) for f in files_in_directory]}")
            else:
                print("Uploads directory is empty")
        
        assert job_directory.exists(), "Uploads directory should exist"
        
        # The job directory should be empty (no files or subdirectories)
        files_in_directory = list(job_directory.glob("**/*"))
        assert len(files_in_directory) == 0, f"Expected empty uploads directory, found: {files_in_directory}"
        
    except Exception as e:
        print(f"Test failed with exception: {str(e)}")
        raise
    finally:
        # Check if output file exists before attempting to delete
        if output_file.exists():
            print(f"Cleaning up output file: {output_path}")
            # output_file.unlink() ## lets not delete the file we are looking for
        else:
            print(f"Cannot clean up output file: {output_path} (file not found)")
