# F1040 Validation module for Open Tax Liberty
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Usage:
#   from F1040_validator import validate_F1040_file
#   validated_data = validate_F1040_file("path/to/your/f1040_config.json")
# or run directly from the command line:
#   python F1040_validator.py path/to/your/f1040_config.json

import os
import sys
import json
from typing import List, Dict, Any, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator


class F1040Configuration(BaseModel):
    """Configuration section for the F1040 form."""
    tax_year: int = Field(..., description="Tax year for the 1040 form")
    form: str = Field(..., description="Form type, must be 'F1040'")
    output_file_name: str = Field(..., description="Output PDF file name")
    debug_json_output: Optional[str] = Field(None, description="Path to save debug JSON output")

    @field_validator('form')
    @classmethod
    def validate_form_type(cls, v):
        if v != "F1040":
            raise ValueError(f"Form type must be 'F1040', got '{v}'")
        return v

    @field_validator('tax_year')
    @classmethod
    def validate_tax_year(cls, v):
        current_year = 2025  # You might want to fetch this dynamically
        if v < 2020 or v > current_year:
            raise ValueError(f"Tax year must be between 2020 and {current_year}, got {v}")
        return v


class NameAddressSSN(BaseModel):
    """Name, address, and SSN information for the taxpayer and spouse."""
    first_name_middle_initial: str = Field(..., description="First name and middle initial")
    first_name_middle_initial_tag: str = Field(..., description="PDF field tag for first name and middle initial")
    last_name: str = Field(..., description="Last name")
    last_name_tag: str = Field(..., description="PDF field tag for last name")
    ssn: str = Field(..., description="Social Security Number")
    ssn_tag: str = Field(..., description="PDF field tag for SSN")
    
    spouse_first_name_middle_inital: Optional[str] = Field(None, description="Spouse's first name and middle initial")
    spouse_first_name_middle_inital_tag: Optional[str] = Field(None, description="PDF field tag for spouse's first name and middle initial")
    spouse_last_name: Optional[str] = Field(None, description="Spouse's last name")
    spouse_last_name_tag: Optional[str] = Field(None, description="PDF field tag for spouse's last name")
    spouse_ssn: Optional[str] = Field(None, description="Spouse's Social Security Number")
    spouse_ssn_tag: Optional[str] = Field(None, description="PDF field tag for spouse's SSN")
    
    home_address: str = Field(..., description="Home address")
    home_address_tag: str = Field(..., description="PDF field tag for home address")
    apartment_no: Optional[str] = Field(None, description="Apartment number")
    apartment_no_tag: Optional[str] = Field(None, description="PDF field tag for apartment number")
    city: str = Field(..., description="City")
    city_tag: str = Field(..., description="PDF field tag for city")
    state: str = Field(..., description="State")
    state_tag: str = Field(..., description="PDF field tag for state")
    zip: str = Field(..., description="ZIP code")
    zip_tag: str = Field(..., description="PDF field tag for ZIP code")
    
    foreign_country_name: Optional[str] = Field(None, description="Foreign country name")
    foreign_country_name_tag: Optional[str] = Field(None, description="PDF field tag for foreign country name")
    foreign_country_province: Optional[str] = Field(None, description="Foreign province/state")
    foreign_country_province_tag: Optional[str] = Field(None, description="PDF field tag for foreign province/state")
    foreign_country_postal_code: Optional[str] = Field(None, description="Foreign postal code")
    foreign_country_postal_code_tag: Optional[str] = Field(None, description="PDF field tag for foreign postal code")
    
    presidential_you: str = Field(..., description="Presidential campaign fund checkbox for you")
    presidential_you_tag: str = Field(..., description="PDF field tag for presidential campaign fund checkbox for you")
    presidential_spouse: Optional[str] = Field(None, description="Presidential campaign fund checkbox for spouse")
    presidential_spouse_tag: Optional[str] = Field(None, description="PDF field tag for presidential campaign fund checkbox for spouse")

    @field_validator('presidential_you', 'presidential_spouse')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class FilingStatus(BaseModel):
    """Filing status section of the 1040 form."""
    single_or_HOH: str = Field(..., description="Single or head of household filing status")
    single_or_HOH_tag: str = Field(..., description="PDF field tag for single or HOH status")
    
    married_filing_jointly_or_QSS: str = Field(..., description="Married filing jointly or qualifying surviving spouse")
    married_filing_jointly_or_QSS_tag: str = Field(..., description="PDF field tag for MFJ or QSS")
    
    married_filing_separately: str = Field(..., description="Married filing separately")
    married_filing_separately_tag: str = Field(..., description="PDF field tag for MFS")
    
    treating_nonresident_alien: Optional[str] = Field(None, description="Nonresident alien spouse treated as resident")
    treating_nonresident_alien_tag: Optional[str] = Field(None, description="PDF field tag for nonresident alien spouse")
    
    spouse_or_child_name: Optional[str] = Field(None, description="Spouse or qualifying child name")
    spouse_or_child_name_tag: Optional[str] = Field(None, description="PDF field tag for spouse or qualifying child name")
    
    nonresident_alien_name: Optional[str] = Field(None, description="Nonresident alien spouse name")
    nonresident_alien_name_tag: Optional[str] = Field(None, description="PDF field tag for nonresident alien spouse name")

    @model_validator(mode='after')
    def validate_filing_status_selection(self):
        """Validate that only one filing status is selected."""
        status_checkboxes = [
            (self.single_or_HOH, "single_or_HOH"),
            (self.married_filing_jointly_or_QSS, "married_filing_jointly_or_QSS"),
            (self.married_filing_separately, "married_filing_separately")
        ]
        
        active_statuses = [name for status, name in status_checkboxes if status not in ["/Off", None]]
        
        if len(active_statuses) != 1:
            raise ValueError(f"Exactly one filing status must be selected, found {len(active_statuses)}: {active_statuses}")
            
        return self


class DigitalAssets(BaseModel):
    """Digital assets section of the 1040 form."""
    value: str = Field(..., description="Digital assets checkbox value")
    tag: str = Field(..., description="PDF field tag for digital assets checkbox")

    @field_validator('value')
    @classmethod
    def validate_digital_assets_value(cls, v):
        if v not in ["/1", "/2"]:
            raise ValueError(f"Digital assets value must be '/1' (Yes) or '/2' (No), got '{v}'")
        return v


class StandardDeduction(BaseModel):
    """Standard deduction section of the 1040 form."""
    you_as_a_dependent: str = Field(..., description="Someone can claim you as a dependent")
    you_as_a_dependent_tag: str = Field(..., description="PDF field tag for you as dependent")
    
    your_spouse_as_a_dependent: Optional[str] = Field(None, description="Someone can claim your spouse as a dependent")
    your_spouse_as_a_dependent_tag: Optional[str] = Field(None, description="PDF field tag for spouse as dependent")
    
    spouse_itemizes: Optional[str] = Field(None, description="Spouse itemizes on a separate return")
    spouse_itemizes_tag: Optional[str] = Field(None, description="PDF field tag for spouse itemizes")
    
    born_before_jan_2_1960: str = Field(..., description="You were born before January 2, 1960")
    born_before_jan_2_1960_tag: str = Field(..., description="PDF field tag for your age")
    
    are_blind: str = Field(..., description="You are blind")
    are_blind_tag: str = Field(..., description="PDF field tag for your blindness")
    
    spouse_born_before_jan_2_1960: Optional[str] = Field(None, description="Spouse was born before January 2, 1960")
    spouse_born_before_jan_2_1960_tag: Optional[str] = Field(None, description="PDF field tag for spouse's age")
    
    spouse_is_blind: Optional[str] = Field(None, description="Spouse is blind")
    spouse_is_blind_tag: Optional[str] = Field(None, description="PDF field tag for spouse's blindness")

    @field_validator('you_as_a_dependent', 'your_spouse_as_a_dependent', 'spouse_itemizes', 
                     'born_before_jan_2_1960', 'are_blind', 'spouse_born_before_jan_2_1960', 
                     'spouse_is_blind')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class Dependents(BaseModel):
    """Dependents section of the 1040 form."""
    check_if_more_than_4_dependents: str = Field(..., description="Check if you have more than 4 dependents")
    check_if_more_than_4_dependents_tag: str = Field(..., description="PDF field tag for more than 4 dependents")
    
    # Dependent 1
    dependent_1_first_last_name: Optional[str] = Field(None, description="First dependent's name")
    dependent_1_first_last_name_tag: Optional[str] = Field(None, description="PDF field tag for first dependent's name")
    dependent_1_ssn: Optional[str] = Field(None, description="First dependent's SSN")
    dependent_1_ssn_tag: Optional[str] = Field(None, description="PDF field tag for first dependent's SSN")
    dependent_1_relationship: Optional[str] = Field(None, description="First dependent's relationship")
    dependent_1_relationship_tag: Optional[str] = Field(None, description="PDF field tag for first dependent's relationship")
    dependent_1_child_tax_credit: Optional[str] = Field(None, description="First dependent's child tax credit")
    dependent_1_child_tax_credit_tag: Optional[str] = Field(None, description="PDF field tag for first dependent's child tax credit")
    dependent_1_credit_for_other_dependents: Optional[str] = Field(None, description="First dependent's credit for other dependents")
    dependent_1_credit_for_other_dependents_tag: Optional[str] = Field(None, description="PDF field tag for first dependent's credit for other dependents")
    
    # Dependent 2
    dependent_2_first_last_name: Optional[str] = Field(None, description="Second dependent's name")
    dependent_2_first_last_name_tag: Optional[str] = Field(None, description="PDF field tag for second dependent's name")
    dependent_2_ssn: Optional[str] = Field(None, description="Second dependent's SSN")
    dependent_2_ssn_tag: Optional[str] = Field(None, description="PDF field tag for second dependent's SSN")
    dependent_2_relationship: Optional[str] = Field(None, description="Second dependent's relationship")
    dependent_2_relationship_tag: Optional[str] = Field(None, description="PDF field tag for second dependent's relationship")
    dependent_2_child_tax_credit: Optional[str] = Field(None, description="Second dependent's child tax credit")
    dependent_2_child_tax_credit_tag: Optional[str] = Field(None, description="PDF field tag for second dependent's child tax credit")
    dependent_2_credit_for_other_dependents: Optional[str] = Field(None, description="Second dependent's credit for other dependents")
    dependent_2_credit_for_other_dependents_tag: Optional[str] = Field(None, description="PDF field tag for second dependent's credit for other dependents")
    
    # Dependent 3
    dependent_3_first_last_name: Optional[str] = Field(None, description="Third dependent's name")
    dependent_3_first_last_name_tag: Optional[str] = Field(None, description="PDF field tag for third dependent's name")
    dependent_3_ssn: Optional[str] = Field(None, description="Third dependent's SSN")
    dependent_3_ssn_tag: Optional[str] = Field(None, description="PDF field tag for third dependent's SSN")
    dependent_3_relationship: Optional[str] = Field(None, description="Third dependent's relationship")
    dependent_3_relationship_tag: Optional[str] = Field(None, description="PDF field tag for third dependent's relationship")
    dependent_3_child_tax_credit: Optional[str] = Field(None, description="Third dependent's child tax credit")
    dependent_3_child_tax_credit_tag: Optional[str] = Field(None, description="PDF field tag for third dependent's child tax credit")
    dependent_3_credit_for_other_dependents: Optional[str] = Field(None, description="Third dependent's credit for other dependents")
    dependent_3_credit_for_other_dependents_tag: Optional[str] = Field(None, description="PDF field tag for third dependent's credit for other dependents")
    
    # Dependent 4
    dependent_4_first_last_name: Optional[str] = Field(None, description="Fourth dependent's name")
    dependent_4_first_last_name_tag: Optional[str] = Field(None, description="PDF field tag for fourth dependent's name")
    dependent_4_ssn: Optional[str] = Field(None, description="Fourth dependent's SSN")
    dependent_4_ssn_tag: Optional[str] = Field(None, description="PDF field tag for fourth dependent's SSN")
    dependent_4_relationship: Optional[str] = Field(None, description="Fourth dependent's relationship")
    dependent_4_relationship_tag: Optional[str] = Field(None, description="PDF field tag for fourth dependent's relationship")
    dependent_4_child_tax_credit: Optional[str] = Field(None, description="Fourth dependent's child tax credit")
    dependent_4_child_tax_credit_tag: Optional[str] = Field(None, description="PDF field tag for fourth dependent's child tax credit")
    dependent_4_credit_for_other_dependents: Optional[str] = Field(None, description="Fourth dependent's credit for other dependents")
    dependent_4_credit_for_other_dependents_tag: Optional[str] = Field(None, description="PDF field tag for fourth dependent's credit for other dependents")

    @field_validator('check_if_more_than_4_dependents', 'dependent_1_child_tax_credit', 
                    'dependent_1_credit_for_other_dependents', 'dependent_2_child_tax_credit',
                    'dependent_2_credit_for_other_dependents', 'dependent_3_child_tax_credit',
                    'dependent_3_credit_for_other_dependents', 'dependent_4_child_tax_credit',
                    'dependent_4_credit_for_other_dependents')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    @model_validator(mode='after')
    def validate_dependent_completeness(self):
        """Validate that all fields for a dependent are either all set or all None."""
        for i in range(1, 5):  # Check dependents 1-4
            name = getattr(self, f"dependent_{i}_first_last_name")
            if name:
                # If name is provided, validate all required fields are present
                required_fields = [
                    f"dependent_{i}_ssn",
                    f"dependent_{i}_relationship",
                    f"dependent_{i}_first_last_name_tag",
                    f"dependent_{i}_ssn_tag",
                    f"dependent_{i}_relationship_tag"
                ]
                
                for field in required_fields:
                    if not getattr(self, field):
                        raise ValueError(f"If dependent_{i}_first_last_name is provided, {field} must also be provided")
                        
        return self


class Income(BaseModel):
    """Income section of the 1040 form."""
    # Lines 1a-1i and 1z
    L1a: Union[str, int, float, Decimal] = Field(..., description="Wages, salaries, tips, etc.")
    L1a_tag: str = Field(..., description="PDF field tag for line 1a")
    L1b: Optional[Union[int, float, Decimal]] = Field(None, description="Household employee wages")
    L1b_tag: Optional[str] = Field(None, description="PDF field tag for line 1b")
    L1c: Optional[Union[int, float, Decimal]] = Field(None, description="Tip income")
    L1c_tag: Optional[str] = Field(None, description="PDF field tag for line 1c")
    L1d: Optional[Union[int, float, Decimal]] = Field(None, description="Medicaid waiver payments")
    L1d_tag: Optional[str] = Field(None, description="PDF field tag for line 1d")
    L1e: Optional[Union[int, float, Decimal]] = Field(None, description="Taxable dependent care benefits")
    L1e_tag: Optional[str] = Field(None, description="PDF field tag for line 1e")
    L1f: Optional[Union[int, float, Decimal]] = Field(None, description="Employer provided adoption benefits")
    L1f_tag: Optional[str] = Field(None, description="PDF field tag for line 1f")
    L1g: Optional[Union[int, float, Decimal]] = Field(None, description="Scholarship and fellowship grants")
    L1g_tag: Optional[str] = Field(None, description="PDF field tag for line 1g")
    L1h: Optional[Union[int, float, Decimal]] = Field(None, description="Pensions and annuities from Form 1099-R, Box 2a")
    L1h_tag: Optional[str] = Field(None, description="PDF field tag for line 1h")
    L1i: Optional[Union[int, float, Decimal]] = Field(None, description="Other earned income")
    L1i_tag: Optional[str] = Field(None, description="PDF field tag for line 1i")
    L1z_sum: List[str] = Field(..., description="List of fields to sum for line 1z")
    L1z_sum_tag: str = Field(..., description="PDF field tag for line 1z")
    
    # Other income lines
    L2a: Optional[Union[int, float, Decimal]] = Field(None, description="Tax-exempt interest")
    L2a_tag: Optional[str] = Field(None, description="PDF field tag for line 2a")
    L2b: Optional[Union[int, float, Decimal]] = Field(None, description="Taxable interest")
    L2b_tag: Optional[str] = Field(None, description="PDF field tag for line 2b")
    L3a: Optional[Union[int, float, Decimal]] = Field(None, description="Qualified dividends")
    L3a_tag: Optional[str] = Field(None, description="PDF field tag for line 3a")
    L3b: Optional[Union[int, float, Decimal]] = Field(None, description="Ordinary dividends")
    L3b_tag: Optional[str] = Field(None, description="PDF field tag for line 3b")
    L4a: Optional[Union[int, float, Decimal]] = Field(None, description="IRA distributions")
    L4a_tag: Optional[str] = Field(None, description="PDF field tag for line 4a")
    L4b: Optional[Union[int, float, Decimal]] = Field(None, description="Taxable IRA distributions")
    L4b_tag: Optional[str] = Field(None, description="PDF field tag for line 4b")
    L5a: Optional[Union[int, float, Decimal]] = Field(None, description="Pensions and annuities")
    L5a_tag: Optional[str] = Field(None, description="PDF field tag for line 5a")
    L5b: Optional[Union[int, float, Decimal]] = Field(None, description="Taxable pensions and annuities")
    L5b_tag: Optional[str] = Field(None, description="PDF field tag for line 5b")
    L6a: Optional[Union[int, float, Decimal]] = Field(None, description="Social security benefits")
    L6a_tag: Optional[str] = Field(None, description="PDF field tag for line 6a")
    L6b: Optional[Union[int, float, Decimal]] = Field(None, description="Taxable social security benefits")
    L6b_tag: Optional[str] = Field(None, description="PDF field tag for line 6b")
    L6c: Optional[str] = Field(None, description="Are you a retired public safety officer?")
    L6c_tag: Optional[str] = Field(None, description="PDF field tag for line 6c")
    L7cb: Optional[str] = Field(None, description="Capital gain or loss")
    L7cb_tag: Optional[str] = Field(None, description="PDF field tag for line 7cb")
    L7: Optional[Union[int, float, Decimal]] = Field(None, description="Capital gain or loss")
    L7_tag: Optional[str] = Field(None, description="PDF field tag for line 7")
    L8: Optional[Union[int, float, Decimal]] = Field(None, description="Other income")
    L8_tag: Optional[str] = Field(None, description="PDF field tag for line 8")
    
    # Total income and adjusted gross income
    L9_sum: List[str] = Field(..., description="List of fields to sum for line 9")
    L9_sum_tag: str = Field(..., description="PDF field tag for line 9")
    L10: Optional[Union[int, float, Decimal]] = Field(None, description="Adjustments to income")
    L10_tag: Optional[str] = Field(None, description="PDF field tag for line 10")
    L11_subtract: List[str] = Field(..., description="List of fields to subtract for line 11")
    L11_subtract_tag: str = Field(..., description="PDF field tag for line 11")
    L12: Optional[Union[int, float, Decimal]] = Field(None, description="Standard deduction or itemized deductions")
    L12_tag: Optional[str] = Field(None, description="PDF field tag for line 12")
    L13: Optional[Union[int, float, Decimal]] = Field(None, description="Qualified business income deduction")
    L13_tag: Optional[str] = Field(None, description="PDF field tag for line 13")
    L14_sum: List[str] = Field(..., description="List of fields to sum for line 14")
    L14_sum_tag: str = Field(..., description="PDF field tag for line 14")
    L15_subtract: List[str] = Field(..., description="List of fields to subtract for line 15")
    L15_subtract_tag: str = Field(..., description="PDF field tag for line 15")
    
    @field_validator('L6c', 'L7cb')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    @field_validator('L1a')
    @classmethod
    def validate_wages(cls, v):
        # Allow either a numeric value or the special function string
        if isinstance(v, str) and v != "get_W2_box_1_sum()":
            try:
                float(v)  # Try to convert to float
            except ValueError:
                if v != "get_W2_box_1_sum()":
                    raise ValueError(f"L1a must be a number or 'get_W2_box_1_sum()', got '{v}'")
        return v


class TaxAndCredits(BaseModel):
    """Tax and credits section of the 1040 form."""
    L16_check_8814: Optional[str] = Field(None, description="Form 8814 checkbox")
    L16_check_8814_tag: Optional[str] = Field(None, description="PDF field tag for Form 8814 checkbox")
    L16_check_4972: Optional[str] = Field(None, description="Form 4972 checkbox")
    L16_check_4972_tag: Optional[str] = Field(None, description="PDF field tag for Form 4972 checkbox")
    L16_check_3: Optional[str] = Field(None, description="Other checkbox")
    L16_check_3_tag: Optional[str] = Field(None, description="PDF field tag for other checkbox")
    L16_check_3_field: Optional[Union[int, float, Decimal]] = Field(None, description="Other tax forms amount")
    L16_check_3_field_tag: Optional[str] = Field(None, description="PDF field tag for other tax forms amount")
    L16: Union[int, float, Decimal] = Field(..., description="Tax amount")
    L16_tag: str = Field(..., description="PDF field tag for line 16")
    L17: Optional[Union[int, float, Decimal]] = Field(None, description="Amount from Schedule 2, line 3")
    L17_tag: Optional[str] = Field(None, description="PDF field tag for line 17")
    L18_sum: List[str] = Field(..., description="List of fields to sum for line 18")
    L18_sum_tag: str = Field(..., description="PDF field tag for line 18")
    L19: Optional[Union[int, float, Decimal]] = Field(None, description="Child tax credit/credit for other dependents")
    L19_tag: Optional[str] = Field(None, description="PDF field tag for line 19")
    L20: Optional[Union[int, float, Decimal]] = Field(None, description="Amount from Schedule 3, line 8")
    L20_tag: Optional[str] = Field(None, description="PDF field tag for line 20")
    L21_sum: List[str] = Field(..., description="List of fields to sum for line 21")
    L21_sum_tag: str = Field(..., description="PDF field tag for line 21")
    L22_subtract: List[str] = Field(..., description="List of fields to subtract for line 22")
    L22_subtract_tag: str = Field(..., description="PDF field tag for line 22")
    L23: Optional[Union[int, float, Decimal]] = Field(None, description="Other taxes from Schedule 2, line 21")
    L23_tag: Optional[str] = Field(None, description="PDF field tag for line 23")
    L24_sum: List[str] = Field(..., description="List of fields to sum for line 24")
    L24_sum_tag: str = Field(..., description="PDF field tag for line 24")
    
    @field_validator('L16_check_8814', 'L16_check_4972', 'L16_check_3')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class Payments(BaseModel):
    """Payments section of the 1040 form."""
    L25a: Union[str, int, float, Decimal] = Field(..., description="Federal income tax withheld from Forms W-2")
    L25a_tag: str = Field(..., description="PDF field tag for line 25a")
    L25b: Optional[Union[int, float, Decimal]] = Field(None, description="Federal income tax withheld from Form 1099")
    L25b_tag: Optional[str] = Field(None, description="PDF field tag for line 25b")
    L25c: Optional[Union[int, float, Decimal]] = Field(None, description="Federal income tax withheld from other forms")
    L25c_tag: Optional[str] = Field(None, description="PDF field tag for line 25c")
    L25d_sum: List[str] = Field(..., description="List of fields to sum for line 25d")
    L25d_sum_tag: str = Field(..., description="PDF field tag for line 25d")
    L26: Optional[Union[int, float, Decimal]] = Field(None, description="Estimated tax payments")
    L26_tag: Optional[str] = Field(None, description="PDF field tag for line 26")
    L27: Optional[Union[int, float, Decimal]] = Field(None, description="Earned income credit (EIC)")
    L27_tag: Optional[str] = Field(None, description="PDF field tag for line 27")
    L28: Optional[Union[int, float, Decimal]] = Field(None, description="Additional child tax credit")
    L28_tag: Optional[str] = Field(None, description="PDF field tag for line 28")
    L29: Optional[Union[int, float, Decimal]] = Field(None, description="American opportunity credit")
    L29_tag: Optional[str] = Field(None, description="PDF field tag for line 29")
    L31: Optional[Union[int, float, Decimal]] = Field(None, description="Amount from Schedule 3, line 15")
    L31_tag: Optional[str] = Field(None, description="PDF field tag for line 31")
    L32_sum: List[str] = Field(..., description="List of fields to sum for line 32")
    L32_sum_tag: str = Field(..., description="PDF field tag for line 32")
    L33_sum: List[str] = Field(..., description="List of fields to sum for line 33")
    L33_sum_tag: str = Field(..., description="PDF field tag for line 33")
    
    @field_validator('L25a')
    @classmethod
    def validate_withholding(cls, v):
        # Allow either a numeric value or the special function string
        if isinstance(v, str):
            if v != "get_W2_box_2_sum()":
                try:
                    float(v)  # Try to convert to float
                except ValueError:
                    raise ValueError(f"L25a must be a number or 'get_W2_box_2_sum()', got '{v}'")
        return v


class Refund(BaseModel):
    """Refund section of the 1040 form."""
    L34_subtract: List[str] = Field(..., description="List of fields to subtract for line 34")
    L34_subtract_tag: str = Field(..., description="PDF field tag for line 34")
    L35a_check: Optional[str] = Field(None, description="Amount applied to estimated tax")
    L35a_check_tag: Optional[str] = Field(None, description="PDF field tag for amount applied to estimated tax checkbox")
    L35a_sum: Optional[List[str]] = Field(None, description="List of fields to sum for line 35a")
    L35a_sum_tag: Optional[str] = Field(None, description="PDF field tag for line 35a")
    L35a_b: Optional[str] = Field(None, description="Routing number for direct deposit")
    L35a_b_tag: Optional[str] = Field(None, description="PDF field tag for routing number")
    L35c_checking: Optional[str] = Field(None, description="Checking account checkbox")
    L35c_checking_tag: Optional[str] = Field(None, description="PDF field tag for checking account checkbox")
    L35c_savings: Optional[str] = Field(None, description="Savings account checkbox")
    L35c_savings_tag: Optional[str] = Field(None, description="PDF field tag for savings account checkbox")
    L35a_d: Optional[str] = Field(None, description="Account number for direct deposit")
    L35a_d_tag: Optional[str] = Field(None, description="PDF field tag for account number")
    L36: Optional[Union[int, float, Decimal, str]] = Field(None, description="Amount you want applied to next year's estimated tax")
    L36_tag: Optional[str] = Field(None, description="PDF field tag for line 36")

    @field_validator('L35a_check', 'L35c_checking', 'L35c_savings')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    @model_validator(mode='after')
    def validate_account_info_completeness(self):
        """Validate that direct deposit information is complete if provided."""
        # If any direct deposit field is provided, all required fields should be provided
        direct_deposit_fields = [self.L35a_b, self.L35a_d]
        account_type_fields = [self.L35c_checking, self.L35c_savings]
        
        # Check if any direct deposit information is provided
        if any(field is not None and field for field in direct_deposit_fields):
            # Check that all required fields are provided
            missing_fields = []
            if not self.L35a_b:
                missing_fields.append("L35a_b (routing number)")
            if not self.L35a_d:
                missing_fields.append("L35a_d (account number)")
                
            # Check that exactly one account type is selected
            selected_account_types = [field for field in account_type_fields if field == "/1"]
            if len(selected_account_types) != 1:
                missing_fields.append("exactly one of L35c_checking or L35c_savings must be selected")
                
            if missing_fields:
                raise ValueError(f"If direct deposit information is provided, the following fields must be properly completed: {', '.join(missing_fields)}")
                
        return self


class AmountYouOwe(BaseModel):
    """Amount You Owe section of the 1040 form."""
    L37: Optional[Union[int, float, Decimal]] = Field(None, description="Amount you owe")
    L37_tag: Optional[str] = Field(None, description="PDF field tag for line 37")
    L38: Optional[Union[int, float, Decimal]] = Field(None, description="Estimated tax penalty")
    L38_tag: Optional[str] = Field(None, description="PDF field tag for line 38")


class ThirdPartyDesignee(BaseModel):
    """Third Party Designee section of the 1040 form."""
    do_you_want_to_designate_yes: Optional[str] = Field(None, description="Yes checkbox for third party designee")
    do_you_want_to_designate_yes_tag: Optional[str] = Field(None, description="PDF field tag for Yes checkbox")
    do_you_want_to_designate_no: Optional[str] = Field(None, description="No checkbox for third party designee")
    do_you_want_to_designate_no_tag: Optional[str] = Field(None, description="PDF field tag for No checkbox")
    desginee_name: Optional[str] = Field(None, description="Designee's name")
    desginee_name_tag: Optional[str] = Field(None, description="PDF field tag for designee's name")
    desginee_phone: Optional[str] = Field(None, description="Designee's phone number")
    desginee_phone_tag: Optional[str] = Field(None, description="PDF field tag for designee's phone number")
    desginee_pin: Optional[str] = Field(None, description="Designee's personal identification number (PIN)")
    desginee_pin_tag: Optional[str] = Field(None, description="PDF field tag for designee's PIN")

    @field_validator('do_you_want_to_designate_yes', 'do_you_want_to_designate_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/2"]:
            raise ValueError(f"Designee checkbox value must be '/1' or '/2', got '{v}'")
        return v

    @model_validator(mode='after')
    def validate_designee_selection(self):
        """Validate that exactly one designee option is selected."""
        yes_selected = self.do_you_want_to_designate_yes == "/1"
        no_selected = self.do_you_want_to_designate_no == "/2"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for third party designee")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for third party designee")
        
        # If Yes is selected, all designee information must be provided
        if yes_selected:
            missing_fields = []
            if not self.desginee_name:
                missing_fields.append("desginee_name")
            if not self.desginee_phone:
                missing_fields.append("desginee_phone")
            if not self.desginee_pin:
                missing_fields.append("desginee_pin")
                
            if missing_fields:
                raise ValueError(f"If 'Yes' is selected for third party designee, the following fields must be provided: {', '.join(missing_fields)}")
                
        return self


class SignHere(BaseModel):
    """Sign Here section of the 1040 form."""
    your_occupation: str = Field(..., description="Your occupation")
    your_occupation_tag: str = Field(..., description="PDF field tag for your occupation")
    your_pin: Optional[str] = Field(None, description="Your personal identification number (PIN)")
    your_pin_tag: Optional[str] = Field(None, description="PDF field tag for your PIN")
    spouse_occupation: Optional[str] = Field(None, description="Spouse's occupation")
    spouse_occupation_tag: Optional[str] = Field(None, description="PDF field tag for spouse's occupation")
    spouse_pin: Optional[str] = Field(None, description="Spouse's personal identification number (PIN)")
    spouse_pin_tag: Optional[str] = Field(None, description="PDF field tag for spouse's PIN")
    phone_no: str = Field(..., description="Your phone number")
    phone_no_tag: str = Field(..., description="PDF field tag for your phone number")
    email: Optional[str] = Field(None, description="Your email address")
    email_tag: Optional[str] = Field(None, description="PDF field tag for your email address")


class F1040Document(BaseModel):
    """Complete F1040 document structure."""
    configuration: F1040Configuration
    name_address_ssn: NameAddressSSN
    filing_status: FilingStatus
    digital_assets: DigitalAssets
    standard_deduction: StandardDeduction
    dependents: Optional[Dependents] = None
    income: Income
    tax_and_credits: TaxAndCredits
    payments: Payments
    refund: Optional[Refund] = None
    amount_you_owe: Optional[AmountYouOwe] = None
    third_party_designee: Optional[ThirdPartyDesignee] = None
    sign_here: SignHere

    @model_validator(mode='after')
    def validate_refund_amount_you_owe(self):
        """
        Validate that either Refund section or Amount You Owe section is used, but not both.
        The determination is based on the comparison of lines 33 and 24.
        """
        # We need to infer whether there should be a refund or amount owed
        # This should be calculated based on the relationship between payments (L33) and tax (L24)
        
        has_refund_section = self.refund is not None and self.refund.L34_subtract is not None
        has_amount_owed_section = self.amount_you_owe is not None and self.amount_you_owe.L37 is not None
        
        # We can't have both sections populated
        if has_refund_section and has_amount_owed_section and self.amount_you_owe.L37 != 0:
            raise ValueError("Cannot have both Refund and Amount You Owe sections populated - they are mutually exclusive")
        
        # We should have at least one section
        if not has_refund_section and not has_amount_owed_section:
            raise ValueError("Must have either Refund or Amount You Owe section populated")
            
        return self


def validate_F1040_file(file_path: str) -> F1040Document:
    """
    Validate a F1040 configuration file and return a validated F1040Document.
    
    Args:
        file_path (str): Path to the F1040 JSON configuration file
        
    Returns:
        F1040Document: Validated F1040 document
        
    Raises:
        ValueError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValidationError: If the JSON doesn't conform to the F1040Document schema
    """
    if not os.path.exists(file_path):
        raise ValueError(f"F1040 configuration file does not exist: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Parse and validate against our schema
    return F1040Document.model_validate(data)


# If the module is run directly, validate a file
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python F1040_validator.py <path_to_F1040_json>")
        sys.exit(1)
    
    try:
        file_path = sys.argv[1]
        validated_data = validate_F1040_file(file_path)
        print(f"✅ F1040 file validated successfully: {file_path}")
        print(f"Tax year: {validated_data.configuration.tax_year}")
        print(f"Taxpayer: {validated_data.name_address_ssn.first_name_middle_initial} {validated_data.name_address_ssn.last_name}")
        
        # Determine if there's a refund or amount owed
        if validated_data.refund and hasattr(validated_data.refund, 'L34_subtract_tag'):
            print(f"Refund expected")
        elif validated_data.amount_you_owe and validated_data.amount_you_owe.L37:
            print(f"Amount owed: {validated_data.amount_you_owe.L37}")
        else:
            print("Neither refund nor amount owed specified")
            
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        sys.exit(1)
