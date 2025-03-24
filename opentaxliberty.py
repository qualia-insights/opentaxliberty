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
from W2 import validate_W2_file, W2Document, W2Entry, W2Configuration
from F1040 import validate_F1040_file, F1040Document, create_F1040_pdf
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
    
    W2_doc = None
    F1040_doc = None
    try:
        # Save json configuration file
        config_path = os.path.join(job_dir, f"config_{config_file.filename}")
        with open(config_path, "wb") as f:
            f.write(await config_file.read())
            
        # Save PDF file
        pdf_path = os.path.join(job_dir, f"form_{pdf_form.filename}")
        with open(pdf_path, "wb") as f:
            f.write(await pdf_form.read())

        # check template
        template_file_path = Path(pdf_path)
        if template_file_path.exists() == False:
            error_str = f"Error: Template PDF does not exist: {template_file_path}"
            logging.error(error_str)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=error_str)
   
        # Validate W2 file using the W2_validator
        try:
            W2_doc = validate_W2_file(config_path)
            logging.info(f"W2 file validated successfully with {len(W2_doc.W2_entries)} entries")
            logging.info(f"Total Box 1 (Wages): {W2_doc.totals['total_box_1']}")
            logging.info(f"Total Box 2 (Federal Tax Withheld): {W2_doc.totals['total_box_2']}")
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
            F1040_doc = validate_F1040_file(config_path)
            logging.info(f"F1040 file validated successfully")
            logging.info(f"Tax year: {F1040_doc.configuration.tax_year}")
            logging.info(f"Taxpayer: {F1040_doc.name_address_ssn.first_name_middle_initial} {F1040_doc.name_address_ssn.last_name}")
            
            # Log refund or amount owed
            if F1040_doc.refund and hasattr(F1040_doc.refund, 'L34'):
                logging.info("Refund expected")
            elif F1040_doc.amount_you_owe and F1040_doc.amount_you_owe.L37:
                logging.info(f"Amount owed: {F1040_doc.amount_you_owe.L37}")
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

        output_file = os.path.join(job_dir, F1040_doc.configuration.output_file_name)
        create_F1040_pdf(F1040_doc, pdf_path, output_file)

        # Add the cleanup task to run after the response is sent
        background_tasks.add_task(remove_job_directory, job_dir)

        merged_dict = {
            "W2": W2_doc.model_dump(),
            "F1040": F1040_doc.model_dump() 
        }
        save_debug_json(merged_dict)

        # send the file back to the requestor
        return FileResponse(
            path=output_file,
            media_type="application/pdf",
            filename=F1040_doc.configuration.output_file_name)

    except HTTPException as http_ex:
        # Get the full stack trace as a string
        stack_trace = traceback.format_exc()
        
        # Log both the error message and the stack trace
        logger.error(f"HTTP Error processing form: {str(http_ex)}")
        logger.error(f"Stack trace: \n{stack_trace}")

        # Cleanup before re-raising the HTTPException
        remove_job_directory(job_dir)
        save_debug_json(F1040_doc.model_dump())

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
        save_debug_json(F1040_doc.model_dump())
    
        # Include line number information in the error detail
        error_info = f"Error processing form: {str(e)} at line {traceback.extract_tb(e.__traceback__)[-1].lineno}"
        raise HTTPException(status_code=500, detail=error_info)

@app.get("/")
async def root():
    return {"message": "Open Tax Liberty Form Processing API is running. Use /api/process-tax-form endpoint to process forms."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

