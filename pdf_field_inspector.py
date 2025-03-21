# Open Tax Liberty - Python program to make IRS 1040 forms                      
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLCa
#
# PDF Field Inspector - utility to print all fields in a PDF form
# Based on the Open Tax Liberty project
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
from pypdf import PdfReader
from pypdf.constants import AnnotationDictionaryAttributes

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
