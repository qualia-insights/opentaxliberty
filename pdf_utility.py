# Open Tax Liberty - Python program to make IRS 1040 forms                      
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLCa
#
# PDF Field Inspector - utility to print all fields in a PDF form and
# write fields to the PDF
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import sys
import argparse
from pathlib import Path
import json

# pypdf dependencies
from pypdf import PdfReader, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes
from decimal import Decimal

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

    # Format decimal numbers to remove trailing .00 or .0
    
    # Convert field_value to string if it's not already
    if not isinstance(field_value, str):
        # For Decimal objects or other numeric types
        try:
            # Check if it's a whole number
            num_value = Decimal(str(field_value))
            if num_value == num_value.to_integral_value():
                field_value = str(int(num_value))
            else:
                field_value = str(field_value)
        except:
            field_value = str(field_value)
    else:
        # For string representations of numbers
        try:
            if '.' in field_value:
                # Check if it ends with .0 or .00
                if field_value.endswith('.0') or field_value.endswith('.00'):
                    num_value = Decimal(field_value)
                    field_value = str(int(num_value))
        except:
            # Keep original string value if conversion fails
            pass
         
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
            # It is not a good idea to break this loop
            # if we put a break here the second page is blank
        except Exception as e:
            # Field might not exist on this page, continue to next page
            continue
            
    if not field_found:
        raise ValueError(f"Field '{field_name}' not found on any page")

def get_form_fields(pdf_path):
    """Get all form fields from the PDF file."""
    reader = PdfReader(pdf_path)
    return reader.get_fields()

def get_widgets(pdf_path):
    """Get all widget annotations from the PDF file."""
    reader = PdfReader(pdf_path)
    fields = []
    for page_num, page in enumerate(reader.pages):
        for annot in page.annotations:
            annot_obj = annot.get_object()
            if annot_obj[AnnotationDictionaryAttributes.Subtype] == "/Widget":
                # Add page number to the annotation info
                annot_info = {"page": page_num}
                
                # Extract other useful annotation attributes
                for key in annot_obj:
                    if isinstance(annot_obj[key], (str, int, float, bool)):
                        annot_info[key] = annot_obj[key]
                    elif key == "/Rect":
                        annot_info["rect"] = [float(v) for v in annot_obj[key]]
                
                fields.append(annot_info)
    return fields

def main():
    parser = argparse.ArgumentParser(description='Inspect form fields in a PDF file')
    parser.add_argument('pdf_file', help='Path to the PDF file to inspect')
    parser.add_argument('--format', choices=['text', 'json'], default='text', 
                        help='Output format (text or json)')
    parser.add_argument('--widgets', action='store_true', 
                        help='Show detailed widget annotations')
    parser.add_argument('-o', '--output', help='Output file (defaults to stdout)')
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: File '{pdf_path}' does not exist.", file=sys.stderr)
        return 1
    
    # Get form fields
    form_fields = get_form_fields(pdf_path)
    
    # If requested, get detailed widget information
    widgets = get_widgets(pdf_path) if args.widgets else None
    
    # Prepare output
    if args.format == 'json':
        output = {
            "filename": str(pdf_path),
            "form_fields": form_fields
        }
        if widgets:
            output["widgets"] = widgets
        output_str = json.dumps(output, indent=2)
    else:
        # Text format
        output_lines = [
            f"PDF File: {pdf_path}",
            f"Number of form fields: {len(form_fields)}",
            "\nForm Fields:",
            "============"
        ]
        
        for field_name, field_value in form_fields.items():
            output_lines.append(f"\nField: {field_name}")
            if isinstance(field_value, dict):
                for k, v in field_value.items():
                    if "/Parent" not in k and "/Kids" not in k:
                        output_lines.append(f"  {k}: {v}")
            else:
                output_lines.append(f"  Value: {field_value}")
        
        if widgets:
            output_lines.extend([
                "\nWidget Annotations:",
                "==================="
            ])
            for i, widget in enumerate(widgets):
                output_lines.append(f"\nWidget #{i+1} (Page {widget.get('page', 'unknown')})")
                for k, v in widget.items():
                    if k != 'page':
                        output_lines.append(f"  {k}: {v}")
        
        output_str = "\n".join(output_lines)
    
    # Output to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_str)
        print(f"Output written to {args.output}")
    else:
        print(output_str)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
