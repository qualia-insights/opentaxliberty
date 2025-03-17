# Test for W2 Validation
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
from W2_validator import validate_W2_file, W2Document, W2Entry, W2Configuration

class TestW2Validation:
    """Test cases for W2 configuration validation."""
    
    @pytest.fixture
    def valid_w2_data(self):
        """Return a dictionary with valid W2 data for testing."""
        return {
            "W2": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "W2"
                },
                "W2_entries": [
                    {
                        "organization": "Data Entry Inc",
                        "box_1": 550,
                        "box_2": 0
                    },
                    {
                        "organization": "Fast Food",
                        "box_1": 3907.57,
                        "box_2": 54.31
                    }
                ]
            },
            "F1040": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "F1040",
                    "output_file_name": "test_output.pdf"
                }
            }
        }
    
    @pytest.fixture
    def valid_empty_w2_data(self):
        """Return a dictionary with valid W2 data but no entries."""
        return {
            "W2": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "W2"
                },
                "W2_entries": []
            },
            "F1040": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "F1040",
                    "output_file_name": "test_output.pdf"
                }
            }
        }
    
    @pytest.fixture
    def temp_w2_file(self, valid_w2_data):
        """Create a temporary W2 JSON file with valid data."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Debug: Print the JSON being written to the file
            json_str = json.dumps(valid_w2_data)
            print(f"Debug - JSON being written to temp file: {json_str}")
            
            tmp.write(json_str.encode())
            tmp_path = tmp.name
        
        # Debug: Read the file back and verify its contents
        try:
            with open(tmp_path, 'r') as f:
                file_content = f.read()
                print(f"Debug - File content read back: {file_content}")
        except Exception as e:
            print(f"Error reading temp file: {e}")
        
        yield tmp_path
        
        # Clean up the file after the test
        os.unlink(tmp_path)
    
    @pytest.fixture
    def temp_empty_w2_file(self, valid_empty_w2_data):
        """Create a temporary W2 JSON file with no entries."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            # Write the JSON with empty W2 array
            json_str = json.dumps(valid_empty_w2_data)
            print(f"Debug - Empty W2 JSON being written to temp file: {json_str}")
            
            tmp.write(json_str.encode())
            tmp_path = tmp.name
        
        yield tmp_path
        
        # Clean up the file after the test
        os.unlink(tmp_path)
    
    def test_valid_w2_file(self, temp_w2_file):
        """Test validation of a valid W2 file."""
        try:
            validated = validate_W2_file(temp_w2_file)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "W2"
            assert len(validated.W2_entries) == 2
            assert validated.W2_entries[0].organization == "Data Entry Inc"
            assert validated.W2_entries[0].box_1 == Decimal('550')
            assert validated.W2_entries[1].organization == "Fast Food"
            assert validated.W2_entries[1].box_2 == Decimal('54.31')
            
            # Check that totals were calculated correctly
            assert validated.totals["total_box_1"] == Decimal('4457.57')
            assert validated.totals["total_box_2"] == Decimal('54.31')
        except Exception as e:
            print(f"Full validation error: {str(e)}")
            raise
    
    def test_empty_w2_list(self, temp_empty_w2_file):
        """Test validation succeeds with an empty W2 list."""
        try:
            validated = validate_W2_file(temp_empty_w2_file)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "W2"
            assert len(validated.W2_entries) == 0
            
            # Check that totals were calculated as zeros
            assert validated.totals["total_box_1"] == Decimal('0')
            assert validated.totals["total_box_2"] == Decimal('0')
            
            # Check that optional totals are also zero
            assert validated.totals["total_box_3"] == Decimal('0')
            assert validated.totals["total_box_4"] == Decimal('0')
            
            print("✅ Empty W2 list validation passed successfully")
        except Exception as e:
            print(f"Empty W2 list validation error: {str(e)}")
            raise
    
    def test_w2_data_without_w2_entries_key(self):
        """Test validation handles missing W2_entries key by creating an empty list."""
        # Create data without the W2_entries key
        data = {
            "W2": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "W2"
                }
                # No W2_entries key
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        try:
            validated = validate_W2_file(tmp_path)
            
            # Check that an empty W2 list was created
            assert len(validated.W2_entries) == 0
            
            # Check that totals were calculated as zeros
            assert validated.totals["total_box_1"] == Decimal('0')
            assert validated.totals["total_box_2"] == Decimal('0')
            
            print("✅ Missing W2_entries key validation passed successfully")
        except Exception as e:
            print(f"Missing W2_entries key validation error: {str(e)}")
            raise
        finally:
            os.unlink(tmp_path)
    
    def test_missing_w2_section(self):
        """Test validation fails when W2 section is completely missing."""
        # Create data without the W2 section
        data = {
            "F1040": {
                "configuration": {
                    "tax_year": 2024,
                    "form": "F1040",
                    "output_file_name": "test_output.pdf"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "W2" in str(excinfo.value)
    
    def test_invalid_tax_year(self, valid_w2_data):
        """Test validation fails with an invalid tax year."""
        valid_w2_data["W2"]["configuration"]["tax_year"] = 2030  # Future year
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Tax year" in str(excinfo.value)
    
    def test_invalid_form_type(self, valid_w2_data):
        """Test validation fails with an incorrect form type."""
        valid_w2_data["W2"]["configuration"]["form"] = "W-2"  # Added hyphen
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Form type must be 'W2'" in str(excinfo.value)
    
    def test_missing_required_field(self, valid_w2_data):
        """Test validation fails when a required field is missing."""
        # Remove the box_1 field from the first W2 entry
        del valid_w2_data["W2"]["W2_entries"][0]["box_1"]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "box_1" in str(excinfo.value)
    
    def test_negative_values(self, valid_w2_data):
        """Test validation fails when box values are negative."""
        valid_w2_data["W2"]["W2_entries"][0]["box_2"] = -10  # Negative value not allowed
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "ge=" in str(excinfo.value) or "greater than or equal to 0" in str(excinfo.value)
    
    def test_with_optional_fields(self, valid_w2_data):
        """Test validation succeeds with optional fields included."""
        # Add optional fields to the first W2 entry
        valid_w2_data["W2"]["W2_entries"][0].update({
            "box_3": 550,
            "box_4": 34.10,
            "box_12a_code": "D",
            "box_12a_amount": 100,
            "box_13_retirement_plan": True
        })
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        validated = validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        
        # Check that optional fields were parsed correctly
        assert validated.W2_entries[0].box_3 == Decimal('550')
        assert validated.W2_entries[0].box_4 == Decimal('34.10')
        assert validated.W2_entries[0].box_12a_code == "D"
        assert validated.W2_entries[0].box_12a_amount == Decimal('100')
        assert validated.W2_entries[0].box_13_retirement_plan is True
        
        # Check that optional field totals were calculated
        assert validated.totals["total_box_3"] == Decimal('550')
        assert validated.totals["total_box_4"] == Decimal('34.10')
    
    def test_invalid_box_12_code(self, valid_w2_data):
        """Test validation fails with an invalid box 12 code."""
        valid_w2_data["W2"]["W2_entries"][0]["box_12a_code"] = "X"  # Invalid code
        valid_w2_data["W2"]["W2_entries"][0]["box_12a_amount"] = 100
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Invalid box 12 code" in str(excinfo.value)
    
    def test_file_not_found(self):
        """Test validation raises an appropriate error when file doesn't exist."""
        with pytest.raises(ValueError) as excinfo:
            validate_W2_file("nonexistent_file.json")
        
        assert "does not exist" in str(excinfo.value)
    
    def test_invalid_json(self):
        """Test validation fails with invalid JSON."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(b"{invalid json")
            tmp_path = tmp.name
        
        with pytest.raises(json.JSONDecodeError):
            validate_W2_file(tmp_path)
        
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
                }
                # Truncated for brevity...
            }
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        try:
            validated = validate_W2_file(tmp_path)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "W2"
            assert len(validated.W2_entries) == 3
            
            # Check specific entries
            assert validated.W2_entries[0].organization == "Data Entry Inc"
            assert validated.W2_entries[1].organization == "Fast Food"
            assert validated.W2_entries[2].organization == "Mexican Buffet"
            
            # Check that totals were calculated correctly
            expected_total_box_1 = Decimal('550') + Decimal('3907.57') + Decimal('1576.59')
            expected_total_box_2 = Decimal('0') + Decimal('54.31') + Decimal('15.00')
            
            assert validated.totals["total_box_1"] == expected_total_box_1
            assert validated.totals["total_box_2"] == expected_total_box_2
            
            print("✅ Real config file structure validation passed successfully")
        except Exception as e:
            print(f"Real config file structure validation error: {str(e)}")
            raise
        finally:
            os.unlink(tmp_path)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
