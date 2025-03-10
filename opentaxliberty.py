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
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging
import uuid
from datetime import datetime
import shutil
from collections import defaultdict

# pypdf dependencies
from pypdf import PdfReader, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# tracks what errors are reported to try and deduplicate errors that are reported
reported_errors = defaultdict(set)
# Track if any critical errors occurred during processing
has_critical_errors = False

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
    return isinstance(value, (int, float))

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

def process_input_json(input_json_data: Dict[str, Any], writer: PdfWriter):
    """
    Process the input JSON data and write the values to the PDF form.
    
    Args:
        input_json_data (Dict[str, Any]): The JSON data to process
        writer (PdfWriter): The PDF writer object to update
        
    Raises:
        KeyError: If a required key is missing in the JSON data
        ValueError: If a value cannot be processed correctly
        TypeError: If a value has an unexpected type
    """
    global has_critical_errors
    reset_error_tracking()  # Reset error tracking at the beginning
    
    try:
        if not isinstance(input_json_data, dict):
            raise TypeError(f"Expected input_json_data to be a dictionary, got {type(input_json_data).__name__}")
            
        # Ensure configuration exists
        if "configuration" not in input_json_data:
            raise KeyError("Missing required 'configuration' section in JSON data")
        
        for key in input_json_data:
            try:
                if key == "configuration":
                    # Just skip configuration section as it's handled elsewhere
                    continue
                elif key == "w-2":
                    process_w2_section(input_json_data, key, writer)
                else:
                    process_generic_section(input_json_data, key, writer)
            except Exception as key_error:
                logging.error(f"Error processing key '{key}': {str(key_error)}")
                has_critical_errors = True
                # Don't re-raise here, continue processing other sections
        
        # Check if any critical errors occurred during processing
        if has_critical_errors:
            raise ValueError("Critical errors occurred during form processing. Check logs for details.")
                
    except Exception as e:
        logging.error(f"Global error in process_input_json: {str(e)}")
        raise

def process_w2_section(input_json_data: Dict[str, Any], key: str, writer: PdfWriter):
    """Process the W-2 section of the input JSON data."""
    try:
        w2_data = input_json_data[key]
        if not isinstance(w2_data, list):
            error_msg = f"W-2 data should be a list, got {type(w2_data).__name__}"
            logging.error(error_msg)
            raise TypeError(error_msg)
            
        total_box_1, total_box_2 = calculate_w2_totals(w2_data)
        update_income_and_payments(input_json_data, total_box_1, total_box_2)
        write_w2_totals_to_pdf(w2_data, total_box_1, total_box_2, writer)
    except Exception as w2_error:
        logging.error(f"Error processing W-2 section: {str(w2_error)}")
        raise


def calculate_w2_totals(w2_data: List[Dict[str, Any]]) -> Tuple[float, float]:
    """Calculate the total box_1 and box_2 values from W-2 data."""
    total_box_1 = 0
    total_box_2 = 0
    
    # Process each W-2 entry, excluding the last two entries which contain tag information
    for index in range(0, len(w2_data)-2):
        try:
            if "_comment" in w2_data[index].keys():
                continue
            elif "tag" in w2_data[index].keys():
                continue
            
            # Validate box_1 and box_2 exist and are numeric
            if 'box_1' not in w2_data[index]:
                error_msg = f"Missing 'box_1' in W-2 entry {index}"
                logging.error(error_msg)
                raise KeyError(error_msg)
                
            if not is_number(w2_data[index]['box_1']):
                error_msg = f"Non-numeric 'box_1' value in W-2 entry {index}: {w2_data[index]['box_1']}"
                logging.error(error_msg)
                raise TypeError(error_msg)
                
            total_box_1 += w2_data[index]['box_1']
            
            # Box 2 is optional but must be numeric if present
            if 'box_2' in w2_data[index]:
                if not is_number(w2_data[index]['box_2']):
                    error_msg = f"Non-numeric 'box_2' value in W-2 entry {index}: {w2_data[index]['box_2']}"
                    logging.error(error_msg)
                    raise TypeError(error_msg)
                total_box_2 += w2_data[index]['box_2']
        except Exception as e:
            logging.error(f"Error processing W-2 entry {index}: {str(e)}")
            raise
    
    return total_box_1, total_box_2


def update_income_and_payments(input_json_data: Dict[str, Any], total_box_1: float, total_box_2: float):
    """Update the income and payments sections with W-2 totals."""
    try:
        # Check if we have Income section to update L1a
        if "income" in input_json_data:
            input_json_data["income"]["L1a"] = total_box_1
        else:
            error_msg = "Cannot update L1a: 'income' section missing"
            logging.error(error_msg)
            raise KeyError(error_msg)
            
        # Check if we have Payments section to update L25a
        if "payments" in input_json_data:
            input_json_data["payments"]["L25a"] = total_box_2
        else:
            error_msg = "Cannot update L25a: 'payments' section missing"
            logging.error(error_msg)
            raise KeyError(error_msg)
    except Exception as e:
        logging.error(f"Error updating income and payments with W-2 totals: {str(e)}")
        raise


def write_w2_totals_to_pdf(w2_data: List[Dict[str, Any]], total_box_1: float, total_box_2: float, writer: PdfWriter):
    """Write W-2 totals to the appropriate fields in the PDF."""
    try:
        if len(w2_data) < 2:
            error_msg = "W-2 data list is too short to contain tag references"
            logging.error(error_msg)
            raise ValueError(error_msg)
            
        if 'box_1_tag' not in w2_data[-2]:
            error_msg = "Cannot write total_box_1: 'box_1_tag' missing in W-2 data"
            logging.error(error_msg)
            raise KeyError(error_msg)
        write_field_pdf(writer, w2_data[-2]['box_1_tag'], total_box_1)
            
        if 'box_2_tag' not in w2_data[-1]:
            error_msg = "Cannot write total_box_2: 'box_2_tag' missing in W-2 data"
            logging.error(error_msg)
            raise KeyError(error_msg)
        write_field_pdf(writer, w2_data[-1]['box_2_tag'], total_box_2)
    except Exception as e:
        logging.error(f"Error writing W-2 totals to PDF: {str(e)}")
        raise


def process_generic_section(input_json_data: Dict[str, Any], key: str, writer: PdfWriter):
    """Process a generic section of the input JSON data."""
    try:
        section_data = input_json_data[key]
        if not isinstance(section_data, dict):
            error_msg = f"Section '{key}' is not a dictionary"
            logging.error(error_msg)
            raise TypeError(error_msg)
            
        # Handle value/tag pairs
        if 'tag' in section_data and 'value' in section_data:
            try:
                write_field_pdf(writer, section_data['tag'], section_data['value'])
            except Exception as e:
                logging.error(f"Error writing field with tag '{section_data['tag']}': {str(e)}")
                raise
        
        # Process sub-keys
        for sub_key, sub_value in section_data.items():
            try:
                # Skip specific keys
                if sub_key in ['value', '_comment']:
                    continue
                    
                # Handle sum calculations
                elif "sum" in sub_key:
                    process_sum_calculation(input_json_data, key, sub_key, writer)
                    
                # Handle subtraction calculations
                elif "subtract" in sub_key:
                    process_subtraction_calculation(input_json_data, key, sub_key, writer)
                    
                else:
                    # Handle regular field/tag pairs
                    process_regular_field(input_json_data, key, sub_key, sub_value, writer)
            except Exception as sub_key_error:
                logging.error(f"Error processing sub-key '{sub_key}' in section '{key}': {str(sub_key_error)}")
                raise
    except Exception as section_error:
        logging.error(f"Error processing section '{key}': {str(section_error)}")
        raise

def process_sum_calculation(input_json_data: Dict[str, Any], key: str, sub_key: str, writer: PdfWriter):
    """Process a sum calculation within a section."""
    global has_critical_errors
    tag_key = f"{sub_key}_tag"
    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
        try:
            sum_fields_list = input_json_data[key][sub_key]
            if not isinstance(sum_fields_list, list):
                error_msg = f"Sum field list for '{sub_key}' is not a list"
                logging.error(error_msg)
                has_critical_errors = True
                raise TypeError(error_msg)
                
            sum_calculation = 0
            missing_fields = []
            
            for index in range(0, len(sum_fields_list)):
                field_key = sum_fields_list[index]
                
                # Check if field exists in the section
                if field_key not in input_json_data[key]:
                    # Only record missing fields, don't raise error yet
                    missing_fields.append(field_key)
                    continue
                    
                value = input_json_data[key][field_key]
                if is_number(value):
                    sum_calculation += value
                else:
                    error_id = f"non_numeric_{key}_{field_key}"
                    if error_id not in reported_errors['type_error']:
                        error_msg = f"Non-numeric value for field '{field_key}' in sum '{sub_key}': {value}"
                        logging.error(error_msg)
                        reported_errors['type_error'].add(error_id)
                        has_critical_errors = True
                        raise TypeError(error_msg)
            
            # After processing all available fields, check if any were missing
            if missing_fields:
                # Create a unique error ID for this set of missing fields
                error_id = f"{key}_{sub_key}_missing_" + "_".join(missing_fields)
                
                # Only log this error if we haven't seen it before
                if error_id not in reported_errors['key_error']:
                    error_msg = f"Fields {missing_fields} referenced in sum '{sub_key}' not found"
                    logging.error(error_msg)
                    reported_errors['key_error'].add(error_id)
                    
                    # Mark as critical error if all fields are missing
                    if len(missing_fields) == len(sum_fields_list):
                        has_critical_errors = True
                        raise KeyError(error_msg)
            
            # Write the field with whatever value we calculated
            write_field_pdf(writer, input_json_data[key][tag_key], sum_calculation)
            input_json_data[key][sub_key] = sum_calculation
            
        except (TypeError, KeyError) as e:
            # Re-raise critical errors
            raise
        except Exception as sum_error:
            error_id = f"{key}_{sub_key}_calc_error"
            if error_id not in reported_errors['calc_error']:
                logging.error(f"Error calculating sum for '{sub_key}': {str(sum_error)}")
                reported_errors['calc_error'].add(error_id)
                has_critical_errors = True
            raise  # Re-raise to ensure processing fails

def process_subtraction_calculation(input_json_data: Dict[str, Any], key: str, sub_key: str, writer: PdfWriter):
    """Process a subtraction calculation within a section."""
    global has_critical_errors
    tag_key = f"{sub_key}_tag"
    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
        try:
            sub_fields_list = input_json_data[key][sub_key]
            if not isinstance(sub_fields_list, list):
                error_msg = f"Subtract field list for '{sub_key}' is not a list"
                logging.error(error_msg)
                has_critical_errors = True
                raise TypeError(error_msg)
                
            if len(sub_fields_list) < 2:
                error_msg = f"Subtract field list for '{sub_key}' needs at least 2 fields, got {len(sub_fields_list)}"
                logging.error(error_msg)
                has_critical_errors = True
                raise ValueError(error_msg)
            
            # Check for missing fields before processing
            missing_fields = []
            for field_key in sub_fields_list:
                if field_key not in input_json_data[key]:
                    missing_fields.append(field_key)
            
            if missing_fields:
                # Create a unique error ID for this set of missing fields
                error_id = f"{key}_{sub_key}_missing_" + "_".join(missing_fields)
                
                # Only log this error if we haven't seen it before
                if error_id not in reported_errors['key_error']:
                    error_msg = f"Fields {missing_fields} referenced in subtract '{sub_key}' not found"
                    logging.error(error_msg)
                    reported_errors['key_error'].add(error_id)
                    
                    # If all fields are missing, this is a critical error
                    if len(missing_fields) == len(sub_fields_list):
                        has_critical_errors = True
                        raise KeyError(error_msg)
                    
                    # If the first field (minuend) is missing, we can't proceed
                    if sub_fields_list[0] in missing_fields:
                        has_critical_errors = True
                        raise KeyError(f"Missing required field '{sub_fields_list[0]}' for subtraction in '{sub_key}'")
            
            # Get first value (minuend)
            sub_calculation = input_json_data[key][sub_fields_list[0]]
            if not is_number(sub_calculation):
                error_id = f"non_numeric_{key}_{sub_fields_list[0]}"
                if error_id not in reported_errors['type_error']:
                    error_msg = f"Non-numeric first value for subtract '{sub_key}': {sub_calculation}"
                    logging.error(error_msg)
                    reported_errors['type_error'].add(error_id)
                    has_critical_errors = True
                    raise TypeError(error_msg)
                
            # Subtract remaining values (subtrahends)
            for index in range(1, len(sub_fields_list)):
                field_key = sub_fields_list[index]
                if field_key not in input_json_data[key]:
                    # We already logged this above, so just skip
                    continue
                    
                value = input_json_data[key][field_key]
                if is_number(value):
                    sub_calculation = sub_calculation - value
                else:
                    error_id = f"non_numeric_{key}_{field_key}"
                    if error_id not in reported_errors['type_error']:
                        error_msg = f"Non-numeric value for field '{field_key}' in subtract '{sub_key}': {value}"
                        logging.error(error_msg)
                        reported_errors['type_error'].add(error_id)
                        has_critical_errors = True
                        raise TypeError(error_msg)
                    
            # Format negative values as "-0-" per IRS convention
            if sub_calculation < 0:
                display_value = "-0-"
            else:
                display_value = sub_calculation
                
            write_field_pdf(writer, input_json_data[key][tag_key], display_value)
            input_json_data[key][sub_key] = sub_calculation
            
        except (TypeError, ValueError, KeyError) as e:
            # Re-raise these as they're important validation errors
            raise
        except Exception as sub_error:
            error_id = f"{key}_{sub_key}_calc_error"
            if error_id not in reported_errors['calc_error']:
                logging.error(f"Error calculating subtraction for '{sub_key}': {str(sub_error)}")
                reported_errors['calc_error'].add(error_id)
                has_critical_errors = True
            raise  # Re-raise to ensure processing fails

def process_regular_field(input_json_data: Dict[str, Any], key: str, sub_key: str, sub_value: Any, writer: PdfWriter):
    """Process a regular field within a section."""
    tag_key = f"{sub_key}_tag"
    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
        try:
            write_field_pdf(writer, input_json_data[key][tag_key], sub_value)
        except Exception as field_error:
            logging.error(f"Error writing field '{sub_key}' with tag '{input_json_data[key][tag_key]}': {str(field_error)}")
            raise

def reset_error_tracking():
    """Reset the error tracking system between processing runs."""
    global reported_errors
    reported_errors = defaultdict(set)
    has_critical_errors = False

def parse_and_validate_input_json(input_json_file_name: str, 
        pdf_template_file_name: str, job_dir: str) -> Dict[str, Any]:
    try:
        # check template
        template_file_path = Path(pdf_template_file_name)
        if template_file_path.exists() == False:
            error_str = f"Error: Template PDF does not exist: {template_file_path}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=error_str)
    
        with open(input_json_file_name, 'r') as f:
                data = json.load(f)  # Load the JSON data from the file
                # validation of the file would occur here
                return data
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
        pdf_form (UploadFile): The PDF tax form to process
    
    Returns:
        ProcessingResult: Results of the form processing
    """
    # Generate unique ID for this processing request
    form_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Create directories for this processing job
    job_dir = os.path.join(UPLOAD_DIR, form_id)
    os.makedirs(job_dir, exist_ok=True)

    try:
        # Save json configuration file
        config_path = os.path.join(job_dir, f"config_{config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())
            
        # Save PDF file
        pdf_path = os.path.join(job_dir, f"form_{pdf_form.filename}")
        with open(pdf_path, "wb") as f:
            f.write(await pdf_form.read())

        json_dict = parse_and_validate_input_json(config_path, pdf_path, job_dir)
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # page = reader.pages[0]
        # fields = reader.get_fields()
        writer.append(reader)
        
        try:
            # Process the JSON input - catching specific exceptions from process_input_json
            process_input_json(json_dict, writer)
        except KeyError as ke:
            # Missing field or key
            logging.error(f"Missing required field in JSON: {str(ke)}")
            remove_job_directory(job_dir)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                               detail=f"Missing required field in configuration: {str(ke)}")
        except TypeError as te:
            # Type error (non-numeric value, wrong data structure, etc.)
            logging.error(f"Invalid data type in JSON: {str(te)}")
            remove_job_directory(job_dir)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                               detail=f"Invalid data type in configuration: {str(te)}")
        except ValueError as ve:
            # Value error (invalid value)
            logging.error(f"Invalid value in JSON: {str(ve)}")
            remove_job_directory(job_dir)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                               detail=f"Invalid value in configuration: {str(ve)}")

        output_file = os.path.join(job_dir, json_dict["configuration"]["output_file_name"])
        with open(output_file, "wb") as output_stream:
            writer.write(output_stream)

        # Add the cleanup task to run after the response is sent
        background_tasks.add_task(remove_job_directory, job_dir)

        # send the file back to the requestor
        return FileResponse(
            path=output_file,
            media_type="application/pdf",
            filename=json_dict["configuration"]["output_file_name"])

    except HTTPException as http_ex:
        # Cleanup before re-raising the HTTPException
        remove_job_directory(job_dir)
        # Re-raise the original HTTPException with its specific status code
        raise http_ex
    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        # cleanup before raising a generic exception
        remove_job_directory(job_dir)
        raise HTTPException(status_code=500, detail=f"Error processing form: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

