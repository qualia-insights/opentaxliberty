import pytest
import subprocess
import os
import json
from pathlib import Path
import time
from decimal import Decimal

def test_F1040sc_execution():
    """
    Test execution of F1040sc.py script with the bob_student_big.json configuration file.
    
    This test verifies:
    1. The script executes successfully
    2. The output PDF file is created
    3. The debug JSON file is created and contains expected values
    4. The script correctly calculates profit/loss and expense totals
    """
    # Define paths
    config_file = "../bob_student.json"
    template_file = "/workspace/code/taxes/2024/f1040sc_blank.pdf"
    output_file = "/workspace/temp/f1040sc.pdf"
    debug_json_file = "/workspace/temp/bob_student_schedule_c_debug.json"
    
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
        
        # Execute the F1040sc.py script
        command = [
            "python3", "../F1040sc.py",
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
        # Business name
        assert debug_data["business_information"]["business_name"] == "Bob S Example", \
            f"Incorrect business name in debug JSON: {debug_data['business_information']['business_name']}"
        
        # Net profit (Line 31)
        expected_net_profit = 19830.00
        actual_net_profit = float(debug_data["net_profit_loss"]["L31"])
        assert abs(actual_net_profit - expected_net_profit) < 0.01, \
            f"Net profit calculation incorrect. Expected: {expected_net_profit}, Got: {actual_net_profit}"
        
        # Total expenses (Line 28)
        expected_expenses = 21570.00
        actual_expenses = float(debug_data["expenses"]["L28"])
        assert abs(actual_expenses - expected_expenses) < 0.01, \
            f"Total expenses calculation incorrect. Expected: {expected_expenses}, Got: {actual_expenses}"
        
        # Other expenses total (Line 48)
        expected_other_expenses = 3150.00
        actual_other_expenses = float(debug_data["other_expenses"]["L48"])
        assert abs(actual_other_expenses - expected_other_expenses) < 0.01, \
            f"Other expenses total incorrect. Expected: {expected_other_expenses}, Got: {actual_other_expenses}"
        
        # Gross income (Line 7)
        expected_gross_income = 42900.00
        actual_gross_income = float(debug_data["income"]["L7"])
        assert abs(actual_gross_income - expected_gross_income) < 0.01, \
            f"Gross income calculation incorrect. Expected: {expected_gross_income}, Got: {actual_gross_income}"
        
        # Verify home office deduction (Line 30)
        expected_home_office = 1500.00
        actual_home_office = float(debug_data["home_office"]["L30"])
        assert abs(actual_home_office - expected_home_office) < 0.01, \
            f"Home office deduction incorrect. Expected: {expected_home_office}, Got: {actual_home_office}"
        
        print("✅ F1040sc.py executed successfully")
        print(f"✅ Output PDF created at: {output_file}")
        print(f"✅ Debug JSON file created at: {debug_json_file}")
        print(f"✅ Business name verified: {debug_data['business_information']['business_name']}")
        print(f"✅ Gross income verified: {actual_gross_income}")
        print(f"✅ Total expenses verified: {actual_expenses}")
        print(f"✅ Other expenses total verified: {actual_other_expenses}")
        print(f"✅ Home office deduction verified: {actual_home_office}")
        print(f"✅ Net profit verified: {actual_net_profit}")
        
    except Exception as e:
        # Print all debug logs if the test fails
        print("\n--- DEBUG INFORMATION ---")
        for log in debug_logs:
            print(log)
        print("\n--- END DEBUG INFORMATION ---")
        
        raise

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
