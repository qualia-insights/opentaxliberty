# F1040sc module for Open Tax Liberty - Schedule C (Profit or Loss From Business)
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Usage:
#   from F1040sc import validate_F1040sc_file
#   validated_data = validate_F1040sc_file("path/to/your/f1040sc_config.json")
# or run directly from the command line:
#   python F1040sc.py --help

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional, Union, Literal
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import tempfile
from datetime import datetime

# PDF Imports used to create the PDF
from pypdf import PdfReader, PdfWriter
from pdf_utility import write_field_pdf

class F1040scConfiguration(BaseModel):
    """Configuration section for the F1040 Schedule C form."""
    tax_year: int = Field(..., description="Tax year for the Schedule C form")
    form: str = Field(..., description="Form type, must be 'F1040SC'")
    output_file_name: str = Field(..., description="Output PDF file name")
    debug_json_output: Optional[str] = Field(None, description="Path to save debug JSON output")

    @field_validator('form')
    @classmethod
    def validate_form_type(cls, v):
        if v != "F1040SC":
            raise ValueError(f"Form type must be 'F1040SC', got '{v}'")
        return v

    @field_validator('tax_year')
    @classmethod
    def validate_tax_year(cls, v):
        current_year = 2025  # You might want to fetch this dynamically
        if v < 2020 or v > current_year:
            raise ValueError(f"Tax year must be between 2020 and {current_year}, got {v}")
        return v


class BusinessInformation(BaseModel):
    """Business information section of Schedule C."""
    business_name: str = Field(..., description="Name of proprietor")
    ssn: Optional[str] = Field(None, description="SSN")
    principal_business: Optional[str] = Field(None, description="Principal business")
    business_code: Optional[str] = Field(None, description="Business code")
    business_name_separate: Optional[str] = Field(None, description="Business name (if different)")
    ein: Optional[str] = Field(None, description="Employer ID number (EIN)")
    business_address: str = Field(..., description="Business address (street)")
    business_city_state_zip: str = Field(..., description="Business address (city, state, ZIP)")
    accounting_method_cash: str = Field("/Off", description="Cash accounting method checkbox")
    accounting_method_accrual: str = Field("/Off", description="Accrual accounting method checkbox")
    accounting_method_other: str = Field("/Off", description="Other accounting method checkbox")
    accounting_method_other_text: Optional[str] = Field(None, description="Other accounting method description")
    material_participation_yes: str = Field("/Yes", description="Yes checkbox for material participation")
    material_participation_no: str = Field("/Off", description="No checkbox for material participation")
    not_started_business: str = Field("/Off", description="Not started business checkbox")
    issued_1099_required_yes: str = Field("/Off", description="Yes checkbox for issued 1099s when required")
    issued_1099_required_no: str = Field("/Off", description="No checkbox for issued 1099s when required")
    issued_1099_not_required_yes: str = Field("/Off", description="Yes checkbox for required to file 1099s")
    issued_1099_not_required_no: str = Field("/Off", description="No checkbox for required to file 1099s")

    @field_validator('accounting_method_cash')
    @classmethod
    def validate_checkbox_1_or_off(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked): got '{v}'")
        return v

    @field_validator('accounting_method_accrual')
    @classmethod
    def validate_checkbox_2_or_off(cls, v):
        if v not in ["/2", "/Off"]:
            raise ValueError(f"Checkbox value must be '/2' (checked) or '/Off' (unchecked): got '{v}'")
        return v

    @field_validator('accounting_method_other')
    @classmethod
    def validate_checkbox_3_or_off(cls, v):
        if v not in ["/3", "/Off"]:
            raise ValueError(f"Checkbox value must be '/3' (checked) or '/Off' (unchecked): got '{v}'")
        return v

    @field_validator('not_started_business', 
                    'material_participation_yes', 'material_participation_no',
                    'issued_1099_required_yes', 'issued_1099_required_no',
                    'issued_1099_not_required_yes', 'issued_1099_not_required_no')
    @classmethod
    def validate_checkbox_yes_off_no(cls, v):
        if v not in ["/Yes", "/Off", "/No"]:
            raise ValueError(f"Checkbox value must be '/Yes' (checked) or '/Off' (unchecked), or '/No': got '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_accounting_method(self):
        """Validate that exactly one accounting method is selected."""
        methods = [
            (self.accounting_method_cash, "cash"),
            (self.accounting_method_accrual, "accrual"),
            (self.accounting_method_other, "other")
        ]
        
        selected_methods = [name for method, name in methods if method == "/1"]
        
        if len(selected_methods) != 1:
            raise ValueError(f"Exactly one accounting method must be selected, found {len(selected_methods)}: {selected_methods}")
        
        # If "Other" is selected, the description must be provided
        if self.accounting_method_other == "/1" and not self.accounting_method_other_text:
            raise ValueError("If 'Other' accounting method is selected, description must be provided")
            
        return self
    ''' 
    @model_validator(mode='after')
    def validate_material_participation(self):
        """Validate that exactly one material participation option is selected."""
        yes_selected = self.material_participation_yes == "/Yes"
        no_selected = self.material_participation_no == "/No"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for material participation")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for material participation")
            
        return self
    
    @model_validator(mode='after')
    def validate_1099_required(self):
        """Validate that exactly one option is selected for required 1099 issuance."""
        yes_selected = self.issued_1099_required_yes == "/1"
        no_selected = self.issued_1099_required_no == "/1"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for issuing required 1099s")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for issuing required 1099s")
            
        return self
    
    @model_validator(mode='after')
    def validate_1099_not_required(self):
        """Validate that exactly one option is selected for 1099 filing requirement."""
        yes_selected = self.issued_1099_not_required_yes == "/1"
        no_selected = self.issued_1099_not_required_no == "/1"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for 1099 filing requirement")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for 1099 filing requirement")
            
        return self
     '''


class Income(BaseModel):
    """Income section of Schedule C."""
    statutory_employee: Optional[str] = Field("/Off", description="Statutory employee checkbox")
    L1: Decimal = Field(default=Decimal('0'), description="Gross receipts or sales")
    L2: Decimal = Field(default=Decimal('0'), description="Returns and allowances")
    L3: Decimal = Field(default=Decimal('0'), description="Subtract line 2 from line 1")
    L4: Decimal = Field(default=Decimal('0'), description="Cost of goods sold")
    L5: Decimal = Field(default=Decimal('0'), description="Gross profit")
    L6: Decimal = Field(default=Decimal('0'), description="Other business income")
    L7: Decimal = Field(default=Decimal('0'), description="Gross income")

    @field_validator('statutory_employee')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    @model_validator(mode='after')
    def calculate_income(self):
        """Calculate income fields."""
        self.L3 = self.L1 - self.L2
        self.L5 = self.L3 - self.L4
        self.L7 = self.L5 + self.L6
        return self


class Expenses(BaseModel):
    """Expenses section of Schedule C."""
    L8: Decimal = Field(default=Decimal('0'), description="Advertising")
    L9: Decimal = Field(default=Decimal('0'), description="Car and truck expenses")
    L10: Decimal = Field(default=Decimal('0'), description="Commissions and fees")
    L11: Decimal = Field(default=Decimal('0'), description="Contract labor")
    L12: Decimal = Field(default=Decimal('0'), description="Depletion")
    L13: Decimal = Field(default=Decimal('0'), description="Depreciation")
    L14: Decimal = Field(default=Decimal('0'), description="Employee benefit programs")
    L15: Decimal = Field(default=Decimal('0'), description="Insurance (other than health)")
    L16a: Decimal = Field(default=Decimal('0'), description="Interest on mortgage")
    L16b: Decimal = Field(default=Decimal('0'), description="Interest - other")
    L17: Decimal = Field(default=Decimal('0'), description="Legal and professional services")
    L18: Decimal = Field(default=Decimal('0'), description="Office expense")
    L19: Decimal = Field(default=Decimal('0'), description="Pension and profit-sharing plans")
    L20a: Decimal = Field(default=Decimal('0'), description="Rent/lease - vehicles, machinery, equipment")
    L20b: Decimal = Field(default=Decimal('0'), description="Rent/lease - other business property")
    L21: Decimal = Field(default=Decimal('0'), description="Repairs and maintenance")
    L22: Decimal = Field(default=Decimal('0'), description="Supplies")
    L23: Decimal = Field(default=Decimal('0'), description="Taxes and licenses")
    L24a: Decimal = Field(default=Decimal('0'), description="Travel")
    L24b: Decimal = Field(default=Decimal('0'), description="Deductible meals")
    L25: Decimal = Field(default=Decimal('0'), description="Utilities")
    L26: Decimal = Field(default=Decimal('0'), description="Wages")
    L27a: Decimal = Field(default=Decimal('0'), description="Other expenses")
    L27b: Decimal = Field(default=Decimal('0'), description="Energy efficient buildings")
    L28: Decimal = Field(default=Decimal('0'), description="Total expenses")
    L29: Decimal = Field(default=Decimal('0'), description="Tentative profit/loss")


class HomeOfficeInformation(BaseModel):
    """Home Office Information section of Schedule C."""
    simplified_method: Optional[str] = Field(None, description="Checkbox for simplified method")
    home_total_area: Optional[str] = Field(None, description="Total square footage of home")
    home_business_area: Optional[str] = Field(None, description="Business square footage")
    L30: Optional[Decimal] = Field(None, description="Home office deduction")

    @field_validator('simplified_method')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class NetProfitLoss(BaseModel):
    """Net Profit or Loss section of Schedule C."""
    L31: Decimal = Field(default=Decimal('0'), description="Net profit or loss")
    L32a: Optional[str] = Field(None, description="All investment at risk")
    L32b: Optional[str] = Field(None, description="Some investment not at risk")

    @field_validator('L32a', 'L32b')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v


class CostOfGoodsSold(BaseModel):
    """Cost of Goods Sold section of Schedule C."""
    L33a: str = Field("/Off", description="Cost method checkbox")
    L33b: str = Field("/Off", description="Lower of cost or market method checkbox")
    L33c: str = Field("/Off", description="Other method checkbox")
    L34_yes: str = Field("/Off", description="Inventory change Yes")
    L34_no: str = Field("/Off", description="Inventory change No")
    L35: Decimal = Field(default=Decimal('0'), description="Beginning inventory")
    L36: Decimal = Field(default=Decimal('0'), description="Purchases")
    L37: Decimal = Field(default=Decimal('0'), description="Cost of labor")
    L38: Decimal = Field(default=Decimal('0'), description="Materials and supplies")
    L39: Decimal = Field(default=Decimal('0'), description="Other costs")
    L40: Decimal = Field(default=Decimal('0'), description="Sum lines 35-39")
    L41: Decimal = Field(default=Decimal('0'), description="Ending inventory")
    L42: Decimal = Field(default=Decimal('0'), description="Cost of goods sold")

    @field_validator('L33a', 'L33b', 'L33c',
                    'L34_yes', 'L34_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_method(self):
        """Validate that exactly one valuation method is selected."""
        methods = [
            (self.L33a, "cost"),
            (self.L33b, "lower of cost or market"),
            (self.L33c, "other")
        ]
        
        selected_methods = [name for method, name in methods if method == "/1"]
        
        if len(selected_methods) != 1:
            raise ValueError(f"Exactly one valuation method must be selected, found {len(selected_methods)}: {selected_methods}")
            
        return self
    
    @model_validator(mode='after')
    def validate_inventory_change(self):
        """Validate that exactly one inventory change option is selected."""
        yes_selected = self.L34_yes == "/1"
        no_selected = self.L34_no == "/1"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for inventory change")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for inventory change")
            
        return self
    
    @model_validator(mode='after')
    def calculate_totals(self):
        """Calculate total cost of goods sold."""
        self.L40 = self.L35 + self.L36 + self.L37 + self.L38 + self.L39
        self.L42 = self.L40 - self.L41
        return self


class VehicleInformation(BaseModel):
    """Vehicle Information section of Schedule C."""
    L43_month: Optional[str] = Field(None, description="Vehicle service date")
    L43_day: Optional[str] = Field(None, description="Vehicle service date")
    L43_year: Optional[str] = Field(None, description="Vehicle service date")
    L44a: Optional[Decimal] = Field(None, description="Business miles")
    L44b: Optional[Decimal] = Field(None, description="Commuting miles")
    L44c: Optional[Decimal] = Field(None, description="Other miles")
    L45_yes: Optional[str] = Field(None, description="Personal use Yes")
    L45_no: Optional[str] = Field(None, description="Personal use No")
    L46_yes: Optional[str] = Field(None, description="Another vehicle Yes")
    L46_no: Optional[str] = Field(None, description="Another vehicle No")
    L47a_yes: Optional[str] = Field(None, description="Evidence Yes")
    L47a_no: Optional[str] = Field(None, description="Evidence No")
    L47b_yes: Optional[str] = Field(None, description="Written evidence Yes")
    L47b_no: Optional[str] = Field(None, description="Written evidence No")

    @field_validator('L45_yes', 'L46_yes', 'L47a_yes', 'L47b_yes')
    @classmethod
    def validate_checkbox_yes(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Yes checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    @field_validator('L45_no', 'L46_no', 'L47a_no', 'L47b_no')
    @classmethod
    def validate_checkbox_no(cls, v):
        if v is not None and v not in ["/2", "/Off"]:
            raise ValueError(f"No checkbox value must be '/2' (checked) or '/Off' (unchecked), got '{v}'")
        return v

    def _validate_date(self, month, day, year):
        """Helper method to validate that the date components form a valid date."""
        try:
            # Clean up the input - strip any non-digit characters
            month_clean = ''.join(c for c in month if c.isdigit())
            day_clean = ''.join(c for c in day if c.isdigit())
            year_clean = ''.join(c for c in year if c.isdigit())
            
            # Convert to integers
            month_int = int(month_clean)
            day_int = int(day_clean)
            
            # Handle 2-digit years (assuming 20xx if < 50, 19xx if >= 50)
            if len(year_clean) == 2:
                year_int = 2000 + int(year_clean) if int(year_clean) < 50 else 1900 + int(year_clean)
            else:
                year_int = int(year_clean)
            
            # Attempt to create a datetime object
            datetime(year_int, month_int, day_int)
            
            # Also check for reasonable range (e.g., not in the future)
            current_year = datetime.now().year
            if year_int > current_year:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @model_validator(mode='after')
    def validate_vehicle_information(self):
        """Validate that vehicle information is consistent."""
        # If any vehicle information is provided, validate all required fields
        has_vehicle_info = any([
            self.L43_month,
            self.L43_day,
            self.L43_year,
            self.L44a is not None,
            self.L44b is not None,
            self.L44c is not None
        ])
        
        if has_vehicle_info:
            missing_fields = []
            
            if not self.L43_month:
                missing_fields.append("L43_month")

            if not self.L43_day:
                missing_fields.append("L43_day")

            if not self.L43_year:
                missing_fields.append("L43_year")
            
            if self.L44a is None:
                missing_fields.append("L44a")
            
            if self.L44b is None:
                missing_fields.append("L44b")
            
            if self.L44c is None:
                missing_fields.append("L44c")
            
            if missing_fields:
                raise ValueError(f"If any vehicle information is provided, the following fields must also be provided: {', '.join(missing_fields)}")
            
            # Validate yes/no pairs
            if not self._validate_yes_no_pair(self.L45_yes, self.L45_no, "vehicle personal use"):
                raise ValueError("Must select either Yes or No for vehicle personal use")
            
            if not self._validate_yes_no_pair(self.L46_yes, self.L46_no, "another vehicle"):
                raise ValueError("Must select either Yes or No for another vehicle")
            
            if not self._validate_yes_no_pair(self.L47a_yes, self.L47a_no, "evidence"):
                raise ValueError("Must select either Yes or No for evidence")
            
            if not self._validate_yes_no_pair(self.L47b_yes, self.L47b_no, "written evidence"):
                raise ValueError("Must select either Yes or No for written evidence")

            # Validate that the date is valid
            if self.L43_month and self.L43_day and self.L43_year:
                if not self._validate_date(self.L43_month, self.L43_day, self.L43_year):
                    raise ValueError(f"Invalid date: {self.L43_month}/{self.L43_day}/{self.L43_year}")
        
        return self
    
    def _validate_yes_no_pair(self, yes_value, no_value, field_name):
        """Helper to validate yes/no pairs."""
        if yes_value is None and no_value is None:
            return False
        
        yes_selected = yes_value == "/1"
        no_selected = no_value == "/2"
        
        if yes_selected and no_selected:
            raise ValueError(f"Cannot select both Yes and No for {field_name}")
        
        if not (yes_selected or no_selected):
            return False
        
        return True


class OtherExpenses(BaseModel):
    """Other expenses section of Schedule C."""
    other_expense_1_desc: Optional[str] = Field(None, description="Expense 1 description")
    other_expense_1_amount: Optional[Decimal] = Field(None, description="Expense 1 amount")
    other_expense_2_desc: Optional[str] = Field(None, description="Expense 2 description")
    other_expense_2_amount: Optional[Decimal] = Field(None, description="Expense 2 amount")
    other_expense_3_desc: Optional[str] = Field(None, description="Expense 3 description")
    other_expense_3_amount: Optional[Decimal] = Field(None, description="Expense 3 amount")
    other_expense_4_desc: Optional[str] = Field(None, description="Expense 4 description")
    other_expense_4_amount: Optional[Decimal] = Field(None, description="Expense 4 amount")
    other_expense_5_desc: Optional[str] = Field(None, description="Expense 5 description")
    other_expense_5_amount: Optional[Decimal] = Field(None, description="Expense 5 amount")
    other_expense_6_desc: Optional[str] = Field(None, description="Expense 6 description")
    other_expense_6_amount: Optional[Decimal] = Field(None, description="Expense 6 amount")
    other_expense_7_desc: Optional[str] = Field(None, description="Expense 7 description")
    other_expense_7_amount: Optional[Decimal] = Field(None, description="Expense 7 amount")
    other_expense_8_desc: Optional[str] = Field(None, description="Expense 8 description")
    other_expense_8_amount: Optional[Decimal] = Field(None, description="Expense 8 amount")
    other_expense_9_desc: Optional[str] = Field(None, description="Expense 9 description")
    other_expense_9_amount: Optional[Decimal] = Field(None, description="Expense 9 amount")
    L48: Decimal = Field(default=Decimal('0'), description="Total other expenses")
    
    @model_validator(mode='after')
    def calculate_total(self):
        """Calculate the total of all other expenses."""
        total = Decimal('0')
        for i in range(1, 10):
            amount = getattr(self, f"other_expense_{i}_amount", None)
            if amount is not None:
                total += amount
        self.L48 = total
        return self


class F1040scDocument(BaseModel):
    """Complete F1040 Schedule C document structure."""
    configuration: F1040scConfiguration
    business_information: BusinessInformation
    income: Income
    expenses: Expenses
    home_office: Optional[HomeOfficeInformation] = None
    net_profit_loss: Optional[NetProfitLoss] = None
    cost_of_goods_sold: Optional[CostOfGoodsSold] = None
    vehicle_information: Optional[VehicleInformation] = None
    other_expenses: Optional[OtherExpenses] = None
    
    @model_validator(mode='after')
    def calculate_all_totals(self):
        """Calculate all totals throughout the document."""
        # Calculate total expenses
        total_expenses = sum([
            self.expenses.L8,
            self.expenses.L9,
            self.expenses.L10,
            self.expenses.L11,
            self.expenses.L12,
            self.expenses.L13,
            self.expenses.L14,
            self.expenses.L15,
            self.expenses.L16a,
            self.expenses.L16b,
            self.expenses.L17,
            self.expenses.L18,
            self.expenses.L19,
            self.expenses.L20a,
            self.expenses.L20b,
            self.expenses.L21,
            self.expenses.L22,
            self.expenses.L23,
            self.expenses.L24a,
            self.expenses.L24b,
            self.expenses.L25,
            self.expenses.L26,
            self.expenses.L27a,
            self.expenses.L27b
        ])
        
        self.expenses.L28 = total_expenses
        
        # Calculate tentative profit/loss
        self.expenses.L29 = self.income.L7 - total_expenses
        
        # Initialize or update net_profit_loss
        if self.net_profit_loss is None:
            self.net_profit_loss = NetProfitLoss()
        
        # Calculate final net profit/loss
        home_office_deduction = Decimal('0')
        if self.home_office and self.home_office.L30 is not None:
            home_office_deduction = self.home_office.L30
        
        self.net_profit_loss.L31 = self.expenses.L29 - home_office_deduction
        
        # Calculate cost of goods sold if provided
        if self.cost_of_goods_sold is not None:
            self.income.L4 = self.cost_of_goods_sold.L42
            # Recalculate income after updating cost of goods sold
            self.income = self.income.calculate_income()
        
        # REMOVE THIS RECURSIVE CALL
        # Calculate other expenses total if provided
        # if self.other_expenses is not None:
        #     self.expenses.L27a = self.other_expenses.L48
        #     # Recalculate expenses after updating other expenses
        #     self.calculate_all_totals()  # THIS IS THE PROBLEM - RECURSIVE CALL

        # For other expenses, just set L27a once
        if self.other_expenses is not None:
            self.expenses.L27a = self.other_expenses.L48
            # Don't call self.calculate_all_totals() again!
        
        return self

# Add this helper function before the main function
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float
        return super().default(obj)


def validate_F1040sc_file(file_path: str) -> F1040scDocument:
    """
    Validate a Schedule C configuration file and return a validated F1040scDocument.
    
    Args:
        file_path (str): Path to the Schedule C JSON configuration file
        
    Returns:
        F1040scDocument: Validated Schedule C document
        
    Raises:
        ValueError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValidationError: If the JSON doesn't conform to the F1040scDocument schema
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Schedule C configuration file does not exist: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
   
    if "F1040SC" not in data:                                                   
        raise ValueError(f"Configuration file has no F1040SC section!")
    
    F1040sc_data = data["F1040SC"] 

    # Parse and validate against our schema
    return F1040scDocument.model_validate(F1040sc_data)


def create_F1040sc_pdf(F1040sc_doc: F1040scDocument, template_F1040sc_pdf_path: str, output_F1040sc_pdf_path: str):
    """
    Create a Schedule C PDF form 
    
    Args:
        F1040sc_doc (F1040scDocument): validated F1040scDocument
        template_F1040sc_pdf_path (str): path to the PDF template
        output_F1040sc_pdf_path (str): path to the output pdf file

    Returns:
        nothing
        
    Raises:
        ValueError: If the template_F1040sc_pdf file doesn't exist
    """
    if not os.path.exists(template_F1040sc_pdf_path):
        raise ValueError(f"Schedule C template PDF file does not exist: {template_F1040sc_pdf_path}")

    # Validate output path
    output_path = Path(output_F1040sc_pdf_path)
    
    # Check parent directory exists
    parent_dir = output_path.parent
    if not parent_dir.exists():
        raise ValueError(f"Output directory does not exist: {parent_dir}")
    
    # Check parent directory is writable
    if not os.access(parent_dir, os.W_OK):
        raise ValueError(f"Output directory is not writable: {parent_dir}")
    
    # Validate file extension
    if output_path.suffix.lower() != '.pdf':
        raise ValueError(f"Output file must have a .pdf extension: {output_F1040sc_pdf_path}")
    
    # Try to create a test file to ensure we can write to this location
    try:
        with tempfile.NamedTemporaryFile(dir=parent_dir, delete=True) as tmp:
            # If this succeeds, we have write permissions
            pass
    except (OSError, PermissionError) as e:
        raise ValueError(f"Cannot write to output directory {parent_dir}: {str(e)}")

    # setup the PdfWriter.....first we have to read the template
    reader = PdfReader(template_F1040sc_pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    # Import tax_form_tags_dict here to avoid circular imports
    try:
        from tax_form_tags import tax_form_tags_dict
        
        F1040sc_dict = F1040sc_doc.model_dump()

        for key in F1040sc_dict:
            if key == "configuration":
                continue

            # Skip None values
            if F1040sc_dict[key] is None:
                continue
                
            # Process any additional sub-keys that have corresponding tag fields
            for sub_key, sub_value in F1040sc_dict[key].items():
                # Skip special keys
                if '_comment' in sub_key:
                    continue
                else:
                    tag_key = f"{sub_key}_tag"
                    # if tag_key in tax_form_tags_dict["F1040SC"][key]:
                    if key in tax_form_tags_dict["F1040SC"] and tag_key in tax_form_tags_dict["F1040SC"][key]:
                        write_field_pdf(writer, tax_form_tags_dict["F1040SC"][key][tag_key], sub_value)
                    else:
                        print(f"Warning: Cannot find tag_key: {tag_key} in tax_form_tags_dict")
    except (ImportError, KeyError) as e:
        print(f"Warning: Error mapping PDF fields: {str(e)}")
        print("PDF field mapping not yet fully implemented for Schedule C")
        print("You'll need to ensure Schedule C tags are properly defined in tax_form_tags.py dictionary")

    # now save the PDF
    with open(output_F1040sc_pdf_path, "wb") as output_stream:                          
        writer.write(output_stream)


def save_debug_json(F1040sc_doc: F1040scDocument, debug_json_path: Optional[str] = None):
    """
    Save F1040scDocument as JSON for debugging purposes.
    
    Args:
        F1040sc_doc (F1040scDocument): The F1040scDocument to save
        debug_json_path (str, optional): Path where to save the JSON. If None, uses the path from the configuration
    """
    if debug_json_path is None and F1040sc_doc.configuration.debug_json_output:
        debug_json_path = F1040sc_doc.configuration.debug_json_output
        
    if debug_json_path:
        with open(debug_json_path, 'w') as file:
            json.dump(F1040sc_doc.model_dump(), file, indent=4, cls=DecimalEncoder)


def main():
    """Main function to process Schedule C form using command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate Schedule C (Profit or Loss From Business) tax form data and create a filled in Schedule C PDF."
    )
    
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to the Schedule C JSON configuration file"
    )
    
    parser.add_argument(
        "--template", 
        required=True,
        help="Path to the blank Schedule C PDF template"
    )
    
    parser.add_argument(
        "--output", 
        required=True,
        help="Path where to save the output filled Schedule C PDF"
    )
    
    parser.add_argument(
        "--debug-json", 
        help="Path where to save debug JSON output (overrides the path in config file)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Show stack trace for debugging if verbose
    if args.verbose:
        import traceback
        stack_trace = traceback.format_stack()
        print("Stack trace at F1040sc.py main execution:")
        for line in stack_trace:
            print(line.strip())
    
    try:
        # Validate the Schedule C data
        validated_data = validate_F1040sc_file(args.config)
        
        if args.verbose:
            print(validated_data.model_dump_json(indent=2))
            
        print(f"✅ Schedule C file validated successfully: {args.config}")
        print(f"Tax year: {validated_data.configuration.tax_year}")
        print(f"Business: {validated_data.business_information.business_name}")
        print(f"Net profit/loss: {validated_data.net_profit_loss.L31}")
        
        # Create the Schedule C PDF
        print(f"Creating PDF at {args.output}...")
        create_F1040sc_pdf(validated_data, args.template, args.output)
        print(f"✅ Schedule C PDF created successfully: {args.output}")
        
        # Save debug JSON if requested
        if args.debug_json:
            save_debug_json(validated_data, args.debug_json)
            print(f"Debug JSON saved to: {args.debug_json}")
        elif validated_data.configuration.debug_json_output:
            save_debug_json(validated_data)
            print(f"Debug JSON saved to: {validated_data.configuration.debug_json_output}")
        
        return 0
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
        if args.verbose:
            print("Detailed error traceback:")
            traceback.print_exc()
            
        return 1

# If the module is run directly, use the argument parser to process command line arguments
if __name__ == "__main__":
    sys.exit(main())
