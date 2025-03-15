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
from typing import Union                                                        
from enum import Enum                                                           
from fastapi import FastAPI, status, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

import os
import sys
import json
from typing import Dict, Any
from pathlib import Path
import logging
import uuid
from datetime import datetime
from decimal import Decimal
import shutil

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

tags_metadata = [                                                               
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

def process_input_json(input_json_data: Dict[str, Any], writer: PdfWriter):
    for key in input_json_data:
        if key == "configuration":
            continue
        elif key == "w-2":
            w2_data = input_json_data[key]
            total_box_1 = 0
            total_box_2 = 0
            for index in range(0, len(w2_data)-2):
                if "_comment" in w2_data[index].keys():
                    continue
                elif "tag" in w2_data[index].keys():
                    continue
                total_box_1 += w2_data[index]['box_1']
                total_box_2 += w2_data[index]['box_2']
            input_json_data["income"]["L1a"] = total_box_1  # make L1a = total_box_1
            input_json_data["payments"]["L25a"] = total_box_2
            write_field_pdf(writer, w2_data[-2]['box_1_tag'], total_box_1)
            write_field_pdf(writer, w2_data[-1]['box_2_tag'], total_box_2)
        else:
            if 'tag' in input_json_data[key].keys() and 'value' in input_json_data[key].keys():
                write_field_pdf(writer, input_json_data[key]['tag'], input_json_data[key]['value'])
            # Process any additional sub-keys that have corresponding tag fields
            for sub_key, sub_value in input_json_data[key].items():
                # Skip the 'value' key as it's already processed
                if sub_key == 'value':
                    continue
                elif sub_key == '_comment':
                    continue
                elif "sum" in sub_key:
                    tag_key = f"{sub_key}_tag"
                    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
                        sum_fields_list = input_json_data[key][sub_key]
                        sum_calculation = 0
                        for index in range(0, len(sum_fields_list)):
                            is_numeric, numeric_value = is_number(find_key_in_json(input_json_data, sum_fields_list[index]))
                            if is_numeric:
                                sum_calculation += numeric_value
                        write_field_pdf(writer, input_json_data[key][tag_key], sum_calculation)
                        input_json_data[key][sub_key] = sum_calculation
                elif "subtract" in sub_key:
                    tag_key = f"{sub_key}_tag"
                    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
                        sub_fields_list = input_json_data[key][sub_key]
                        sub_calculation = find_key_in_json(input_json_data, sub_fields_list[0])
                        for index in range(1, len(sub_fields_list)):
                            value = find_key_in_json(input_json_data, sub_fields_list[index])
                            is_numeric, numeric_value = is_number(find_key_in_json(input_json_data, sub_fields_list[index]))
                            if is_numeric:
                                sub_calculation = sub_calculation - numeric_value
                        if sub_calculation < 0:
                            sub_calculation = "-0-"
                            input_json_data[key][sub_key] = 0
                        else:
                            input_json_data[key][sub_key] = sub_calculation
                            
                        write_field_pdf(writer, input_json_data[key][tag_key], sub_calculation)
                        sub_calculation = 0
                else:
                    # Check if there's a corresponding tag field
                    tag_key = f"{sub_key}_tag"
                    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
                        write_field_pdf(writer, input_json_data[key][tag_key], sub_value) 

def process_input_W_2(W_2_dict: Dict[str, Any]):
    """
    Process W-2 data from input dictionary and calculate totals.

    This function iterates through the W-2 entries in the input dictionary,
    calculates the sum of box_1 (wages) and box_2 (federal income tax withheld)
    values across all W-2 forms, and stores these totals in the dictionary.

    Args:
        W_2_dict (Dict[str, Any]): A dictionary containing W-2 data with the following structure:
            {
                "configuration": {...},
                "W-2": [
                    {"organization": str, "box_1": float, "box_2": float},
                    ...
                ],
                "totals": {...}  # Will be populated with calculated values
            }

    Returns:
        None: The function modifies the input dictionary in place, adding:
            - W_2_dict["totals"]["total_box_1"]: Total of all box_1 values
            - W_2_dict["totals"]["total_box_2"]: Total of all box_2 values

    Note:
        The function skips entries that contain a "_comment" key.
        The dictionary is expected to have a "totals" section to store the calculated values.
    """
    for key in W_2_dict:
        if key == "configuration":
            continue
        elif key == "W-2":
            W_2_data = W_2_dict[key] # this is getting the list of W-2 data
            total_box_1 = 0
            total_box_2 = 0
            for index in range(0, len(W_2_data)):
                if "_comment" in W_2_data[index].keys():
                    continue
                total_box_1 += W_2_data[index]['box_1']
                total_box_2 += W_2_data[index]['box_2']
            W_2_dict["totals"]["total_box_1"] = total_box_1  
            W_2_dict["totals"]["total_box_2"] = total_box_2

def parse_and_validate_input_files(config_file_name: str, W_2_config_file_name: str, 
        pdf_template_file_name: str, job_dir: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Parse and validate the input configuration files and PDF template.
    
    This function verifies that the PDF template exists and attempts to parse the JSON
    configuration files for tax form and W-2 data. It performs basic validation and
    raises appropriate exceptions if any validation fails.
    
    Args:
        config_file_name (str): Path to the main tax form configuration JSON file
        W_2_config_file_name (str): Path to the W-2 configuration JSON file
        pdf_template_file_name (str): Path to the PDF template file
        job_dir (str): Directory path for the current processing job
        
    Returns:
        tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing:
            - config_data: The parsed main tax form configuration data
            - W_2_config_data: The parsed W-2 configuration data
            
    Raises:
        HTTPException(404): If the PDF template file does not exist
        HTTPException(400): If the JSON files have invalid format
        HTTPException(500): For other unexpected errors during processing
    """
    try:
        # check template
        template_file_path = Path(pdf_template_file_name)
        if template_file_path.exists() == False:
            error_str = f"Error: Template PDF does not exist: {template_file_path}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=error_str)
    
        with open(config_file_name, 'r') as f:
                config_data = json.load(f)  # Load the JSON data from the config file
        
        with open(W_2_config_file_name, 'r') as f:
                W_2_config_data = json.load(f)  # Load the JSON data from the W-2 config file

        return config_data, W_2_config_data  # Changed the return order to match parameters
    except json.JSONDecodeError as e:
        error_str = f"Error: Invalid JSON format in uploaded configuration file: {str(e)}"
        logging.error(error_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
            detail=error_str)
    except HTTPException:
        # re-raise HTTP exceptions to be handled by FastAPI
        raise
    except Exception as e: # Catch other potential errors
        error_str = f"An unexpected error occurred while processing configuration: {str(e)}"
        logging.error(error_str)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=error_str)

def save_debug_json(json_dict : Dict[str, Any]):
    if json_dict is not None and "debug_json_output" in json_dict["configuration"]:
        with open(json_dict["configuration"]["debug_json_output"], 'w') as file:
            json.dump(json_dict, file, indent=4)

class processing_response(BaseModel):
    """Response model for successful processing"""
    message: str
    filename: str

@app.post("/api/process-tax-form", response_class=FileResponse)
async def process_tax_form(
    background_tasks: BackgroundTasks,
    config_file: UploadFile = File(...),
    W_2_config_fle: UploadFile = File(...),
    pdf_form: UploadFile = File(...),
):
    """
    Process a tax form PDF using a JSON configuration file.
    
    Args:
        background_tasks: Background tasks to run after returning response
        config_file (UploadFile): JSON configuration file that defines how to process the form
        W-2_config_file: a JSON configuration file that contains one or more W-2 forms
        pdf_form (UploadFile): The blank PDF tax form to process
    
    Returns:
        ProcessingResult: Results of the form processing

    Note on W-2 and using it as a variable name in Python.  The proper name is W-2.
    In Python, variable names can't start with a number or contain hyphens. 

    It contains a hyphen (-), which Python interprets as the subtraction operator
    When Python sees W-2, it tries to interpret it as "W minus 2" (a mathematical expression)

    This makes Python think you're trying to do a calculation with a decimal number, hence the "invalid decimal literal" error message.
    To fix this, OTL replaces the hypen with an underscore
    """
    # Generate unique ID for this processing request
    form_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create directories for this processing job
    job_dir = os.path.join(UPLOAD_DIR, form_id)
    os.makedirs(job_dir, exist_ok=True)
    
    W_2_dict = None
    config_dict = None
    try:
        # Save json configuration file
        config_path = os.path.join(job_dir, f"config_{config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())
            
        # Save PDF file
        pdf_path = os.path.join(job_dir, f"form_{pdf_form.filename}")
        with open(pdf_path, "wb") as f:
            f.write(await pdf_form.read())

        # Save the W-2 json configuration file
        W_2_config_path = os.path.join(job_dir, f"W-2_config_{W_2_config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())

        config_dict, W_2_dict = parse_and_validate_input_files(config_path, W_2_config_path, pdf_path, job_dir)
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # page = reader.pages[0]
        # fields = reader.get_fields()
        writer.append(reader)
        process_input_W_2(W_2_dict)
        process_input_json(json_dict, writer)

        output_file = os.path.join(job_dir, json_dict["configuration"]["output_file_name"])
        with open(output_file, "wb") as output_stream:
            writer.write(output_stream)

        # Add the cleanup task to run after the response is sent
        background_tasks.add_task(remove_job_directory, job_dir)

        save_debug_json(json_dict)

        # send the file back to the requestor
        return FileResponse(
            path=output_file,
            media_type="application/pdf",
            filename=json_dict["configuration"]["output_file_name"])

    except HTTPException as http_ex:
        # Cleanup before re-raising the HTTPException
        remove_job_directory(job_dir)
        save_debug_json(json_dict)
        # Re-raise the original HTTPException with its specific status code
        raise http_ex
    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        # cleanup before rasing a generic exception
        remove_job_directory(job_dir)
        save_debug_json(json_dict)
        raise HTTPException(status_code=500, detail=f"Error processing form: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

