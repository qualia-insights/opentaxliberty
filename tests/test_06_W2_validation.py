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
            "configuration": {
                "tax_year": 2024,
                "form": "W2"
            },
            "W2": [
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
        #os.unlink(tmp_path)
    
    def test_valid_w2_file(self, temp_w2_file):
        """Test validation of a valid W2 file."""
        try:
            validated = validate_W2_file(temp_w2_file)
            
            # Check that the document was parsed correctly
            assert validated.configuration.tax_year == 2024
            assert validated.configuration.form == "W2"
            assert len(validated.W2) == 2
            assert validated.W2[0].organization == "Data Entry Inc"
            assert validated.W2[0].box_1 == Decimal('550')
            assert validated.W2[1].organization == "Fast Food"
            assert validated.W2[1].box_2 == Decimal('54.31')
            
            # Check that totals were calculated correctly
            assert validated.totals["total_box_1"] == Decimal('4457.57')
            assert validated.totals["total_box_2"] == Decimal('54.31')
        except Exception as e:
            print(f"Full validation error: {str(e)}")
            raise
    
    def test_invalid_tax_year(self, valid_w2_data):
        """Test validation fails with an invalid tax year."""
        valid_w2_data["configuration"]["tax_year"] = 2030  # Future year
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "Tax year" in str(excinfo.value)
    
    def test_invalid_form_type(self, valid_w2_data):
        """Test validation fails with an incorrect form type."""
        valid_w2_data["configuration"]["form"] = "W-2"  # Added hyphen
        
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
        del valid_w2_data["W2"][0]["box_1"]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(valid_w2_data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "box_1" in str(excinfo.value)
    
    def test_negative_values(self, valid_w2_data):
        """Test validation fails when box values are negative."""
        valid_w2_data["W2"][0]["box_2"] = -10  # Negative value not allowed
        
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
        valid_w2_data["W2"][0].update({
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
        assert validated.W2[0].box_3 == Decimal('550')
        assert validated.W2[0].box_4 == Decimal('34.10')
        assert validated.W2[0].box_12a_code == "D"
        assert validated.W2[0].box_12a_amount == Decimal('100')
        assert validated.W2[0].box_13_retirement_plan is True
        
        # Check that optional field totals were calculated
        assert validated.totals["total_box_3"] == Decimal('550')
        assert validated.totals["total_box_4"] == Decimal('34.10')
    
    def test_invalid_box_12_code(self, valid_w2_data):
        """Test validation fails with an invalid box 12 code."""
        valid_w2_data["W2"][0]["box_12a_code"] = "X"  # Invalid code
        valid_w2_data["W2"][0]["box_12a_amount"] = 100
        
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
        
    def test_empty_w2_list(self):
        """Test validation fails when no W2 entries are provided."""
        data = {
            "configuration": {
                "tax_year": 2024,
                "form": "W2"
            },
            "W2": []  # Empty list - should fail validation
        }
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp.write(json.dumps(data).encode())
            tmp_path = tmp.name
        
        with pytest.raises(Exception) as excinfo:
            validate_W2_file(tmp_path)
        
        os.unlink(tmp_path)
        assert "List should have at least 1 item after validation, not 0" in str(excinfo.value) 

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
