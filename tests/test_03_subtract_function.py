import os
import sys
import json
import pytest
from pathlib import Path
import tempfile
from pypdf import PdfReader, PdfWriter

# Add the parent directory to sys.path so we can import opentaxliberty
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions we want to test
from opentaxliberty import process_input_json, find_key_in_json, write_field_pdf

class TestSubtractFunctionality:
    
    @pytest.fixture
    def sample_pdf(self):
        """Create a temporary PDF file for testing."""
        # This is a minimal placeholder - we're not actually testing PDF writing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)
            writer.write(tmp)
            tmp_path = tmp.name
        
        yield tmp_path
        
        # Clean up the file after the test
        os.unlink(tmp_path)
    
    @pytest.fixture
    def mock_writer(self):
        """Create a mocked PdfWriter that tracks field updates."""
        class MockPdfWriter:
            def __init__(self):
                self.pages = [None]  # Simulate having one page
                self.updated_fields = {}
                
            def update_page_form_field_values(self, page, fields, auto_regenerate=True):
                self.updated_fields.update(fields)
                
        return MockPdfWriter()
    
    def test_simple_subtraction(self, mock_writer):
        """Test basic subtraction functionality."""
        # Create test data with subtraction
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 100,
                "value2": 25,
                "subtract_result": ["value1", "value2"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (100 - 25 = 75)
        assert test_data["section1"]["subtract_result"] == 75
        assert mock_writer.updated_fields["test_field"] == 75
    
    def test_multiple_subtractions(self, mock_writer):
        """Test subtraction with multiple values."""
        # Create test data with a chain of subtractions
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 200,
                "value2": 50,
                "value3": 30,
                "subtract_result": ["value1", "value2", "value3"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (200 - 50 - 30 = 120)
        assert test_data["section1"]["subtract_result"] == 120
        assert mock_writer.updated_fields["test_field"] == 120
    
    def test_negative_result_handling(self, mock_writer):
        """Test handling of negative results in subtraction."""
        # Create test data where subtraction yields a negative result
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 50,
                "value2": 75,
                "subtract_result": ["value1", "value2"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_json(test_data, mock_writer)
        
        # The code should convert negative results to "-0-" for display and 0 for calculations
        assert test_data["section1"]["subtract_result"] == 0
        assert mock_writer.updated_fields["test_field"] == "-0-"
    
    def test_nested_values_subtraction(self, mock_writer):
        """Test subtraction using values from nested sections."""
        # Create test data with nested values
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 300
            },
            "section2": {
                "nested": {
                    "value2": 150
                },
                "subtract_result": ["section1.value1", "section2.nested.value2"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Mock the find_key_in_json function to handle the nested paths
        def mock_find_key(data, path):
            if path == "section1.value1":
                return 300
            elif path == "section2.nested.value2":
                return 150
            return None
        
        # Patch the find_key_in_json function temporarily
        original_find_key = sys.modules["opentaxliberty"].find_key_in_json
        sys.modules["opentaxliberty"].find_key_in_json = mock_find_key
        
        try:
            # Process the JSON
            process_input_json(test_data, mock_writer)
            
            # Verify the subtraction was calculated correctly (300 - 150 = 150)
            assert test_data["section2"]["subtract_result"] == 150
            assert mock_writer.updated_fields["test_field"] == 150
        finally:
            # Restore the original function
            sys.modules["opentaxliberty"].find_key_in_json = original_find_key
    
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
