import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pypdf import PdfWriter

# Add the parent directory to sys.path so we can import opentaxliberty
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions we want to test
from opentaxliberty import process_input_json, find_key_in_json, write_field_pdf

class TestSumFunctionality:
    
    @pytest.fixture
    def mock_writer(self):
        """Create a mocked PdfWriter for testing."""
        mock = MagicMock(spec=PdfWriter)
        mock.pages = [MagicMock()]  # Mock a single page
        return mock
    
    def test_basic_sum(self, mock_writer):
        """Test basic summation functionality with a few values."""
        # Create test data with a sum operation
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 100,
                "value2": 200,
                "value3": 50,
                "sum_result": ["value1", "value2", "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # Verify the sum was calculated correctly (100 + 200 + 50 = 350)
        assert test_data["section1"]["sum_result"] == 350
        
        # Verify write_field_pdf was called with the correct values
        mock_writer.update_page_form_field_values.assert_called()
    
    def test_sum_with_one_value(self, mock_writer):
        """Test summation with just one value."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "single_value": 42,
                "sum_result": ["single_value"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # Verify the sum equals the single value (42)
        assert test_data["section1"]["sum_result"] == 42
    
    def test_sum_with_float_values(self, mock_writer):
        """Test summation with floating point values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 10.5,
                "value2": 20.75,
                "value3": 0.25,
                "sum_result": ["value1", "value2", "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # Verify the sum was calculated correctly (10.5 + 20.75 + 0.25 = 31.5)
        assert test_data["section1"]["sum_result"] == 31.5
    
    def test_sum_with_non_numeric_values(self, mock_writer):
        """Test how summation handles non-numeric values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "numeric_value": 100,
                "string_value": "not a number",
                "bool_value": True,
                "sum_result": ["numeric_value", "string_value", "bool_value"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Mock find_key_in_json to handle our test values
        def mock_find_key(data, key):
            if key == "numeric_value":
                return 100
            elif key == "string_value":
                return "not a number"  # Non-numeric
            elif key == "bool_value":
                return True # Boolean
            return None
        
        # Patch the find_key_in_json function
        with patch('opentaxliberty.find_key_in_json', side_effect=mock_find_key):
            with patch('opentaxliberty.write_field_pdf') as mock_write:
                # Process the test data
                process_input_json(test_data, mock_writer)
                
                # Since is_number() should filter out non-numeric values,
                # the sum should only include the numeric_value (100) + bool_value (1)
                assert test_data["section1"]["sum_result"] == 101
    
    def test_sum_across_sections(self, mock_writer):
        """Test summation of values from different sections."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 100
            },
            "section2": {
                "value2": 200
            },
            "results": {
                "sum_result": ["section1.value1", "section2.value2"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Mock find_key_in_json to handle cross-section references
        def mock_find_key(data, key):
            if key == "section1.value1":
                return 100
            elif key == "section2.value2":
                return 200
            return 0
        
        # Patch the find_key_in_json function
        with patch('opentaxliberty.find_key_in_json', side_effect=mock_find_key):
            with patch('opentaxliberty.write_field_pdf') as mock_write:
                # Process the test data
                process_input_json(test_data, mock_writer)
                
                # Verify the sum was calculated correctly (100 + 200 = 300)
                assert test_data["results"]["sum_result"] == 300
                mock_write.assert_any_call(mock_writer, "test_sum_field", 300)
    
    def test_sum_with_none_values(self, mock_writer):
        """Test how summation handles None values."""
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 50,
                "value2": None,
                "value3": 25,
                "sum_result": ["value1", "value2", "value3"],
                "sum_result_tag": "test_sum_field"
            }
        }
        
        # Mock find_key_in_json to handle None values
        def mock_find_key(data, key):
            if key == "value1":
                return 50
            elif key == "value2":
                return None
            elif key == "value3":
                return 25
            return 0
        
        # Patch the find_key_in_json function
        with patch('opentaxliberty.find_key_in_json', side_effect=mock_find_key):
            with patch('opentaxliberty.write_field_pdf') as mock_write:
                # Process the test data
                process_input_json(test_data, mock_writer)
                
                # None should be filtered out by is_number(), so sum should be 75
                assert test_data["section1"]["sum_result"] == 75
                mock_write.assert_any_call(mock_writer, "test_sum_field", 75)
    
    def test_real_tax_form_sum(self, mock_writer):
        """Test the summation functionality with data structured like real tax form data."""
        # This test data mimics the structure found in bob_student_example.json
        test_data = {
            "configuration": {"tax_year": 2024},
            "income": {
                "L1a": 6034.16,  # W-2 wages
                "L1b": 100,      # Household employee wages
                "L1c": 1,        # Tip income
                "L1z_sum": ["L1a", "L1b", "L1c"],
                "L1z_sum_tag": "f1_41[0]"
            }
        }
        
        # Mock find_key_in_json for tax form fields
        def mock_find_key(data, key):
            if key == "L1a":
                return 6034.16
            elif key == "L1b":
                return 100
            elif key == "L1c":
                return 1
            return 0
        
        # Patch the functions
        with patch('opentaxliberty.find_key_in_json', side_effect=mock_find_key):
            with patch('opentaxliberty.write_field_pdf') as mock_write:
                # Process the test data
                process_input_json(test_data, mock_writer)
                
                # Verify the sum is correct: 6034.16 + 100 + 1 = 6135.16
                assert test_data["income"]["L1z_sum"] == 6135.16
                mock_write.assert_any_call(mock_writer, "f1_41[0]", 6135.16)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
