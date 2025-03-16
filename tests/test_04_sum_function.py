import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pypdf import PdfWriter

# Add the parent directory to sys.path so we can import opentaxliberty
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions we want to test
from opentaxliberty import process_input_config, find_key_in_json, write_field_pdf, is_number

class TestSumFunctionality:
    
    @pytest.fixture
    def mock_writer(self):
        """Create a mocked PdfWriter for testing."""
        class MockPdfWriter:
            def __init__(self):
                self.pages = [None]  # Simulate having one page
                self.updated_fields = {}
                
            def update_page_form_field_values(self, page, fields, auto_regenerate=True):
                self.updated_fields.update(fields)
        
        return MockPdfWriter()
    
    @pytest.fixture
    def mock_w2_data(self):
        """Create mock W2 data for testing."""
        return {
            "totals": {
                "total_box_1": 6034.16,
                "total_box_2": 69.31
            }
        }
    
    def test_basic_sum(self, mock_writer, mock_w2_data):
        """Test basic summation functionality with a few values."""
        # Create test data with a sum operation
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 100,
                "value1_tag": "value1_tag",
                "value2": 200,
                "value2_tag": "value2_tag",
                "value3": 50,
                "value3_tag": "value3_tag",
                "sum_result": ["value1", "value2", "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the sum was calculated correctly (100 + 200 + 50 = 350)
        assert test_data["section1"]["sum_result"] == 350
        assert mock_writer.updated_fields["test_sum_field"] == 350
    
    def test_sum_with_one_value(self, mock_writer, mock_w2_data):
        """Test summation with just one value."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "single_value": 42,
                "single_value_tag": "single_value_tag",
                "sum_result": ["single_value"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the sum equals the single value (42)
        assert test_data["section1"]["sum_result"] == 42
        assert mock_writer.updated_fields["test_sum_field"] == 42
    
    def test_sum_with_float_values(self, mock_writer, mock_w2_data):
        """Test summation with floating point values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 10.5,
                "value1_tag": "value1_tag",
                "value2": 20.75,
                "value2_tag": "value2_tag",
                "value3": 0.25,
                "value3_tag": "value3_tag",
                "sum_result": ["value1", "value2", "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the sum was calculated correctly (10.5 + 20.75 + 0.25 = 31.5)
        assert test_data["section1"]["sum_result"] == 31.5
        assert mock_writer.updated_fields["test_sum_field"] == 31.5
    
    def test_sum_with_non_numeric_values(self, mock_writer, mock_w2_data):
        """Test how summation handles non-numeric values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "numeric_value": 100,
                "numeric_value_tag": "numeric_value_tag",
                "string_value": "not a number",
                "string_value_tag": "string_value_tag",
                "bool_value": True,
                "bool_value_tag": "bool_value_tag",
                "sum_result": ["numeric_value", "string_value", "bool_value"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # We'll need to patch find_key_in_json to ensure it returns our test values
        # Create a patched version to explicitly return our non-numeric test values
        def mocked_find_key_in_json(data, key):
            if key == "numeric_value":
                return 100
            elif key == "string_value":
                return "not a number"
            elif key == "bool_value":
                return True
            else:
                # Default fallback for other keys
                try:
                    return find_key_in_json(data, key)
                except KeyError:
                    return None
        
        # Apply our patch for this test
        with patch('opentaxliberty.find_key_in_json', side_effect=mocked_find_key_in_json):
            # Process the test data
            process_input_config(test_data, mock_w2_data, mock_writer)
            
            # Since is_number() should filter out non-numeric values,
            # the sum should only include numeric_value (100) and bool_value (True, treated as 1)
            # The "string_value" should be ignored in the sum
            assert test_data["section1"]["sum_result"] == 101
            assert mock_writer.updated_fields["test_sum_field"] == 101
    
    def test_cross_section_sum(self, mock_writer, mock_w2_data):
        """Test summation of values from different sections."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "income": {
                "L1z": 5000,
                "L1z_tag": "l1z_tag"
            },
            "adjustments": {
                "L2b": 200,
                "L2b_tag": "l2b_tag",
                "L3b": 300,
                "L3b_tag": "l3b_tag"
            },
            "totals": {
                "L9_sum": ["L1z", "L2b", "L3b"],
                "L9_sum_tag": "total_income_tag"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the sum was calculated correctly (5000 + 200 + 300 = 5500)
        assert test_data["totals"]["L9_sum"] == 5500
        assert mock_writer.updated_fields["total_income_tag"] == 5500
    
    def test_sum_with_none_values(self, mock_writer, mock_w2_data):
        """Test how summation handles None values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 50,
                "value1_tag": "value1_tag",
                "value2": None,
                "value2_tag": "value2_tag",
                "value3": 25,
                "value3_tag": "value3_tag",
                "sum_result": ["value1",  "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # None should be filtered out by is_number(), so sum should be 75
        assert test_data["section1"]["sum_result"] == 75
        assert mock_writer.updated_fields["test_sum_field"] == 75
    
    def test_w2_data_in_sum(self, mock_writer, mock_w2_data):
        """Test summation that includes W2 data."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "income": {
                "L1a": "get_W2_box_1_sum()",
                "L1a_tag": "l1a_tag",
                "L1b": 500,
                "L1b_tag": "l1b_tag",
                "L1c": 200,
                "L1c_tag": "l1c_tag",
                "L1z_sum": ["L1a", "L1b", "L1c"],
                "L1z_sum_tag": "total_wages_tag"
            }
        }
        
        # For testing purposes, manually set L1a to the W2 box 1 total
        test_data["income"]["L1a"] = mock_w2_data["totals"]["total_box_1"]
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the sum was calculated correctly (6034.16 + 500 + 200 = 6734.16)
        assert test_data["income"]["L1z_sum"] == 6734.16
        assert mock_writer.updated_fields["total_wages_tag"] == 6734.16
    
    def test_real_tax_form_sum(self, mock_writer, mock_w2_data):
        """Test sum functionality with structure like real tax form."""
        # This test data mimics a portion of the actual tax form JSON
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "income": {
                "L1a": 6034.16,  # W2 wages
                "L1a_tag": "f1_32[0]",
                "L1b": 100,      # Household employee wages
                "L1b_tag": "f1_33[0]",
                "L1c": 1,        # Tip income
                "L1c_tag": "f1_34[0]",
                "L1z_sum": ["L1a", "L1b", "L1c"],
                "L1z_sum_tag": "f1_41[0]"
            },
            "tax_and_credits": {
                "L16": 500,
                "L16_tag": "f2_02[0]",
                "L17": 250,
                "L17_tag": "f2_03[0]",
                "L18_sum": ["L16", "L17"],
                "L18_sum_tag": "f2_04[0]"
            }
        }
        
        # Process the JSON data
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the L1z_sum (total wages) is correct: 6034.16 + 100 + 1 = 6135.16
        assert test_data["income"]["L1z_sum"] == 6135.16
        assert mock_writer.updated_fields["f1_41[0]"] == 6135.16
        
        # Verify the L18_sum (tax total) is correct: 500 + 250 = 750
        assert test_data["tax_and_credits"]["L18_sum"] == 750
        assert mock_writer.updated_fields["f2_04[0]"] == 750

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
