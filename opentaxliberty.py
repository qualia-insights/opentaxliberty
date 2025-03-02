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
    if not field_value == "":
        writer.update_page_form_field_values(
            writer.pages[0],
            #{"f1_32[0]": "11.11"},
            {field_name: field_value},
            auto_regenerate = False,
        )

def get_widgets():
    fields = []
    for page in reader.pages:
        for annot in page.annotations:
            annot = annot.get_object()
            if annot[AnnotationDictionaryAttributes.Subtype] == "/Widget":
                fields.append(annot)
    return fields

def get_filing_status_tag_and_value(key: str) -> tuple[str, str]:
    """
    Returns a tuple containing (tag, value) for the filing status.
    
    Args:
        key: The filing status key (e.g., 'single', 'married_filing_jointly')
        
    Returns:
        tuple: (tag, value) where tag is the PDF form field name and value is what to write
    """
    if key == "single":
        logger.debug("single filing status detected")
        return "c1_3[0]", "/1"
    elif key == "head_of_household":
        return "c1_3[0]", "/2"
    elif key == "married_filing_jointly":
        return "c1_3[1]", "/3"
    elif key == "married_filing_separately":
        return "c1_3[2]", "/4"
    elif key == "qualifying_surviving_spouse":
        return "c1_3[1]", "/5"
    elif key == "treating_nonresident_alien":
        return "c1_4[0]", "/1"
    else:
        error_msg = f"Unknown filing status: '{key}'. Valid options are: 'single', 'head_of_household', 'married_filing_jointy', 'married_filing_separately', 'qualifying_surviving_spouse','treating_nonresident_alien'"
        logger.error(error_msg)
        raise ValueError(error_msg)
        
def process_input_json(input_json_data: Dict[str, Any], writer: PdfWriter):
    for key in input_json_data:
        if key == "configuration":
            continue
        elif key == "w-2":
            w2_data = input_json_data[key]
            total_box_1 = 0
            for index in range(0, len(w2_data)-1):
                total_box_1 += w2_data[index]['box_1']
            write_field_pdf(writer, w2_data[-1]['tag'], total_box_1)
            continue
        elif key == "ssn":
            ssn_string = input_json_data[key]['value']
            ssns = ssn_string.split("-")
            ssn_output = ("%s         %s         %s" % (ssns[0], ssns[1], ssns[2]))
            write_field_pdf(writer, input_json_data[key]['tag'], ssn_output)
        elif key == "filing_status":
            try:
                filing_status_tag, filing_status_value = get_filing_status_tag_and_value(input_json_data[key]['value'])
                write_field_pdf(writer, filing_status_tag, filing_status_value)
    
                # Process any additional sub-keys that have corresponding tag fields
                for sub_key, sub_value in input_json_data[key].items():
                    # Skip the 'value' key as it's already processed
                    if sub_key == 'value':
                        continue
            
                    # Check if there's a corresponding tag field
                    tag_key = f"{sub_key}_tag"
                    if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
                        write_field_pdf(writer, input_json_data[key][tag_key], sub_value) 
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
            
                # Check if there's a corresponding tag field
                tag_key = f"{sub_key}_tag"
                if tag_key in input_json_data[key] and input_json_data[key][tag_key]:
                    write_field_pdf(writer, input_json_data[key][tag_key], sub_value) 

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

        page = reader.pages[0]
        fields = reader.get_fields()
        #keys_list = list(fields.keys())
        #fields_widgets = get_widgets()
        writer.append(reader)
        process_input_json(json_dict, writer)

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
        # cleanup before rasing a generic exception
        remove_job_directory(job_dir)
        raise HTTPException(status_code=500, detail=f"Error processing form: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

