import pytest
import subprocess
import os
import json
from pathlib import Path
import time
from decimal import Decimal

def test_F1040_execution():
    """
    Test execution of F1040.py script with the bob_student.json configuration file.
    
    This test verifies:
    1. The script executes successfully
    2. The output PDF file is created
    3. The debug JSON file is created and contains expected values
    4. The script correctly calculates income, tax, and refund amounts
    """
    # Define paths
    config_file = "../bob_student.json"
    template_file = "/workspace/code/taxes/2024/f1040_blank.pdf"
    output_file = "/workspace/temp/f1040.pdf"
    debug_json_file = "/workspace/temp/bob_student.json"
    
    # Save debug information
    debug_logs = []
    def log_debug(message):
        debug_logs.append(message)
    
    try:
        # Verify the config file exists
        config_path = Path(config_file)
        log_debug(f"Config file exists: {config_path.exists()} at {config_path}")
        assert config_path.exists(), f"Config file {config_file} does not exist"
        
        # Verify the template file exists
        template_path = Path(template_file)
        log_debug(f"Template file exists: {template_path.exists()} at {template_path}")
        assert template_path.exists(), f"Template file {template_file} does not exist"
        
        # Create output directory if it doesn't exist
        output_dir = Path(output_file).parent
        os.makedirs(output_dir, exist_ok=True)
        
        # Delete output files if they already exist
        for file_path in [output_file, debug_json_file]:
            if Path(file_path).exists():
                Path(file_path).unlink()
                log_debug(f"Deleted existing file: {file_path}")
        
        # Execute the F1040.py script
        command = [
            "python3", "../F1040.py",
            "--config", config_file,
            "--template", template_file,
            "--output", output_file,
            "--verbose"
        ]
        
        log_debug(f"Executing command: {' '.join(command)}")
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Store command results
        log_debug(f"Command exit code: {result.returncode}")
        log_debug(f"Command stdout: {result.stdout}")
        log_debug(f"Command stderr: {result.stderr}")
        
        # Check for successful execution
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Check that the output file was created
        output_path = Path(output_file)
        log_debug(f"Output file exists: {output_path.exists()} at {output_path}")
        assert output_path.exists(), f"Output file {output_file} was not created"
        
        # Check that the output file has a reasonable size (not empty)
        output_size = output_path.stat().st_size
        log_debug(f"Output file size: {output_size} bytes")
        assert output_size > 1000, f"Output file {output_file} is too small ({output_size} bytes)"
        
        # Check that the debug JSON file was created
        debug_json_path = Path(debug_json_file)
        log_debug(f"Debug JSON file exists: {debug_json_path.exists()} at {debug_json_path}")
        assert debug_json_path.exists(), f"Debug JSON file {debug_json_file} was not created"
        
        # Verify the content of the debug JSON file
        with open(debug_json_file, 'r') as f:
            debug_data = json.load(f)
        
        # Check key fields and calculations
        # Personal information
        assert debug_data["name_address_ssn"]["first_name_middle_initial"] == "Bob S", \
            f"Incorrect first name in debug JSON: {debug_data['name_address_ssn']['first_name_middle_initial']}"
        
        assert debug_data["name_address_ssn"]["last_name"] == "Example", \
            f"Incorrect last name in debug JSON: {debug_data['name_address_ssn']['last_name']}"
        
        # Verify filing status
        assert debug_data["filing_status"]["single_or_HOH"] == "/1", \
            f"Incorrect filing status in debug JSON: {debug_data['filing_status']['single_or_HOH']}"
        
        # Verify W2 wages (Line 1a)
        expected_w2_sum = 6034.16
        actual_w2_sum = float(debug_data["income"]["L1a"])
        assert abs(actual_w2_sum - expected_w2_sum) < 0.01, \
            f"W2 sum calculation incorrect. Expected: {expected_w2_sum}, Got: {actual_w2_sum}"
        
        # Verify standard deduction (Line 12)
        expected_standard_deduction = 14600
        actual_standard_deduction = float(debug_data["income"]["L12"])
        assert abs(actual_standard_deduction - expected_standard_deduction) < 0.01, \
            f"Standard deduction incorrect. Expected: {expected_standard_deduction}, Got: {actual_standard_deduction}"
        
        # Verify total income (Line 9)
        #expected_total_income = 6168.16  # W2 wages plus other income items
        expected_total_income = 6397.16
        actual_total_income = float(debug_data["income"]["L9"])
        assert abs(actual_total_income - expected_total_income) < 0.01, \
            f"Total income calculation incorrect. Expected: {expected_total_income}, Got: {actual_total_income}"
        
        # Verify adjusted gross income (Line 11)
        expected_agi = 6384.16  # Total income minus adjustments
        actual_agi = float(debug_data["income"]["L11"])
        assert abs(actual_agi - expected_agi) < 0.01, \
            f"Adjusted gross income calculation incorrect. Expected: {expected_agi}, Got: {actual_agi}"
        
        # Verify total payments (Line 33)
        expected_payments = 102.31  # W2 withholdings plus other payments
        actual_payments = float(debug_data["payments"]["L33"])
        assert abs(actual_payments - expected_payments) < 0.01, \
            f"Total payments calculation incorrect. Expected: {expected_payments}, Got: {actual_payments}"
        
        # Verify refund amount (Line 34)
        expected_refund = 102.31  # No tax due, so refund equals total payments
        actual_refund = float(debug_data["refund"]["L34"])
        assert abs(actual_refund - expected_refund) < 0.01, \
            f"Refund calculation incorrect. Expected: {expected_refund}, Got: {actual_refund}"
        
        print("✅ F1040.py executed successfully")
        print(f"✅ Output PDF created at: {output_file}")
        print(f"✅ Debug JSON file created at: {debug_json_file}")
        print(f"✅ Taxpayer name verified: {debug_data['name_address_ssn']['first_name_middle_initial']} {debug_data['name_address_ssn']['last_name']}")
        print(f"✅ W2 wages verified: {actual_w2_sum}")
        print(f"✅ Standard deduction verified: {actual_standard_deduction}")
        print(f"✅ Total income verified: {actual_total_income}")
        print(f"✅ Adjusted gross income verified: {actual_agi}")
        print(f"✅ Total payments verified: {actual_payments}")
        print(f"✅ Refund amount verified: {actual_refund}")
        
    except Exception as e:
        # Print all debug logs if the test fails
        print("\n--- DEBUG INFORMATION ---")
        for log in debug_logs:
            print(log)
        print("\n--- END DEBUG INFORMATION ---")
        
        raise

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
