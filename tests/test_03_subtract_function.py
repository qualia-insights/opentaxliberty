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
from opentaxliberty import process_input_config, find_key_in_json, write_field_pdf

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
    
    @pytest.fixture
    def mock_w2_data(self):
        """Create mock W-2 data for testing."""
        return {
            "totals": {
                "total_box_1": 6034.16,
                "total_box_2": 69.31
            }
        }
    
    def test_simple_subtraction(self, mock_writer, mock_w2_data):
        """Test basic subtraction functionality."""
        # Create test data with subtraction
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 100,
                "value1_tag": "value1_tag",
                "value2": 25,
                "value2_tag": "value2_tag",
                "subtract_result": ["value1", "value2"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (100 - 25 = 75)
        assert test_data["section1"]["subtract_result"] == 75
        assert mock_writer.updated_fields["test_field"] == 75
    
    def test_multiple_subtractions(self, mock_writer, mock_w2_data):
        """Test subtraction with multiple values."""
        # Create test data with a chain of subtractions
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 200,
                "value1_tag": "value1_tag",
                "value2": 50,
                "value2_tag": "value2_tag",
                "value3": 30,
                "value3_tag": "value3_tag",
                "subtract_result": ["value1", "value2", "value3"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (200 - 50 - 30 = 120)
        assert test_data["section1"]["subtract_result"] == 120
        assert mock_writer.updated_fields["test_field"] == 120
    
    def test_negative_result_handling(self, mock_writer, mock_w2_data):
        """Test handling of negative results in subtraction."""
        # Create test data where subtraction yields a negative result
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "section1": {
                "value1": 50,
                "value1_tag": "value1_tag",
                "value2": 75,
                "value2_tag": "value2_tag",
                "subtract_result": ["value1", "value2"],
                "subtract_result_tag": "test_field"
            }
        }
        
        # Process the JSON
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # The code should convert negative results to "-0-" for display and 0 for calculations
        assert test_data["section1"]["subtract_result"] == 0
        assert mock_writer.updated_fields["test_field"] == "-0-"
    
    def test_cross_section_subtraction(self, mock_writer, mock_w2_data):
        """Test subtraction using values across different sections."""
        # Create test data with cross-section references
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "income": {
                "L9": 5000,
                "L9_tag": "income_tag"
            },
            "deductions": {
                "L10": 3000,
                "L10_tag": "deduction_tag",
                "L11_subtract": ["L9", "L10"],
                "L11_subtract_tag": "result_tag"
            }
        }
        
        # Process the JSON 
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (5000 - 3000 = 2000)
        assert test_data["deductions"]["L11_subtract"] == 2000
        assert mock_writer.updated_fields["result_tag"] == 2000
    
    def test_using_w2_data(self, mock_writer, mock_w2_data):
        """Test integration with W-2 data in subtraction calculations."""
        # Create test data that references W-2 data
        test_data = {
            "configuration": {
                "tax_year": 2024
            },
            "income": {
                "L1a": "get_W-2_box_1_sum()",
                "L1a_tag": "l1a_tag",
                "deduction": 1000,
                "deduction_tag": "deduction_tag",
                "net_subtract": ["L1a", "deduction"],
                "net_subtract_tag": "net_tag"
            }
        }
        
        # This test will require special handling since W-2 data is processed differently
        # And the function call would be "mocked" or handled differently in actual execution
        # For now, we're testing the subtraction logic, not the W-2 data retrieval
        
        # Manually set the L1a value to match what would be pulled from W-2
        test_data["income"]["L1a"] = mock_w2_data["totals"]["total_box_1"]
        
        # Process the JSON
        process_input_config(test_data, mock_w2_data, mock_writer)
        
        # Verify the subtraction was calculated correctly (6034.16 - 1000 = 5034.16)
        assert test_data["income"]["net_subtract"] == 5034.16
        assert mock_writer.updated_fields["net_tag"] == 5034.16

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
