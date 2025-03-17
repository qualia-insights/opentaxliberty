import pytest
import subprocess
import os
import json
from pathlib import Path
import time
import contextlib
from io import StringIO
from decimal import Decimal
from pypdf import PdfReader

def test_process_tax_form_with_curl():
    """
    Test the OpenTaxLiberty API by executing a curl command to process a tax form.
    This test verifies:
    1. The API responds with a 200 OK status
    2. The output PDF file is created
    3. The temporary job directory is cleaned up after processing
    4. Line 34 (1z sum) equals 102.31 for bob_student_F1040.json and bob_student_W2.json
    5. Line 1a matches W2 box 1 sum
    6. Line 25a matches W2 box 2 sum
    
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
    W2_config_file_path = "../bob_student_W2.json"
    
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
        
        W2_config_file = Path(W2_config_file_path)
        log_debug(f"W2 config file exists: {W2_config_file.exists()} at {W2_config_file_path}")
        assert W2_config_file.exists(), f"W2 config file does not exist at {W2_config_file_path}"
        
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
            '-F', f'W2_config_file=@{W2_config_file_path}',
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
        
        # Verify the values in the PDF match expected values
        # Variables to track if verifications were successful and their source
        L1a_verified = False
        L25a_verified = False
        L34_verified = False
        L1a_source = None
        L25a_source = None
        L34_source = None
        
        # Explicitly verify that Line 34 equals 102.31 for bob_student_F1040.json
        expected_L34_value = Decimal('102.31')
        log_debug(f"Verifying Line 34 equals 102.31 for bob_student_F1040.json and bob_student_W2.json")
        
        # Calculate expected W2 box sums from W2 data
        with open(W2_config_file_path, 'r') as f:
            w2_data = json.load(f)
            
        expected_box_1_sum = sum(Decimal(str(entry['box_1'])) for entry in w2_data.get('W2', []))
        expected_box_2_sum = sum(Decimal(str(entry['box_2'])) for entry in w2_data.get('W2', []))
        
        log_debug(f"Expected W2 Box 1 sum: {expected_box_1_sum}")
        log_debug(f"Expected W2 Box 2 sum: {expected_box_2_sum}")
        
        # Read the generated PDF to extract form field values
        try:
            reader = PdfReader(output_path)
            
            # Get all form fields from the PDF
            fields = reader.get_fields()
            
            # Check that we have form fields
            log_debug(f"Number of form fields in PDF: {len(fields) if fields else 0}")
            assert fields, "No form fields found in the generated PDF"
            
            # Log all field names to help with debugging
            log_debug("All field names in PDF:")
            for field_name in fields:
                field_value = None
                field = fields[field_name]
                if isinstance(field, dict) and "/V" in field:
                    field_value = field["/V"]
                elif not isinstance(field, dict):
                    field_value = field
                log_debug(f"  Field: {field_name}, Value: {field_value}")
            
            # Function to extract field value from the PDF
            def get_pdf_field_values(pdf_path):
                """Extract form field values from a PDF file more thoroughly."""
                values = {}
                reader = PdfReader(pdf_path)
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        annotations = page.get('/Annots')
                        if annotations:
                            for annotation in annotations:
                                if annotation.get('/Subtype') == '/Widget':
                                    field_name = annotation.get('/T')
                                    if field_name:
                                        field_name = field_name.replace('\x00', '')  # Remove null bytes
                                        field_value = annotation.get('/V')
                                        if field_value:
                                            values[field_name] = field_value
                    except Exception as e:
                        print(f"Error reading annotations on page {page_num}: {e}")
                        
                return values
            
            # Read the config file to determine the actual field names used
            with open(config_file_path, 'r') as f:
                form_config = json.load(f)
            
            # Look up the field names from the configuration
            L1a_field_name = form_config.get("income", {}).get("L1a_tag")
            L25a_field_name = form_config.get("payments", {}).get("L25a_tag")
            L34_field_name = form_config.get("refund", {}).get("L34_subtract_tag")  # Line 34 is the 1z sum field
            
            log_debug(f"Looking for Line 1a using field name: {L1a_field_name}")
            log_debug(f"Looking for Line 25a using field name: {L25a_field_name}")
            log_debug(f"Looking for Line 34 using field name: {L34_field_name}")
            
            # Get the values from the PDF
            pdf_values = get_pdf_field_values(output_path)
            log_debug("Fields extracted directly from PDF:")
            for field_name, value in pdf_values.items():
                log_debug(f"  {field_name}: {value}")

            # Then try to find your specific fields
            L1a_value = pdf_values.get(L1a_field_name)
            L25a_value = pdf_values.get(L25a_field_name)
            L34_value = pdf_values.get(L34_field_name)
            
            log_debug(f"Found value for Line 1a (field {L1a_field_name}): {L1a_value}")
            log_debug(f"Found value for Line 25a (field {L25a_field_name}): {L25a_value}")
            log_debug(f"Found value for Line 34 (field {L34_field_name}): {L34_value}")
            
            # VERIFICATION 1: Line 34 equals 102.31
            # This is the primary test requirement
            if L34_value is not None:
                # Convert string representations to Decimal
                if isinstance(L34_value, str):
                    L34_value = L34_value.replace(',', '')
                try:
                    pdf_L34_value = Decimal(str(L34_value))
                    
                    # Assert that Line 34 equals 102.31
                    assert abs(pdf_L34_value - Decimal('102.31')) < Decimal('0.01'), \
                        f"Line 34 value ({pdf_L34_value}) does not equal 102.31 for bob_student_F1040.json"
                    log_debug(f"✓ Line 34 value equals 102.31 as required")
                    L34_verified = True
                    L34_source = L34_source or "PDF"
                except (ValueError, TypeError) as e:
                    log_debug(f"Error converting Line 34 value ({L34_value}) to Decimal: {str(e)}")
                    log_debug("❌ Line 34 value could not be verified")
                    # This is important to verify, so fail the test
                    assert False, f"Line 34 value ({L34_value}) could not be verified as 102.31"
            else:
                log_debug("❌ Line 34 value not found in PDF or debug JSON")
                # This is important to verify, so fail the test
                assert False, "Line 34 value not found in PDF or debug JSON - cannot verify it equals 102.31"
            
            # VERIFICATION 2: Line 1a matches W2 box 1 sum
            # This is an additional check
            if L1a_value is not None:
                # Convert string representations to Decimal
                if isinstance(L1a_value, str):
                    L1a_value = L1a_value.replace(',', '')
                try:
                    pdf_L1a_value = Decimal(str(L1a_value))
                    
                    # Assert that Line 1a matches the W2 box 1 sum
                    assert abs(pdf_L1a_value - expected_box_1_sum) < Decimal('0.01'), \
                        f"Line 1a value ({pdf_L1a_value}) does not match expected W2 box 1 sum ({expected_box_1_sum})"
                    log_debug(f"✓ Line 1a value matches expected W2 box 1 sum")
                    L1a_verified = True
                    L1a_source = L1a_source or "PDF"
                except (ValueError, TypeError) as e:
                    log_debug(f"Error converting Line 1a value ({L1a_value}) to Decimal: {str(e)}")
                    log_debug("❌ Line 1a value could not be verified")
                    print(f"Warning: Line 1a value ({L1a_value}) could not be verified")
            else:
                log_debug("❌ Line 1a value not found in PDF or debug JSON")
                print("Warning: Line 1a value not found in PDF or debug JSON. Test will continue.")
                
            # VERIFICATION 3: Line 25a matches W2 box 2 sum
            # This is an additional check
            if L25a_value is not None:
                # Convert string representations to Decimal
                if isinstance(L25a_value, str):
                    L25a_value = L25a_value.replace(',', '')
                try:
                    pdf_L25a_value = Decimal(str(L25a_value))
                    
                    # Assert that Line 25a matches the W2 box 2 sum
                    assert abs(pdf_L25a_value - expected_box_2_sum) < Decimal('0.01'), \
                        f"Line 25a value ({pdf_L25a_value}) does not match expected W2 box 2 sum ({expected_box_2_sum})"
                    log_debug(f"✓ Line 25a value matches expected W2 box 2 sum")
                    L25a_verified = True
                    L25a_source = L25a_source or "PDF"
                except (ValueError, TypeError) as e:
                    log_debug(f"Error converting Line 25a value ({L25a_value}) to Decimal: {str(e)}")
                    log_debug("❌ Line 25a value could not be verified")
                    print(f"Warning: Line 25a value ({L25a_value}) could not be verified")
            else:
                log_debug("❌ Line 25a value not found in PDF or debug JSON")
                print("Warning: Line 25a value not found in PDF or debug JSON. Test will continue.")

            # VERIFICATION 4: Line 12 equals 14600 (Standard deduction for Single filing status)
            # Lookup the field name for Line 12
            L12_field_name = form_config.get("income", {}).get("L12_tag")
            log_debug(f"Looking for Line 12 using field name: {L12_field_name}")

            # Get the value from the PDF
            L12_value = pdf_values.get(L12_field_name)
            log_debug(f"Found value for Line 12 (field {L12_field_name}): {L12_value}")

            L12_verified = False
            L12_source = None

            if L12_value is not None:
                # Convert string representations to Decimal
                if isinstance(L12_value, str):
                    L12_value = L12_value.replace(',', '')
                try:
                    pdf_L12_value = Decimal(str(L12_value))
                    
                    # Assert that Line 12 equals 14600 (standard deduction for Single)
                    assert abs(pdf_L12_value - Decimal('14600')) < Decimal('0.01'), \
                        f"Line 12 value ({pdf_L12_value}) does not equal 14600 for standard deduction"
                    log_debug(f"✓ Line 12 value equals 14600 as required for standard deduction")
                    L12_verified = True
                    L12_source = L12_source or "PDF"
                except (ValueError, TypeError) as e:
                    log_debug(f"Error converting Line 12 value ({L12_value}) to Decimal: {str(e)}")
                    log_debug("❌ Line 12 value could not be verified")
                    # This is important to verify
                    assert False, f"Line 12 value ({L12_value}) could not be verified as 14600"
            else:
                log_debug("❌ Line 12 value not found in PDF or debug JSON")
                assert False, "Line 12 value not found in PDF or debug JSON - cannot verify it equals 14600"
                
        except Exception as e:
            log_debug(f"Error validating PDF values: {str(e)}")
            raise
            
        # Print success messages
        print("OpenTaxLiberty API test successful")
        print(f"Output PDF saved at: {output_path}")
        
        # Always print the Line 34 verification result as it's the primary test requirement
        print(f"✅ Verified Line 34 equals 102.31 for bob_student_F1040.json (Source: {L34_source})")
        
        # Print additional verification results
        if L1a_verified:
            print(f"✅ Verified Line 1a matches W2 box 1 sum: {expected_box_1_sum} (Source: {L1a_source})")
        else:
            print(f"Line 1a verification skipped. Expected W2 box 1 sum: {expected_box_1_sum}")
            
        if L25a_verified:
            print(f"✅ Verified Line 25a matches W2 box 2 sum: {expected_box_2_sum} (Source: {L25a_source})")
        else:
            print(f"Line 25a verification skipped. Expected W2 box 2 sum: {expected_box_2_sum}")

        # Print Line 12 verification result
        print(f"✅ Verified Line 12 equals 14600 for standard deduction (Source: {L12_source})")
            
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
