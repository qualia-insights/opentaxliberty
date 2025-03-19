# Open Tax Liberty - Python program to make IRS 1040 forms
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# 
#  OpenTaxLiberty for tax year 2024 

# FASTAPI dependencies
from typing import Union, Dict, Any, List
from enum import Enum                                                           
from fastapi import FastAPI, status, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

import os
import sys
import json
from pathlib import Path
import logging
import uuid
from datetime import datetime
from decimal import Decimal
import shutil
import traceback
from W2_validator import validate_W2_file, W2Document, W2Entry, W2Configuration
from F1040_validator import validate_F1040_file, F1040Document
from tax_form_tags import tax_form_tags_dict
import tempfile

# pypdf dependencies
from pypdf import PdfReader, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

description = """

Open Tax Liberty is a FastAPI application that will take as input a json
configuration file then produce tax forms filled out for the user.
                                                                                
""" 

tags_metadata: List[Dict[str, Any]] = [                                                               
    {                                                                           
        "name": "system",                                                       
        "description": "Queries the system and prints specs for  GPUs and versions of libraries",
    },                                                                          
    {                                                                           
        "name": "models",                                                       
        "description": "Manage models. So _fancy_ they have their own docs.",   
        "externalDocs": {                                                       
            "description": "models external docs",                              
            "url": "https://fastapi.tiangolo.com/",                             
        },                                                                      
    },                                                                          
]

app = FastAPI(                                                                  
    title="Open Tax Liberty",                                                 
    description=description,                                                    
    summary="Open Tax Liberty.",      
    version="0.0.1",                                                            
    #terms_of_service="http://example.com/terms/",                              
    contact={                                                                   
        "name": "Todd V. Rovito",                                               
        "url": "https://github.com/qualia-insights/opentaxliberty",                                                
        "email": "rovitotv@gmail.com",                                          
    },                                                                          
    license_info={                                                              
        "name": "AGPLv3",                                                       
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",                 
    },                                                                          
    openapi_tags = tags_metadata,                                               
)  

# configuration ===============================================================  
UPLOAD_DIR = "/workspace/temp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FastAPI Program =============================================================  

def is_number(value):
    """
    Check if a value is a number or can be converted to a number.
    
    Args:
        value: The value to check
        
    Returns:
        tuple: (is_number, converted_value)
            - is_number (bool): True if the value is a number or can be converted to a number
            - converted_value: The numeric value if conversion was successful, None otherwise
    """
    # Handle None values
    if value is None:
        return False, None
        
    # Handle native numeric types
    if isinstance(value, (int, float, Decimal)):
        return True, value
        
    # Try to convert strings to numbers
    if isinstance(value, str):
        # Remove any thousands separators and spaces
        cleaned_value = value.replace(',', '').replace(' ', '')
        
        # Skip empty strings
        if not cleaned_value:
            return False, None
            
        # Try to convert to float
        try:
            converted_value = float(cleaned_value)
            # If it's a whole number, convert to int for cleaner representation
            if converted_value.is_integer():
                converted_value = int(converted_value)
            return True, converted_value
        except ValueError:
            pass
            
    # Not a number
    return False, None

# Define a function to delete the file and its directory
def remove_job_directory(directory_path_str: str):
    try:
        # Recursively Delete the directory
        directory_path = Path(directory_path_str)
        if directory_path.exists():
            shutil.rmtree(directory_path)
            logger.info(f"Deleted directory: {directory_path}")
    except Exception as e:
        logger.error(f"Error deleting file or directory: {str(e)}")

def write_field_pdf(writer: PdfWriter, field_name: str, field_value: str):
    """
    Update a form field across all pages of a PDF.
    
    Args:
        writer (PdfWriter): The PDF writer object
        field_name (str): The name of the field to update
        field_value (str): The value to set the field to
    """
    if field_value == "":
        return
    elif field_value == 0:
        return
        
    # Try to update the field on each page
    field_found = False
    for page_num in range(len(writer.pages)):
        try:
            # Check if this page has the field by attempting to update it
            writer.update_page_form_field_values(
                writer.pages[page_num],
                {field_name: field_value},
                auto_regenerate=False
            )
            field_found = True
            # If we don't want to update the same field on multiple pages,
            # we could break here after the first success
            # break
        except Exception as e:
            # Field might not exist on this page, continue to next page
            continue
            
    # Optionally log if field wasn't found on any page
    if not field_found:
        logging.debug(f"Field '{field_name}' not found on any page")

def read_field_pdf(reader: PdfReader, field_name: str) -> str:
    """
    Read the value of a form field from a PDF.
    
    Args:
        reader (PdfReader): The PDF reader object
        field_name (str): The name of the field to read
        
    Returns:
        str: The value of the field, or empty string if field doesn't exist or has no value
    """
    fields = reader.get_fields()
    
    # Check if the field exists
    assert fields is not None, "fields dictionary should not be None at this point this is to help mypy"
    if field_name in fields:
        field = fields[field_name]
        
        # Handle different field types appropriately
        if isinstance(field, dict) and "/V" in field:
            return str(field["/V"])
        elif not isinstance(field, dict):
            return str(field)
    
    # Return empty string if field doesn't exist or has no value
    return ""

def find_key_in_json(input_json_data: Dict[str, Any], target_key: str) -> Any:
    """
    Search recursively through a nested JSON structure to find the first occurrence of a specific key.
    
    Args:
        input_json_data (Dict[str, Any]): The JSON data to search through
        target_key (str): The key to search for
        
    Returns:
        Any: The value associated with the first occurrence of the key, or None if not found
    """
    # Define a recursive helper function to search through the structure
    def search_recursive(data, key):
        # Base case: if data is a dictionary
        if isinstance(data, dict):
            # First check if the key exists directly in this dictionary
            if key in data:
                return data[key]
            
            # If not, recursively search through all values in the dictionary
            for k, v in data.items():
                result = search_recursive(v, key)
                if result is not None:  # Found the key in this branch
                    return result
                    
        # If data is a list, search through each element
        elif isinstance(data, list):
            for item in data:
                result = search_recursive(item, key)
                if result is not None:  # Found the key in this branch
                    return result
                    
        # If we get here, the key wasn't found in this branch
        return None

    # Start the recursive search
    result = search_recursive(input_json_data, target_key)
    
    # If the key wasn't found, raise an exception
    if result is None:
        raise KeyError(f"Key '{target_key}' not found in the JSON structure")
    
    return result    


def process_input_config(input_json_data: Dict[str, Any], W2_data: Dict[str, Any], writer: PdfWriter):
    """
    Process the input configuration data and update the PDF form fields.
    
    Args:
        input_json_data (Dict[str, Any]): The input JSON configuration data
        W2_data (Dict[str, Any]): The W2 data containing totals
        writer (PdfWriter): The PDF writer to update form fields
        
    Raises:
        KeyError: If a required key is not found
        ValueError: If a value cannot be processed correctly
    """
    for key in input_json_data:
        if key == "configuration":
            continue
            
        # Check for simple value/tag pairs
        #if 'tag' in input_json_data[key] and 'value' in input_json_data[key]:
        #    write_field_pdf(writer, input_json_data[key]['tag'], input_json_data[key]['value'])
            
        # Process any additional sub-keys that have corresponding tag fields
        for sub_key, sub_value in input_json_data[key].items():
            # Skip special keys
            # we skip the _tag because we use that information within the operations below
            if sub_key == '_comment' in sub_key:
                continue
            else:
                tag_key = f"{sub_key}_tag"
                if tag_key in tax_form_tags_dict["F1040"][key]:
                    write_field_pdf(writer, tax_form_tags_dict["F1040"][key][tag_key], sub_value)

def parse_and_validate_input_files(config_file_name: str, 
        pdf_template_file_name: str, job_dir: str) -> tuple[W2Document, F1040Document]:
    """
    Parse and validate the input configuration files and PDF template.
    
    This function verifies that the PDF template exists and attempts to parse the JSON
    configuration files for tax form and W2 data. It performs proper validation using
    the W2_validator and F1040_validator modules and raises appropriate exceptions if any validation fails.
    
    Args:
        config_file_name (str): Path to the main tax form configuration JSON file
        pdf_template_file_name (str): Path to the PDF template file
        job_dir (str): Directory path for the current processing job
        
    Returns:
        [W2Document, F1040Document]: A tuple containing:
            - W2_data: The validated W2Document object
            - F1040_data: The validated F1040Document object
            
    Raises:
        HTTPException(404): If the PDF template file does not exist
        HTTPException(400): If the JSON files have invalid format or validation fails
        HTTPException(500): For other unexpected errors during processing
    """
    config_data = None
    W2_data = None
    F1040_data = None
    
    try:
        # check template
        template_file_path = Path(pdf_template_file_name)
        if template_file_path.exists() == False:
            error_str = f"Error: Template PDF does not exist: {template_file_path}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=error_str)
   
        '''
        # this code is redundant because of the Validate F1040 code below 
        # Parse main config file
        try:
            with open(config_file_name, 'r') as f:
                config_data = json.load(f)  # Load the JSON data from the config file
        except json.JSONDecodeError as e:
            error_str = f"Error: Invalid JSON format in main configuration file ({config_file_name}): {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)
        '''        
        # Validate W2 file using the W2_validator
        try:
            W2_data = validate_W2_file(config_file_name)
            logging.info(f"W2 file validated successfully with {len(W2_data.W2_entries)} entries")
            logging.info(f"Total Box 1 (Wages): {W2_data.totals['total_box_1']}")
            logging.info(f"Total Box 2 (Federal Tax Withheld): {W2_data.totals['total_box_2']}")
        except json.JSONDecodeError as e:
            error_str = f"Error: Invalid JSON format in W2 configuration file ({config_file_name}): {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)
        except ValueError as e:
            error_str = f"Error: Invalid W2 data: {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)
        except Exception as e:
            error_str = f"Error validating W2 file: {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)

        # Validate F1040 file using the F1040_validator
        try:
            F1040_data = validate_F1040_file(config_file_name)
            logging.info(f"F1040 file validated successfully")
            logging.info(f"Tax year: {F1040_data.configuration.tax_year}")
            logging.info(f"Taxpayer: {F1040_data.name_address_ssn.first_name_middle_initial} {F1040_data.name_address_ssn.last_name}")
            
            # Log refund or amount owed
            if F1040_data.refund and hasattr(F1040_data.refund, 'L34_subtract_tag'):
                logging.info("Refund expected")
            elif F1040_data.amount_you_owe and F1040_data.amount_you_owe.L37:
                logging.info(f"Amount owed: {F1040_data.amount_you_owe.L37}")
            else:
                logging.info("Neither refund nor amount owed specified")
        except json.JSONDecodeError as e:
            error_str = f"Error: Invalid JSON format in F1040 configuration file ({config_file_name}): {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)
        except ValueError as e:
            error_str = f"Error: Invalid F1040 data: {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)
        except Exception as e:
            error_str = f"Error validating F1040 file: {str(e)}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                detail=error_str)

        return W2_data, F1040_data
        
    except HTTPException:
        # re-raise HTTP exceptions to be handled by FastAPI
        raise
    except Exception as e: # Catch other potential errors
        error_str = f"An unexpected error occurred while processing configuration: {str(e)}"
        logging.error(error_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=error_str)

# Decimal doesn't have a build in serialization function so we borrowed this one
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float
        return super().default(obj)

def save_debug_json(json_dict : Dict[str, Any] | None):
    if json_dict is not None and "debug_json_output" in json_dict["F1040"]["configuration"]:
        with open(json_dict["F1040"]["configuration"]["debug_json_output"], 'w') as file:
            json.dump(json_dict, file, indent=4, cls=DecimalEncoder)

class processing_response(BaseModel):
    """Response model for successful processing"""
    message: str
    filename: str

@app.post("/api/process-tax-form", response_class=FileResponse)
async def process_tax_form(
    background_tasks: BackgroundTasks,
    config_file: UploadFile = File(...),
    pdf_form: UploadFile = File(...),
):
    """
    Process a tax form PDF using a JSON configuration file.
    
    Args:
        background_tasks: Background tasks to run after returning response
        config_file (UploadFile): JSON configuration file that defines how to process the form
        W2_config_file: a JSON configuration file that contains 0 or more W2 forms
        pdf_form (UploadFile): The blank PDF tax form to process
    
    Returns:
        FileResponse: The processed PDF form
    """
    # Generate unique ID for this processing request
    form_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create directories for this processing job
    job_dir = os.path.join(UPLOAD_DIR, form_id)
    os.makedirs(job_dir, exist_ok=True)
    
    W2_data = None
    W2_dict = None
    F1040_data = None
    F1040_dict = None
    try:
        # Save json configuration file
        config_path = os.path.join(job_dir, f"config_{config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())
            
        # Save PDF file
        pdf_path = os.path.join(job_dir, f"form_{pdf_form.filename}")
        with open(pdf_path, "wb") as f:
            f.write(await pdf_form.read())

        W2_data, F1040_data = parse_and_validate_input_files(config_path, pdf_path, job_dir)
        F1040_dict = F1040_data.model_dump()  # this converts F1040_data into a dict
        W2_dict = W2_data.model_dump() # this converts W2_data into a dict

        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        writer.append(reader)
        
        # No need to call process_input_W2 since the W2 validation already calculates totals
        # Now we can directly use W2_data.totals in process_input_config
        process_input_config(F1040_dict, W2_dict, writer)

        output_file = os.path.join(job_dir, F1040_dict["configuration"]["output_file_name"])
        with open(output_file, "wb") as output_stream:
            writer.write(output_stream)

        # Add the cleanup task to run after the response is sent
        background_tasks.add_task(remove_job_directory, job_dir)

        merged_dict = {
            "W2": W2_dict,
            "F1040": F1040_dict
        }
        save_debug_json(merged_dict)

        # send the file back to the requestor
        return FileResponse(
            path=output_file,
            media_type="application/pdf",
            filename=F1040_dict["configuration"]["output_file_name"])

    except HTTPException as http_ex:
        # Get the full stack trace as a string
        stack_trace = traceback.format_exc()
        
        # Log both the error message and the stack trace
        logger.error(f"HTTP Error processing form: {str(http_ex)}")
        logger.error(f"Stack trace: \n{stack_trace}")

        # Cleanup before re-raising the HTTPException
        remove_job_directory(job_dir)
        save_debug_json(F1040_dict)

        # Include line number information in the error detail
        error_info = f"Error processing form: {str(http_ex)} at line {traceback.extract_tb(http_ex.__traceback__)[-1].lineno}"

        # Create a new HTTPException with the enhanced error information
        raise HTTPException(status_code=http_ex.status_code, detail=error_info)

    except Exception as e:
        # Get the full stack trace as a string
        stack_trace = traceback.format_exc()
    
        # Log both the error message and the stack trace
        logger.error(f"Error processing form: {str(e)}")
        logger.error(f"Stack trace: \n{stack_trace}")
    
        # cleanup before raising a generic exception
        remove_job_directory(job_dir)
        save_debug_json(F1040_dict)
    
        # Include line number information in the error detail
        error_info = f"Error processing form: {str(e)} at line {traceback.extract_tb(e.__traceback__)[-1].lineno}"
        raise HTTPException(status_code=500, detail=error_info)

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

