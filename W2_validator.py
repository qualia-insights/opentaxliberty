# W2 Validation module for Open Tax Liberty
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import sys
import json
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator


class W2Configuration(BaseModel):
    """Configuration section for the W2 form."""
    tax_year: int = Field(..., description="Tax year for the W2 form")
    form: str = Field(..., description="Form type, must be 'W2'")

    @field_validator('form')
    @classmethod
    def validate_form_type(cls, v):
        if v != "W2":
            raise ValueError(f"Form type must be 'W2', got '{v}'")
        return v

    @field_validator('tax_year')
    @classmethod
    def validate_tax_year(cls, v):
        current_year = 2025  # You might want to fetch this dynamically
        if v < 2020 or v > current_year:
            raise ValueError(f"Tax year must be between 2020 and {current_year}, got {v}")
        return v


class W2Entry(BaseModel):
    """A single W2 form entry."""
    organization: str = Field(..., description="Employer organization name")
    box_1: Decimal = Field(..., description="Wages, tips, other compensation", ge=0)
    box_2: Decimal = Field(..., description="Federal income tax withheld", ge=0)
    
    # Optional fields that could be added in the future
    box_3: Optional[Decimal] = Field(None, description="Social security wages", ge=0)
    box_4: Optional[Decimal] = Field(None, description="Social security tax withheld", ge=0)
    box_5: Optional[Decimal] = Field(None, description="Medicare wages and tips", ge=0)
    box_6: Optional[Decimal] = Field(None, description="Medicare tax withheld", ge=0)
    box_7: Optional[Decimal] = Field(None, description="Social security tips", ge=0)
    box_8: Optional[Decimal] = Field(None, description="Allocated tips", ge=0)
    box_10: Optional[Decimal] = Field(None, description="Dependent care benefits", ge=0)
    box_11: Optional[Decimal] = Field(None, description="Nonqualified plans", ge=0)
    box_12a_code: Optional[str] = Field(None, description="Box 12a code")
    box_12a_amount: Optional[Decimal] = Field(None, description="Box 12a amount")
    box_12b_code: Optional[str] = Field(None, description="Box 12b code")
    box_12b_amount: Optional[Decimal] = Field(None, description="Box 12b amount")
    box_12c_code: Optional[str] = Field(None, description="Box 12c code")
    box_12c_amount: Optional[Decimal] = Field(None, description="Box 12c amount")
    box_12d_code: Optional[str] = Field(None, description="Box 12d code")
    box_12d_amount: Optional[Decimal] = Field(None, description="Box 12d amount")
    box_13_retirement_plan: Optional[bool] = Field(None, description="Box 13 Retirement plan")
    box_13_third_party_sick_pay: Optional[bool] = Field(None, description="Box 13 Third-party sick pay")
    box_13_statutory_employee: Optional[bool] = Field(None, description="Box 13 Statutory employee")
    box_14: Optional[Dict[str, Union[str, Decimal]]] = Field(None, description="Box 14 Other")
    
    @field_validator('box_12a_code', 'box_12b_code', 'box_12c_code', 'box_12d_code')
    @classmethod
    def validate_box_12_codes(cls, v):
        if v is not None:
            valid_codes = [
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 
                'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y', 'Z', 'AA', 'BB', 
                'DD', 'EE', 'FF', 'GG', 'HH'
            ]
            if v not in valid_codes:
                raise ValueError(f"Invalid box 12 code: {v}. Must be one of {valid_codes}")
        return v


class W2Document(BaseModel):
    """Complete W2 document structure."""
    configuration: W2Configuration
    W2_entries: List[W2Entry] = Field(default_factory=list, description="List of W2 entries (can be empty)")
    totals: Dict[str, Any] = Field(description="Calculated totals")

    @model_validator(mode='before')
    @classmethod
    def initialize_totals(cls, values):
        if isinstance(values, dict) and "totals" not in values:
            values["totals"] = {}
        return values
    
    @model_validator(mode='after')
    def calculate_totals(self):
        """Calculate and populate the totals field."""
        w2_entries = self.W2_entries
        
        # Initialize totals with zero values in case there are no entries
        total_box_1 = Decimal('0')
        total_box_2 = Decimal('0')
        
        # Only calculate totals if there are entries
        if w2_entries:
            total_box_1 = sum(entry.box_1 for entry in w2_entries)
            total_box_2 = sum(entry.box_2 for entry in w2_entries)
        elif self.totals is None:
            self.totals = {}
            self.totals["total_box_1"] = 0
            self.totals["total_box_2"] = 0

        # Add an assertion to tell mypy that totals is definitely a dictionary at this point
        assert self.totals is not None
            
        self.totals["total_box_1"] = total_box_1
        self.totals["total_box_2"] = total_box_2
        
        # If other box fields are provided, calculate those totals as well
        optional_boxes = [3, 4, 5, 6, 7, 8, 10, 11]
        for box_num in optional_boxes:
            box_key = f"box_{box_num}"
            box_values = [getattr(entry, box_key) for entry in w2_entries if getattr(entry, box_key) is not None]
            if box_values:
                self.totals[f"total_{box_key}"] = sum(box_values)
            else:
                # Initialize with zero for consistent structure even if no values are present
                self.totals[f"total_{box_key}"] = Decimal('0')
        
        return self


def validate_W2_file(file_path: str) -> W2Document:
    """
    Validate a W2 configuration file and return a validated W2Document.
    
    Args:
        file_path (str): Path to the W2 JSON configuration file
        
    Returns:
        W2Document: Validated W2 document
        
    Raises:
        ValueError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValidationError: If the JSON doesn't conform to the W2Document schema
    """
    if not os.path.exists(file_path):
        raise ValueError(f"W2 configuration file does not exist: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)

    data = data["W2"]   # this parses the data down to just the W2 structure 
    # Parse and validate against our schema
    return W2Document.model_validate(data)


# If the module is run directly, validate a file
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python W2_validator.py <path_to_W2_json>")
        sys.exit(1)
    
    try:
        file_path = sys.argv[1]
        validated_data = validate_W2_file(file_path)
        print(validated_data.model_dump_json(indent=2))
        print(f"✅ W2 file validated successfully: {file_path}")
        print(f"Found {len(validated_data.W2_entries)} W2 entries")
        print(f"Total Box 1 (Wages): {validated_data.totals['total_box_1']}")
        print(f"Total Box 2 (Federal Tax Withheld): {validated_data.totals['total_box_2']}")
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        sys.exit(1)
