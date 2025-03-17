# Test for F1040 Validation
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import json
import pytest
import tempfile
from decimal import Decimal
from pathlib import Path

# Add the parent directory to sys.path so we can import our module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the validator module
from F1040_validator import validate_F1040_file, F1040Document, F1040Configuration

class TestF1040Validation:
    """Test cases for F1040 configuration validation."""
    
    @pytest.fixture
    def valid_f1040_data(self):
        """Return a dictionary with valid F1040 data for testing."""
        return {
            "W2": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "W2"
                },
                "W2_entries": [
                    {"organization": "Data Entry Inc", "box_1": 550, "box_2": 0},
                    {"organization": "Fast Food", "box_1": 3907.57, "box_2": 54.31}
                ]
            },
            "F1040": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "F1040",
                    "output_file_name": "test_output.pdf",
                    "debug_json_output": "/workspace/temp/test_debug.json"
                },
                "name_address_ssn": {
                    "first_name_middle_initial": "John Q",
                    "first_name_middle_initial_tag": "f1_04[0]",
                    "last_name": "Taxpayer",
                    "last_name_tag": "f1_05[0]",
                    "ssn": "123      45      6789",
                    "ssn_tag": "f1_06[0]",
                    "home_address": "123 Main Street",
                    "home_address_tag": "f1_10[0]",
                    "city": "Anytown",
                    "city_tag": "f1_12[0]",
                    "state": "CA",
                    "state_tag": "f1_13[0]",
                    "zip": "12345",
                    "zip_tag": "f1_14[0]",
                    "presidential_you": "/1",
                    "presidential_you_tag": "c1_1[0]"
                },
                "filing_status": {
                    "single_or_HOH": "/1",
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/Off",
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off",
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "digital_assets": {
                    "value": "/2",
                    "tag": "c1_5[1]"
                },
                "standard_deduction": {
                    "you_as_a_dependent": "/Off",
                    "you_as_a_dependent_tag": "c1_6[0]",
                    "born_before_jan_2_1960": "/Off",
                    "born_before_jan_2_1960_tag": "c1_9[0]",
                    "are_blind": "/Off",
                    "are_blind_tag": "c1_10[0]"
                },
                "dependents": {
                    "check_if_more_than_4_dependents": "/Off",
                    "check_if_more_than_4_dependents_tag": "c1_13[0]",
                    "dependent_1_first_last_name": "Jane Taxpayer",
                    "dependent_1_first_last_name_tag": "f1_20[0]",
                    "dependent_1_ssn": "987      65      4321",
                    "dependent_1_ssn_tag": "f1_21[0]",
                    "dependent_1_relationship": "Daughter",
                    "dependent_1_relationship_tag": "f1_22[0]",
                    "dependent_1_child_tax_credit": "/1",
                    "dependent_1_child_tax_credit_tag": "c1_14[0]",
                    "dependent_1_credit_for_other_dependents": "/Off",
                    "dependent_1_credit_for_other_dependents_tag": "c1_15[0]"
                },
                "income": {
                    "L1a": "get_W2_box_1_sum()",
                    "L1a_tag": "f1_32[0]",
                    "L1b": 0,
                    "L1b_tag": "f1_33[0]",
                    "L1c": 0,
                    "L1c_tag": "f1_34[0]",
                    "L1z_sum": ["L1a", "L1b", "L1c"],
                    "L1z_sum_tag": "f1_41[0]",
                    "L2b": 100,
                    "L2b_tag": "f1_43[0]",
                    "L3b": 200,
                    "L3b_tag": "f1_45[0]",
                    "L4b": 0,
                    "L4b_tag": "f1_47[0]",
                    "L5b": 0,
                    "L5b_tag": "f1_49[0]",
                    "L6b": 0,
                    "L6b_tag": "f1_51[0]",
                    "L7": 0,
                    "L7_tag": "f1_52[0]",
                    "L8": 0,
                    "L8_tag": "f1_53[0]",
                    "L9_sum": ["L1z_sum", "L2b", "L3b", "L4b", "L5b", "L6b", "L7", "L8"],
                    "L9_sum_tag": "f1_54[0]",
                    "L10": 0,
                    "L10_tag": "f1_55[0]",
                    "L11_subtract": ["L9_sum", "L10"],
                    "L11_subtract_tag": "f1_56[0]",
                    "L12": 13850,
                    "L12_tag": "f1_57[0]",
                    "L13": 0,
                    "L13_tag": "f1_58[0]",
                    "L14_sum": ["L12", "L13"],
                    "L14_sum_tag": "f1_59[0]",
                    "L15_subtract": ["L11_subtract", "L14_sum"],
                    "L15_subtract_tag": "f1_60[0]"
                },
                "tax_and_credits": {
                    "L16_check_8814": "/Off",
                    "L16_check_8814_tag": "c2_1[0]",
                    "L16_check_4972": "/Off",
                    "L16_check_4972_tag": "c2_2[0]",
                    "L16_check_3": "/Off",
                    "L16_check_3_tag": "c2_3[0]",
                    "L16": 500,
                    "L16_tag": "f2_02[0]",
                    "L17": 0,
                    "L17_tag": "f2_03[0]",
                    "L18_sum": ["L16", "L17"],
                    "L18_sum_tag": "f2_04[0]",
                    "L19": 0,
                    "L19_tag": "f2_05[0]",
                    "L20": 0,
                    "L20_tag": "f2_06[0]",
                    "L21_sum": ["L19", "L20"],
                    "L21_sum_tag": "f2_07[0]",
                    "L22_subtract": ["L18_sum", "L21_sum"],
                    "L22_subtract_tag": "f2_08[0]",
                    "L23": 0,
                    "L23_tag": "f2_09[0]",
                    "L24_sum": ["L22_subtract", "L23"],
                    "L24_sum_tag": "f2_10[0]"
                },
                "payments": {
                    "L25a": "get_W2_box_2_sum()",
                    "L25a_tag": "f2_11[0]",
                    "L25b": 0,
                    "L25b_tag": "f2_12[0]",
                    "L25c": 0,
                    "L25c_tag": "f2_13[0]",
                    "L25d_sum": ["L25a", "L25b", "L25c"],
                    "L25d_sum_tag": "f2_14[0]",
                    "L26": 0,
                    "L26_tag": "f2_15[0]",
                    "L27": 0,
                    "L27_tag": "f2_16[0]",
                    "L28": 0,
                    "L28_tag": "f2_17[0]",
                    "L29": 0,
                    "L29_tag": "f2_18[0]",
                    "L31": 0,
                    "L31_tag": "f2_20[0]",
                    "L32_sum": ["L27", "L28", "L29", "L31"],
                    "L32_sum_tag": "f2_21[0]",
                    "L33_sum": ["L25d_sum", "L26", "L32_sum"],
                    "L33_sum_tag": "f2_22[0]"
                },
                "refund": {
                    "L34_subtract": ["L33_sum", "L24_sum"],
                    "L34_subtract_tag": "f2_23[0]",
                    "L35a_check": "/Off",
                    "L35a_check_tag": "c2_4[0]"
                },
                "amount_you_owe": {
                    "L37": 0,
                    "L37_tag": "f2_28[0]",
                    "L38": 0,
                    "L38_tag": "f2_29[0]"
                },
                "third_party_designee": {
                    "do_you_want_to_designate_yes": "/1",
                    "do_you_want_to_designate_yes_tag": "c2_6[0]",
                    "do_you_want_to_designate_no": "/Off",
                    "do_you_want_to_designate_no_tag": "c2_6[1]",
                    "desginee_name": "Tax Preparer",
                    "desginee_name_tag": "f2_30[0]",
                    "desginee_phone": "(555)123-4567",
                    "desginee_phone_tag": "f2_31[0]",
                    "desginee_pin": "12345",
                    "desginee_pin_tag": "f2_32[0]"
                },
                "sign_here": {
                    "your_occupation": "Engineer",
                    "your_occupation_tag": "f2_33[0]",
                    "your_pin": "98765",
                    "your_pin_tag": "f2_34[0]",
                    "phone_no": "(555)987-6543",
                    "phone_no_tag": "f2_37[0]",
                    "email": "john.taxpayer@example.com",
                    "email_tag": "f2_38[0]"
                }
            }
        }
    
    @pytest.fixture
    def temp_f1040_file(self, valid_f1040_data):
        """Create a temporary F1040 JSON file with valid data."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            json_str = json.dumps(valid_f1040_data, indent=2)
            tmp.write(json_str.encode())
            tmp_path = tmp.name
        
        # Debug: Read the file back and verify its contents
        try:
            with open(tmp_path, 'r') as f:
                file_content = f.read()
                print(f"Debug - File content read back: {file_content[:500]}...")  # First 500 chars for brevity
        except Exception as e:
            print(f"Error reading temp file: {e}")
        
        yield tmp_path
        
        # Clean up the file after the test
        os.unlink(tmp_path)
    
    def test_valid_f1040_file(self, temp_f1040_file):
        """Test validation of a valid F1040 file."""
        try:
            validated = validate_F1040_file(temp_f1040_file)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "F1040"
            assert validated.name_address_ssn.first_name_middle_initial == "John Q"
            assert validated.name_address_ssn.last_name == "Taxpayer"
            assert validated.filing_status.single_or_HOH == "/1"
            assert validated.digital_assets.value == "/2"
            assert validated.income.L2b == 100
            assert validated.tax_and_credits.L16 == 500
        except Exception as e:
            print(f"Full validation error: {str(e)}")
            raise
    
    def test_invalid_tax_year(self, valid_f1040_data):
        """Test validation fails with an invalid tax year."""
        valid_f1040_data["F1040"]["configuration"]["tax_year"] = 2030  # Future year
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Tax year" in str(excinfo.value)
    
    def test_invalid_form_type(self, valid_f1040_data):
        """Test validation fails with an incorrect form type."""
        valid_f1040_data["F1040"]["configuration"]["form"] = "1040"  # Missing 'F'
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Form type must be 'F1040'" in str(excinfo.value)
    
    def test_missing_required_field(self, valid_f1040_data):
        """Test validation fails when a required field is missing."""
        # Remove a required field
        del valid_f1040_data["F1040"]["name_address_ssn"]["first_name_middle_initial"]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "first_name_middle_initial" in str(excinfo.value)
    
    def test_multiple_filing_statuses(self, valid_f1040_data):
        """Test validation fails when multiple filing statuses are selected."""
        # Set multiple filing statuses to active
        valid_f1040_data["F1040"]["filing_status"]["single_or_HOH"] = "/1"
        valid_f1040_data["F1040"]["filing_status"]["married_filing_jointly_or_QSS"] = "/3"
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "filing status" in str(excinfo.value).lower()
    
    def test_no_filing_status(self, valid_f1040_data):
        """Test validation fails when no filing status is selected."""
        # Set all filing statuses to inactive
        valid_f1040_data["F1040"]["filing_status"]["single_or_HOH"] = "/Off"
        valid_f1040_data["F1040"]["filing_status"]["married_filing_jointly_or_QSS"] = "/Off"
        valid_f1040_data["F1040"]["filing_status"]["married_filing_separately"] = "/Off"
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Exactly one filing status must be selected" in str(excinfo.value)
    
    def test_invalid_checkbox_value(self, valid_f1040_data):
        """Test validation fails with an invalid checkbox value."""
        valid_f1040_data["F1040"]["digital_assets"]["value"] = "YES"  # Invalid value, should be /1 or /2
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Digital assets value must be" in str(excinfo.value)
    
    def test_invalid_payment_function(self, valid_f1040_data):
        """Test validation fails with an invalid payment function."""
        valid_f1040_data["F1040"]["payments"]["L25a"] = "get_wrong_function()"  # Invalid function
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "L25a must be a number or" in str(excinfo.value)
    
    def test_both_refund_and_amount_owed(self, valid_f1040_data):
        """Test validation handles having both refund and amount owed sections."""
        # Make both sections active with non-zero values
        valid_f1040_data["F1040"]["refund"]["L34_subtract"] = ["L33_sum", "L24_sum"]
        valid_f1040_data["F1040"]["amount_you_owe"]["L37"] = 500
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Cannot have both Refund and Amount You Owe" in str(excinfo.value)

    def test_direct_deposit_incomplete(self, valid_f1040_data):
            """Test validation fails when direct deposit information is incomplete."""
            # Add partial direct deposit info
            valid_f1040_data["F1040"]["refund"]["L35a_b"] = "123456789"  # Routing number
            # Missing account number and account type
            
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                tmp.write(json.dumps(valid_f1040_data).encode())
                tmp_path = tmp.name
            
            with pytest.raises(Exception) as excinfo:
                validate_F1040_file(tmp_path)
            
            os.unlink(tmp_path)
            assert "direct deposit information" in str(excinfo.value).lower()
        
    def test_designee_incomplete(self, valid_f1040_data):
        """Test validation fails when third-party designee information is incomplete."""
        # Set Yes for designee but remove required fields
        valid_f1040_data["F1040"]["third_party_designee"]["do_you_want_to_designate_yes"] = "/1"
        valid_f1040_data["F1040"]["third_party_designee"]["do_you_want_to_designate_no"] = "/Off"
        del valid_f1040_data["F1040"]["third_party_designee"]["desginee_name"]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "third party designee" in str(excinfo.value).lower()

    def test_dependent_incomplete(self, valid_f1040_data):
        """Test validation fails when dependent information is incomplete."""
        # Remove a required field for dependent 1
        valid_f1040_data["F1040"]["dependents"]["dependent_1_ssn"] = None
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "dependent_1_ssn must also be provided" in str(excinfo.value)

    def test_file_not_found(self):
        """Test validation raises an appropriate error when file doesn't exist."""
        with pytest.raises(ValueError) as excinfo:
            validate_F1040_file("nonexistent_file.json")
        
        assert "does not exist" in str(excinfo.value)

    def test_invalid_json(self):
        """Test validation fails with invalid JSON."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(b"{invalid json")
            tmp_path = tmp.name
        
        with pytest.raises(json.JSONDecodeError):
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)

    def test_missing_f1040_section(self):
        """Test validation fails when F1040 section is missing."""
        # Create data with only W2 section, missing F1040
        data = {
            "W2": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "W2"
                },
                "W2_entries": [
                    {"organization": "Data Entry Inc", "box_1": 550, "box_2": 0}
                ]
            }
            # No F1040 section
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "F1040" in str(excinfo.value)

    def test_no_refund_or_amount_owed(self, valid_f1040_data):
        """Test validation fails when neither refund nor amount owed sections are provided."""
        # Remove both sections
        valid_f1040_data["F1040"].pop("refund", None)
        valid_f1040_data["F1040"].pop("amount_you_owe", None)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_F1040_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Must have either Refund or Amount You Owe" in str(excinfo.value)

    def test_w2_box_1_sum_function(self, valid_f1040_data):
        """Test validation accepts the W2 box 1 sum function."""
        # Explicitly set the function for testing
        valid_f1040_data["F1040"]["income"]["L1a"] = "get_W2_box_1_sum()"
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        validated = validate_F1040_file(tmp_path)
        assert validated.income.L1a == "get_W2_box_1_sum()"
        
        os.unlink(tmp_path)

    def test_w2_box_2_sum_function(self, valid_f1040_data):
        """Test validation accepts the W2 box 2 sum function."""
        # Explicitly set the function for testing
        valid_f1040_data["F1040"]["payments"]["L25a"] = "get_W2_box_2_sum()"
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        validated = validate_F1040_file(tmp_path)
        assert validated.payments.L25a == "get_W2_box_2_sum()"
        
        os.unlink(tmp_path)

    def test_calculate_standard_deduction(self, valid_f1040_data):
        """Test automatic calculation of standard deduction based on filing status."""
        
        # Test cases for different filing statuses
        test_cases = [
            # Single filing status
            {
                "filing_status": {
                    "single_or_HOH": "/1", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/Off", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "expected_deduction": 14600
            },
            # Married filing separately
            {
                "filing_status": {
                    "single_or_HOH": "/Off", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/Off", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/1", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "expected_deduction": 14600
            },
            # Married filing jointly
            {
                "filing_status": {
                    "single_or_HOH": "/Off", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/3", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "expected_deduction": 29200
            },
            # Qualifying surviving spouse
            {
                "filing_status": {
                    "single_or_HOH": "/Off", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/4", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "expected_deduction": 29200
            },
            # Head of household
            {
                "filing_status": {
                    "single_or_HOH": "/2", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/Off", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "expected_deduction": 21900
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Create a deep copy of the valid data for this test case
            test_data = json.loads(json.dumps(valid_f1040_data))
            
            # Update the filing status fields
            for key, value in test_case["filing_status"].items():
                test_data["F1040"]["filing_status"][key] = value
            
            # Set L12 to 0 to ensure it gets calculated
            test_data["F1040"]["income"]["L12"] = 0
            
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                tmp.write(json.dumps(test_data).encode())
                tmp_path = tmp.name
            
            try:
                # Validate the file, which should trigger calculate_standard_deduction
                validated = validate_F1040_file(tmp_path)
                
                # Verify the standard deduction was calculated correctly
                assert validated.income.L12 == test_case["expected_deduction"], \
                    f"Test case {i+1}: Expected standard deduction of {test_case['expected_deduction']}, " \
                    f"got {validated.income.L12}"
                
            finally:
                os.unlink(tmp_path)

    def test_standard_deduction_not_overwritten(self, valid_f1040_data):
        """Test that existing standard deduction values are not overwritten."""
        
        # Set L12 to a non-zero value
        valid_f1040_data["F1040"]["income"]["L12"] = 14600
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_f1040_data).encode())
            tmp_path = tmp.name
        
        try:
            # Validate the file
            validated = validate_F1040_file(tmp_path)
            
            # Verify the standard deduction was not changed
            assert validated.income.L12 == 14600, \
                f"Expected standard deduction to remain 14600, but got {validated.income.L12}"
            
        finally:
            os.unlink(tmp_path)

    def test_real_config_file_structure(self):
        """Test validation with a file structure matching bob_student.json"""
        # Create data matching the bob_student.json structure
        data = {
            "W2": {
                "configuration": {
                    "_comment": "W2 is wage and tax statement, you should have one of these for each job that you work",
                    "_comment": "See README.md on why we use W2 and not W-2",
                    "_comment": "Under W2_entries it is possible to have no entries or multiple entries",
                    "tax_year": 2024,
                    "form": "W2"
                },
                "W2_entries": [
                    {"organization": "Data Entry Inc", "box_1": 550, "box_2": 0},
                    {"organization": "Fast Food", "box_1": 3907.57, "box_2": 54.31},
                    {"organization": "Mexican Buffet", "box_1": 1576.59, "box_2": 15.00}
                ]
            },
            "F1040": {
                "configuration": {
                    "tax_year": 2024,
                    "output_file_name": "bob_student_F1040.pdf",
                    "form": "F1040",
                    "debug_json_output": "/workspace/temp/bob_student_F1040.json"
                },
                "name_address_ssn": {
                    "first_name_middle_initial": "Bob S",
                    "first_name_middle_initial_tag": "f1_04[0]",
                    "last_name": "Example",
                    "last_name_tag": "f1_05[0]",
                    "ssn": "222        22        2222",
                    "ssn_tag": "f1_06[0]",
                    "home_address": "123 Main Street",
                    "home_address_tag": "f1_10[0]",
                    "city": "Anytown",
                    "city_tag": "f1_12[0]",
                    "state": "CA",
                    "state_tag": "f1_13[0]",
                    "zip": "12345",
                    "zip_tag": "f1_14[0]",
                    "presidential_you": "/Off",
                    "presidential_you_tag": "c1_1[0]"
                },
                "filing_status": {
                    "single_or_HOH": "/1", 
                    "single_or_HOH_tag": "c1_3[0]",
                    "married_filing_jointly_or_QSS": "/Off", 
                    "married_filing_jointly_or_QSS_tag": "c1_3[1]",
                    "married_filing_separately": "/Off", 
                    "married_filing_separately_tag": "c1_3[2]"
                },
                "digital_assets": {
                    "value": "/2",
                    "tag": "c1_5[1]"
                },
                # Minimal required fields for validation
                "standard_deduction": {
                    "you_as_a_dependent": "/Off",
                    "you_as_a_dependent_tag": "c1_6[0]",
                    "born_before_jan_2_1960": "/Off",
                    "born_before_jan_2_1960_tag": "c1_9[0]",
                    "are_blind": "/Off",
                    "are_blind_tag": "c1_10[0]"
                },
                "income": {
                    "L1a": "get_W2_box_1_sum()",
                    "L1a_tag": "f1_32[0]",
                    "L1z_sum": ["L1a"],
                    "L1z_sum_tag": "f1_41[0]",
                    "L9_sum": ["L1z_sum"],
                    "L9_sum_tag": "f1_54[0]",
                    "L11_subtract": ["L9_sum"],
                    "L11_subtract_tag": "f1_56[0]",
                    "L12": 14600,
                    "L12_tag": "f1_57[0]",
                    "L14_sum": ["L12"],
                    "L14_sum_tag": "f1_59[0]",
                    "L15_subtract": ["L11_subtract", "L14_sum"],
                    "L15_subtract_tag": "f1_60[0]"
                },
                "tax_and_credits": {
                    "L16": 0,
                    "L16_tag": "f2_02[0]",
                    "L18_sum": ["L16"],
                    "L18_sum_tag": "f2_04[0]",
                    "L21_sum": [],
                    "L21_sum_tag": "f2_07[0]",
                    "L22_subtract": ["L18_sum", "L21_sum"],
                    "L22_subtract_tag": "f2_08[0]",
                    "L24_sum": ["L22_subtract"],
                    "L24_sum_tag": "f2_10[0]"
                },
                "payments": {
                    "L25a": "get_W2_box_2_sum()",
                    "L25a_tag": "f2_11[0]",
                    "L25d_sum": ["L25a"],
                    "L25d_sum_tag": "f2_14[0]",
                    "L32_sum": [],
                    "L32_sum_tag": "f2_21[0]",
                    "L33_sum": ["L25d_sum", "L32_sum"],
                    "L33_sum_tag": "f2_22[0]"
                },
                "refund": {
                    "L34_subtract": ["L33_sum", "L24_sum"],
                    "L34_subtract_tag": "f2_23[0]"
                },
                "sign_here": {
                    "your_occupation": "Engineer",
                    "your_occupation_tag": "f2_33[0]",
                    "phone_no": "(555)987-6543",
                    "phone_no_tag": "f2_37[0]"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        try:
            validated = validate_F1040_file(tmp_path)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "F1040"
            assert validated.name_address_ssn.first_name_middle_initial == "Bob S"
            assert validated.filing_status.single_or_HOH == "/1"
            
            # Check that income fields reflect the new structure
            assert validated.income.L1a == "get_W2_box_1_sum()"
            assert validated.payments.L25a == "get_W2_box_2_sum()"
            
            print("✅ Real config file structure validation passed successfully")
        except Exception as e:
            print(f"Real config file structure validation error: {str(e)}")
            raise
        finally:
            os.unlink(tmp_path)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 
