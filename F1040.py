# F1040 module for Open Tax Liberty
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Usage:
#   from F1040 import validate_F1040_file
#   validated_data = validate_F1040_file("path/to/your/f1040_config.json")
# or run directly from the command line:
#   python F1040_validator.py path/to/your/f1040_config.json

import os
import sys
import json
from typing import List, Dict, Any, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from W2 import validate_W2_json, W2Document, W2Entry, W2Configuration
from pathlib import Path
import tempfile
from tax_form_tags import tax_form_tags_dict

# PDF Imports used to create the PDF
from pypdf import PdfReader, PdfWriter
import pdf_utility

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
    last_name: str = Field(..., description="Last name")
    ssn: str = Field(..., description="Social Security Number")
    
    spouse_first_name_middle_inital: Optional[str] = Field(None, description="Spouse's first name and middle initial")
    spouse_last_name: Optional[str] = Field(None, description="Spouse's last name")
    spouse_ssn: Optional[str] = Field(None, description="Spouse's Social Security Number")
    
    home_address: str = Field(..., description="Home address")
    apartment_no: Optional[str] = Field(None, description="Apartment number")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    zip: str = Field(..., description="ZIP code")
    
    foreign_country_name: Optional[str] = Field(None, description="Foreign country name")
    foreign_country_province: Optional[str] = Field(None, description="Foreign province/state")
    foreign_country_postal_code: Optional[str] = Field(None, description="Foreign postal code")
    
    presidential_you: str = Field(..., description="Presidential campaign fund checkbox for you")
    presidential_spouse: Optional[str] = Field(None, description="Presidential campaign fund checkbox for spouse")

    @field_validator('presidential_you', 'presidential_spouse')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class FilingStatus(BaseModel):
    """Filing status section of the 1040 form."""
    single_or_HOH: str = Field(..., description="Single or head of household filing status")
    married_filing_jointly_or_QSS: str = Field(..., description="Married filing jointly or qualifying surviving spouse")
    married_filing_separately: str = Field(..., description="Married filing separately")
    treating_nonresident_alien: Optional[str] = Field(None, description="Nonresident alien spouse treated as resident")
    spouse_or_child_name: Optional[str] = Field(None, description="Spouse or qualifying child name")
    nonresident_alien_name: Optional[str] = Field(None, description="Nonresident alien spouse name")

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
    yes: str = Field("/Off", description="Digital assets checkbox value")
    no: str = Field("/Off", description="Digital assets checkbox value")
    
    @field_validator('yes')
    @classmethod
    def validate_digital_assets_value(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Digital assets value must be '/1' (Yes) or '/2' (No), got '{v}'")
        return v

    @field_validator('no')
    @classmethod
    def validate_digital_assets_value(cls, v):
        if v not in ["/2", "/Off"]:
            raise ValueError(f"Digital assets value must be '/1' (Yes) or '/2' (No), got '{v}'")
        return v


class StandardDeduction(BaseModel):
    """Standard deduction section of the 1040 form."""
    you_as_a_dependent: str = Field(..., description="Someone can claim you as a dependent")
    your_spouse_as_a_dependent: Optional[str] = Field(None, description="Someone can claim your spouse as a dependent")
    spouse_itemizes: Optional[str] = Field(None, description="Spouse itemizes on a separate return")
    born_before_jan_2_1960: str = Field(..., description="You were born before January 2, 1960")
    are_blind: str = Field(..., description="You are blind")
    spouse_born_before_jan_2_1960: Optional[str] = Field(None, description="Spouse was born before January 2, 1960")
    spouse_is_blind: Optional[str] = Field(None, description="Spouse is blind")

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
    
    # Dependent 1
    dependent_1_first_last_name: Optional[str] = Field(None, description="First dependent's name")
    dependent_1_ssn: Optional[str] = Field(None, description="First dependent's SSN")
    dependent_1_relationship: Optional[str] = Field(None, description="First dependent's relationship")
    dependent_1_child_tax_credit: Optional[str] = Field(None, description="First dependent's child tax credit")
    dependent_1_credit_for_other_dependents: Optional[str] = Field(None, description="First dependent's credit for other dependents")
    
    # Dependent 2
    dependent_2_first_last_name: Optional[str] = Field(None, description="Second dependent's name")
    dependent_2_ssn: Optional[str] = Field(None, description="Second dependent's SSN")
    dependent_2_relationship: Optional[str] = Field(None, description="Second dependent's relationship")
    dependent_2_child_tax_credit: Optional[str] = Field(None, description="Second dependent's child tax credit")
    dependent_2_credit_for_other_dependents: Optional[str] = Field(None, description="Second dependent's credit for other dependents")
    
    # Dependent 3
    dependent_3_first_last_name: Optional[str] = Field(None, description="Third dependent's name")
    dependent_3_ssn: Optional[str] = Field(None, description="Third dependent's SSN")
    dependent_3_relationship: Optional[str] = Field(None, description="Third dependent's relationship")
    dependent_3_child_tax_credit: Optional[str] = Field(None, description="Third dependent's child tax credit")
    dependent_3_credit_for_other_dependents: Optional[str] = Field(None, description="Third dependent's credit for other dependents")
    
    # Dependent 4
    dependent_4_first_last_name: Optional[str] = Field(None, description="Fourth dependent's name")
    dependent_4_ssn: Optional[str] = Field(None, description="Fourth dependent's SSN")
    dependent_4_relationship: Optional[str] = Field(None, description="Fourth dependent's relationship")
    dependent_4_child_tax_credit: Optional[str] = Field(None, description="Fourth dependent's child tax credit")
    dependent_4_credit_for_other_dependents: Optional[str] = Field(None, description="Fourth dependent's credit for other dependents")

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
                    f"dependent_{i}_relationship"
                ]
                
                for field in required_fields:
                    if not getattr(self, field):
                        raise ValueError(f"If dependent_{i}_first_last_name is provided, {field} must also be provided")
                        
        return self


class Income(BaseModel):
    """Income section of the 1040 form."""
    # Lines 1a-1i and 1z
    L1a: Union[str, Decimal] = Field(default="get_W2_box_1_sum()", description="Wages, salaries, tips, etc.")
    L1b: Decimal = Field(default=0, description="Household employee wages")
    L1c: Decimal = Field(default=0, description="Tip income")
    L1d: Decimal = Field(default=0, description="Medicaid waiver payments")
    L1e: Decimal = Field(default=0, description="Taxable dependent care benefits")
    L1f: Decimal = Field(default=0, description="Employer provided adoption benefits")
    L1g: Decimal = Field(default=0, description="Scholarship and fellowship grants")
    L1h: Decimal = Field(default=0, description="Pensions and annuities from Form 1099-R, Box 2a")
    L1i: Decimal = Field(default=0, description="Other earned income")
    L1z: Decimal = Field(0, description="List of fields to sum for line 1z")
    
    # Other income lines
    L2a: Decimal = Field(default=0, description="Tax-exempt interest")
    L2b: Decimal = Field(default=0, description="Taxable interest")
    L3a: Decimal = Field(default=0, description="Qualified dividends")
    L3b: Decimal = Field(default=0, description="Ordinary dividends")
    L4a: Decimal = Field(default=0, description="IRA distributions")
    L4b: Decimal = Field(default=0, description="Taxable IRA distributions")
    L5a: Decimal = Field(default=0, description="Pensions and annuities")
    L5b: Decimal = Field(default=0, description="Taxable pensions and annuities")
    L6a: Decimal = Field(default=0, description="Social security benefits")
    L6b: Decimal = Field(default=0, description="Taxable social security benefits")
    L6c: str = Field("/Off", description="Are you a retired public safety officer?")
    L7cb: str = Field("/Off", description="Capital gain or loss")
    L7: Decimal = Field(default=0, description="Capital gain or loss")
    L8: Decimal = Field(default=0, description="Other income")
    
    # Total income and adjusted gross income
    L9: Decimal = Field(default=0, description="Total income")
    L10: Decimal = Field(default=0, description="Adjustments to income")
    L11: Decimal = Field(default=0, description="Adjusted gross income")
    L12: Decimal = Field(default=0, description="Standard deduction or itemized deductions")
    L13: Decimal = Field(default=0, description="Qualified business income deduction")
    L14: Decimal = Field(default=0, description="Sum of standard deduction and QBI deduction")
    L15: Union[str, Decimal] = Field(default=0, description="Taxable income")

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
    L16_check_4972: Optional[str] = Field(None, description="Form 4972 checkbox")
    L16_check_3: Optional[str] = Field(None, description="Other checkbox")
    L16_check_3_field: Decimal = Field(default=Decimal('0'), description="Other tax forms amount")
    L16: Decimal = Field(default=Decimal('0'), description="Tax amount")
    L17: Decimal = Field(default=Decimal('0'), description="Amount from Schedule 2, line 3")
    L18: Decimal = Field(default=Decimal('0'), description="Sum of tax")
    L19: Decimal = Field(default=Decimal('0'), description="Child tax credit/credit for other dependents")
    L20: Decimal = Field(default=Decimal('0'), description="Amount from Schedule 3, line 8")
    L21: Decimal = Field(default=Decimal('0'), description="Sum of credits")
    L22: Union[str, Decimal] = Field(default=Decimal('0'), description="Subtract lines 21 from 18")
    L23: Decimal = Field(default=Decimal('0'), description="Other taxes from Schedule 2, line 21")
    L24: Union[str, Decimal] = Field(default=Decimal('0'), description="Sum of tax and additional taxes")
    
    @field_validator('L16_check_8814', 'L16_check_4972', 'L16_check_3')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class Payments(BaseModel):
    """Payments section of the 1040 form."""
    L25a: Union[str, Decimal] = Field(..., description="Federal income tax withheld from Forms W-2")
    L25b: Decimal = Field(default=Decimal('0'), description="Federal income tax withheld from Form 1099")
    L25c: Decimal = Field(default=Decimal('0'), description="Federal income tax withheld from other forms")
    L25d: Decimal = Field(default=Decimal('0'), description="Sum of lines 25a, 25b, and 25c")
    L26: Decimal = Field(default=Decimal('0'), description="Estimated tax payments")
    L27: Decimal = Field(default=Decimal('0'), description="Earned income credit (EIC)")
    L28: Decimal = Field(default=Decimal('0'), description="Additional child tax credit")
    L29: Decimal = Field(default=Decimal('0'), description="American opportunity credit")
    L31: Decimal = Field(default=Decimal('0'), description="Amount from Schedule 3, line 15")
    L32: Decimal = Field(default=Decimal('0'), description="List of fields to sum for line 32")
    L33: Decimal = Field(default=Decimal('0'), description="List of fields to sum for line 33")
    
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
    L34: Decimal = Field(default=Decimal('0'), description="Line 34 subtraction result")
    L35a_check: Optional[str] = Field(None, description="Amount applied to estimated tax")
    L35a: Decimal = Field(default=Decimal('0'), description="Line 35a sum result")
    L35a_b: Optional[str] = Field(None, description="Routing number for direct deposit")
    L35c_checking: Optional[str] = Field(None, description="Checking account checkbox")
    L35c_savings: Optional[str] = Field(None, description="Savings account checkbox")
    L35a_d: Optional[str] = Field(None, description="Account number for direct deposit")
    L36: Optional[Union[int, float, Decimal, str]] = Field(None, description="Amount you want applied to next year's estimated tax")

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
    L38: Optional[Union[int, float, Decimal]] = Field(None, description="Estimated tax penalty")


class ThirdPartyDesignee(BaseModel):
    """Third Party Designee section of the 1040 form."""
    do_you_want_to_designate_yes: Optional[str] = Field(None, description="Yes checkbox for third party designee")
    do_you_want_to_designate_no: Optional[str] = Field(None, description="No checkbox for third party designee")
    desginee_name: Optional[str] = Field(None, description="Designee's name")
    desginee_phone: Optional[str] = Field(None, description="Designee's phone number")
    desginee_pin: Optional[str] = Field(None, description="Designee's personal identification number (PIN)")

    @field_validator('do_you_want_to_designate_yes', 'do_you_want_to_designate_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/2", "/Off"]:
            raise ValueError(f"Designee checkbox value must be '/1' or '/2' or '/Off', got '{v}'")
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
    your_pin: Optional[str] = Field(None, description="Your personal identification number (PIN)")
    spouse_occupation: Optional[str] = Field(None, description="Spouse's occupation")
    spouse_pin: Optional[str] = Field(None, description="Spouse's personal identification number (PIN)")
    phone_no: str = Field(..., description="Your phone number")
    email: Optional[str] = Field(None, description="Your email address")


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

    @model_validator(mode='before')
    @classmethod
    def replace_W2_box_sums(cls, data):
        """replace W2 box sums with W2 data that is run in the validation functions."""
        if isinstance(data, dict) and not isinstance(data, BaseModel):
            # Process W2 function calls in the data
            if "income" in data and "L1a" in data["income"] and data["income"]["L1a"] == "get_W2_box_1_sum()":
                # If W2 box 1 sum is available in the data, use it
                if "W2_box_1_sum" in data:
                    data["income"]["L1a"] = data["W2_box_1_sum"]
                    data.pop("W2_box_1_sum", None)  # Explicitly remove the key
                    
            if "payments" in data and "L25a" in data["payments"] and data["payments"]["L25a"] == "get_W2_box_2_sum()":
                # If W2 box 2 sum is available in the data, use it
                if "W2_box_2_sum" in data:
                    data["payments"]["L25a"] = data["W2_box_2_sum"]
                    data.pop("W2_box_2_sum", None)  # Explicitly remove the key
        
        return data

    @model_validator(mode='after')
    def calculate_standard_deduction(self):
        """
        Calculate the standard deduction amount (line 12) based on filing status.
        This will only set line 12 if it's not already explicitly provided.
        
        Standard deduction amounts for 2024:
        - Single or Married Filing Separately: $14,600
        - Married Filing Jointly or Qualifying Surviving Spouse: $29,200
        - Head of Household: $21,900
        """
        # Only calculate if income section exists and has L12 field
        if hasattr(self, 'income') and hasattr(self.income, 'L12'):
            # Skip if L12 is already set to a non-zero value
            #if self.income.L12 and self.income.L12 != 0:
            #    return self
                
            # Determine standard deduction based on filing status
            filing_status = self.filing_status
            
            # Single or Married Filing Separately
            if filing_status.single_or_HOH == "/1" or filing_status.married_filing_separately == "/1":
                self.income.L12 = 14600
                
            # Married Filing Jointly or Qualifying Surviving Spouse
            elif filing_status.married_filing_jointly_or_QSS in ["/3", "/4"]:
                self.income.L12 = 29200
                
            # Head of Household
            elif filing_status.single_or_HOH == "/2":
                self.income.L12 = 21900
                
            # Add adjustments for age, blindness, and dependent status if applicable
            # These would need to be implemented based on tax rules
            
        return self

    @model_validator(mode='after')
    def calculate_income(self):
        """
        Calculate the income section of the F1040
        """
        if hasattr(self, 'income') and hasattr(self.income, 'L1z'):
            self.income.L1z = (self.income.L1a + self.income.L1b + self.income.L1c + 
                self.income.L1d + self.income.L1e + self.income.L1f + 
                self.income.L1g + self.income.L1h + self.income.L1i)
        
        if hasattr(self, 'income') and hasattr(self.income, 'L9'):
            self.income.L9 = (self.income.L1z + self.income.L2b + self.income.L3b + 
                self.income.L4b + self.income.L5b + self.income.L6b + 
                self.income.L7 + self.income.L8)

        if hasattr(self, 'income') and hasattr(self.income, 'L11'):
            self.income.L11 = self.income.L9 - self.income.L10

        if hasattr(self, 'income') and hasattr(self.income, 'L14'):
            self.income.L14 = self.income.L12 + self.income.L13

        if hasattr(self, 'income') and hasattr(self.income, 'L15'):
            self.income.L15 = self.income.L11 - self.income.L14
            if self.income.L15 <= 0:
                self.income.L15 = "-0-"

        return self

    @model_validator(mode='after')
    def calculate_tax_and_credits(self):
        """
        Calculate the Tax and Credits section of the F1040
        """
        if hasattr(self, 'tax_and_credits') and hasattr(self.tax_and_credits, 'L18'):
            self.tax_and_credits.L18 = (self.tax_and_credits.L16 + self.tax_and_credits.L17)
        
        if hasattr(self, 'tax_and_credits') and hasattr(self.tax_and_credits, 'L21'):
            self.tax_and_credits.L21 = (self.tax_and_credits.L19 + self.tax_and_credits.L20)

        if hasattr(self, 'tax_and_credits') and hasattr(self.tax_and_credits, 'L22'):
            self.tax_and_credits.L22 = self.tax_and_credits.L18 - self.tax_and_credits.L21
            if self.tax_and_credits.L22 <= 0:
                self.tax_and_credits.L22 = "-0-"

        if hasattr(self, 'tax_and_credits') and hasattr(self.tax_and_credits, 'L24'):
            if isinstance(self.tax_and_credits.L22, Decimal):
                self.tax_and_credits.L24 = self.tax_and_credits.L22 + self.tax_and_credits.L23
                if self.tax_and_credits.L24 <= 0:
                    self.tax_and_credits.L24 = "-0-"
            else:
                self.tax_and_credits.L24 = self.tax_and_credits.L23
                if self.tax_and_credits.L24 <= 0:
                    self.tax_and_credits.L24 = "-0-"

        return self

    @model_validator(mode='after')
    def calculate_payments(self):
        """
        Calculate the Payments section of the F1040
        """
        if hasattr(self, 'tax_and_credits') and hasattr(self.payments, 'L25d'):
            self.payments.L25d = (self.payments.L25a + self.payments.L25b +
                    self.payments.L25c)
        
        if hasattr(self, 'tax_and_credits') and hasattr(self.payments, 'L32'):
            self.payments.L32 = (self.payments.L27 + self.payments.L28 +
                self.payments.L29 + self.payments.L31)

        if hasattr(self, 'tax_and_credits') and hasattr(self.payments, 'L33'):
            self.payments.L33 = (self.payments.L25d + self.payments.L26 +
                self.payments.L32)

        return self

    @model_validator(mode='after')
    def calculate_refund(self):
        """
        Calculate the Redund section of the F1040
        """
        if hasattr(self, 'tax_and_credits') and hasattr(self.refund, 'L34'):
            if isinstance(self.payments.L33, Decimal) and isinstance(self.tax_and_credits.L24, Decimal):
                self.refund.L34 = self.payments.L33 - self.tax_and_credits.L24 
            elif isinstance(self.tax_and_credits.L24, str):
                self.refund.L34 = self.payments.L33
        
        if hasattr(self, 'tax_and_credits') and hasattr(self.refund, 'L35a'):
            self.refund.L35a = self.refund.L34

        return self

    @model_validator(mode='after')
    def validate_refund_amount_you_owe(self):
        """
        Validate that either Refund section or Amount You Owe section is used, but not both.
        The determination is based on the comparison of lines 33 and 24.
        """
        # We need to infer whether there should be a refund or amount owed
        # This should be calculated based on the relationship between payments (L33) and tax (L24)
        
        has_refund_section = self.refund is not None and self.refund.L34 is not None
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
    Validate a Open Tax Liberty configuration file and return a validated F1040Document.
    
    Args:
        file_path (str): Path to the Open Tax Liberty JSON configuration file
        
    Returns:
        F1040Document: Validated F1040 document
        
    Raises:
        ValueError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValidationError: If the JSON doesn't conform to the F1040Document schema
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Open Tax Liberty configuration file does not exist: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
   
    # first we have to acquire the W2 data using the W2_validator.py 
    # this will compute the totals for box_1 and box_2 on all W2 in the global configuration file
    if "W2" not in data:                                                   
        raise ValueError(f"Open Tax Liberty configration file has no W2 section!")
    W2_json_data = data["W2"]
    W2_doc = validate_W2_json(W2_json_data) 

    if "F1040" not in data:                                                   
        raise ValueError(f"Open Tax Liberty configration file has no F1040 section!")
    F1040_data = data["F1040"] 
    # Add the W2 box sums directly to the F1040 data
    F1040_data["W2_box_1_sum"] = W2_doc.totals["total_box_1"]
    F1040_data["W2_box_2_sum"] = W2_doc.totals["total_box_2"]

    # Parse and validate against our schema, passing the context which includes the W2 Boxes Totals
    return F1040Document.model_validate(F1040_data)

def create_F1040_pdf(F1040_doc: F1040Document, template_F1040_pdf_path: str, output_F1040_pdf_path: str):
    """
    create a F1040 PDF form 
    
    Args:
        F1040_doc (F1040Document): validated F1040Document
        template_F1040_pdf_path (str): path to the PDF template
        output_F1040_pdf_path (str): path to the output pdf file

    Returns:
        nothing
        
    Raises:
        ValueError: If the template_F1040_pdf file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValidationError: If the JSON doesn't conform to the F1040Document schema
    """
    if not os.path.exists(template_F1040_pdf_path):
        raise ValueError(f"Open Tax Liberty template F1040 pdf file does not exist: {template_F1040_pdf_path}")

    # Validate output path
    output_path = Path(output_F1040_pdf_path)
    
    # Check parent directory exists
    parent_dir = output_path.parent
    if not parent_dir.exists():
        raise ValueError(f"Output directory does not exist: {parent_dir}")
    
    # Check parent directory is writable
    if not os.access(parent_dir, os.W_OK):
        raise ValueError(f"Output directory is not writable: {parent_dir}")
    
    # Validate file extension
    if output_path.suffix.lower() != '.pdf':
        raise ValueError(f"Output file must have a .pdf extension: {output_F1040_pdf_path}")
    
    # Try to create a test file to ensure we can write to this location
    try:
        with tempfile.NamedTemporaryFile(dir=parent_dir, delete=True) as tmp:
            # If this succeeds, we have write permissions
            pass
    except (OSError, PermissionError) as e:
        raise ValueError(f"Cannot write to output directory {parent_dir}: {str(e)}")

    # setup the PdfWriter.....first we have to read the template
    reader = PdfReader(template_F1040_pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    F1040_dict = F1040_data.model_dump()  # this converts F1040_data into a dict

    for key in F1040_dict:
        if key == "configuration":
            continue
            
        # Check for simple value/tag pairs
        #if 'tag' in input_json_data[key] and 'value' in input_json_data[key]:
        #    write_field_pdf(writer, input_json_data[key]['tag'], input_json_data[key]['value'])
            
        # Process any additional sub-keys that have corresponding tag fields
        for sub_key, sub_value in F1040_dict[key].items():
            # Skip special keys
            # we skip the _tag because we use that information within the operations below
            if sub_key == '_comment' in sub_key:
                continue
            else:
                tag_key = f"{sub_key}_tag"
                if tag_key in tax_form_tags_dict["F1040"][key]:
                    write_field_pdf(writer, tax_form_tags_dict["F1040"][key][tag_key], sub_value)
                else:
                    raise ValueError(f"Cannot find tag_key: {tag_key} in tax_form_tags_dict") 

    # now save the PDF
    with open(output_F1040_pdf_path, "wb") as output_stream:                          
        writer.write(output_stream)


# If the module is run directly, validate the config file, then create the F1040 PDF file
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python F1040_validator.py <path_to_F1040_json> <path_to_template_F1040_pdf> <output_F1040_pdf_path>")
        sys.exit(1)
    
    # Add stack trace for debugging
    import traceback
    stack_trace = traceback.format_stack()
    print("Stack trace at F1040.py main execution:")
    for line in stack_trace:
        print(line.strip())
    
    try:
        json_file_path = sys.argv[1]
        validated_data = validate_F1040_file(json_file_path)
        print(validated_data.model_dump_json(indent=2))
        print(f"✅ F1040 file validated successfully: {json_file_path}")
        print(f"Tax year: {validated_data.configuration.tax_year}")
        print(f"Taxpayer: {validated_data.name_address_ssn.first_name_middle_initial} {validated_data.name_address_ssn.last_name}")
        
        # Determine if there's a refund or amount owed
        if validated_data.refund and hasattr(validated_data.refund, 'L34_subtract_tag'):
            print(f"Refund expected")
        elif validated_data.amount_you_owe and validated_data.amount_you_owe.L37:
            print(f"Amount owed: {validated_data.amount_you_owe.L37}")
        else:
            print("Neither refund nor amount owed specified")

        create_F1040_pdf(validated_data, sys.argv[1], sys.argv[2])
            
    except Exception as e:
        print(f"❌ Validation and Create failed: {str(e)}")
        print("Detailed error traceback:")
        traceback.print_exc()
        sys.exit(1)
