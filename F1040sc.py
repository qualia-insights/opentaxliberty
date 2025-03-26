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
    business_address: str = Field(..., description="Business address (street)")
    business_city_state_zip: str = Field(..., description="Business address (city, state, ZIP)")
    ein: Optional[str] = Field(None, description="Employer ID number (EIN)")
    business_code: Optional[str] = Field(None, description="Business code")
    accounting_method_cash: str = Field("/Off", description="Cash accounting method checkbox")
    accounting_method_accrual: str = Field("/Off", description="Accrual accounting method checkbox")
    accounting_method_other: str = Field("/Off", description="Other accounting method checkbox")
    accounting_method_other_text: Optional[str] = Field(None, description="Other accounting method description")
    not_started_business: str = Field("/Off", description="Not started business checkbox")
    acquired_business: str = Field("/Off", description="Acquired business checkbox")
    modified_business: str = Field("/Off", description="Modified business checkbox")
    
    material_participation_yes: str = Field("/Off", description="Yes checkbox for material participation")
    material_participation_no: str = Field("/Off", description="No checkbox for material participation")
    
    issued_1099_required_yes: str = Field("/Off", description="Yes checkbox for issued 1099s when required")
    issued_1099_required_no: str = Field("/Off", description="No checkbox for issued 1099s when required")
    
    issued_1099_not_required_yes: str = Field("/Off", description="Yes checkbox for required to file 1099s")
    issued_1099_not_required_no: str = Field("/Off", description="No checkbox for required to file 1099s")

    @field_validator('accounting_method_cash', 'accounting_method_accrual', 'accounting_method_other',
                    'not_started_business', 'acquired_business', 'modified_business',
                    'material_participation_yes', 'material_participation_no',
                    'issued_1099_required_yes', 'issued_1099_required_no',
                    'issued_1099_not_required_yes', 'issued_1099_not_required_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
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
    
    @model_validator(mode='after')
    def validate_material_participation(self):
        """Validate that exactly one material participation option is selected."""
        yes_selected = self.material_participation_yes == "/1"
        no_selected = self.material_participation_no == "/1"
        
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


class Income(BaseModel):
    """Income section of Schedule C."""
    gross_receipts: Decimal = Field(default=Decimal('0'), description="Gross receipts or sales")
    returns_allowances: Decimal = Field(default=Decimal('0'), description="Returns and allowances")
    other_income: Decimal = Field(default=Decimal('0'), description="Other business income")
    gross_income: Decimal = Field(default=Decimal('0'), description="Gross income")

    @model_validator(mode='after')
    def calculate_gross_income(self):
        """Calculate gross income (Line 7) from other income fields."""
        self.gross_income = self.gross_receipts - self.returns_allowances + self.other_income
        return self


class Expenses(BaseModel):
    """Expenses section of Schedule C."""
    advertising: Decimal = Field(default=Decimal('0'), description="Advertising")
    car_truck_expenses: Decimal = Field(default=Decimal('0'), description="Car and truck expenses")
    commissions_fees: Decimal = Field(default=Decimal('0'), description="Commissions and fees")
    contract_labor: Decimal = Field(default=Decimal('0'), description="Contract labor")
    depletion: Decimal = Field(default=Decimal('0'), description="Depletion")
    depreciation: Decimal = Field(default=Decimal('0'), description="Depreciation")
    employee_benefits: Decimal = Field(default=Decimal('0'), description="Employee benefit programs")
    insurance: Decimal = Field(default=Decimal('0'), description="Insurance (other than health)")
    interest_mortgage: Decimal = Field(default=Decimal('0'), description="Interest on mortgage")
    interest_other: Decimal = Field(default=Decimal('0'), description="Interest - other")
    legal_professional: Decimal = Field(default=Decimal('0'), description="Legal and professional services")
    office_expense: Decimal = Field(default=Decimal('0'), description="Office expense")
    pension_profit_sharing: Decimal = Field(default=Decimal('0'), description="Pension and profit-sharing plans")
    rent_lease_vehicles: Decimal = Field(default=Decimal('0'), description="Rent/lease - vehicles, machinery, equipment")
    rent_lease_other: Decimal = Field(default=Decimal('0'), description="Rent/lease - other business property")
    repairs_maintenance: Decimal = Field(default=Decimal('0'), description="Repairs and maintenance")
    supplies: Decimal = Field(default=Decimal('0'), description="Supplies")
    taxes_licenses: Decimal = Field(default=Decimal('0'), description="Taxes and licenses")
    travel: Decimal = Field(default=Decimal('0'), description="Travel")
    meals: Decimal = Field(default=Decimal('0'), description="Deductible meals")
    utilities: Decimal = Field(default=Decimal('0'), description="Utilities")
    wages: Decimal = Field(default=Decimal('0'), description="Wages")
    
    other_expenses_total: Decimal = Field(default=Decimal('0'), description="Total other expenses")
    
    total_expenses: Decimal = Field(default=Decimal('0'), description="Total expenses")


class OtherExpenses(BaseModel):
    """Other expenses section of Schedule C."""
    expense_items: List[Dict[str, Union[str, Decimal]]] = Field(
        default_factory=list,
        description="List of other expense items, each with 'description' and 'amount' keys"
    )
    
    @field_validator('expense_items')
    @classmethod
    def validate_expense_items(cls, v):
        """Validate expense items format."""
        if not isinstance(v, list):
            raise ValueError("expense_items must be a list")
        
        for i, item in enumerate(v):
            if not isinstance(item, dict):
                raise ValueError(f"Item {i} must be a dictionary")
            
            if 'description' not in item:
                raise ValueError(f"Item {i} must have a 'description' key")
            
            if 'amount' not in item:
                raise ValueError(f"Item {i} must have an 'amount' key")
            
            # Convert amount to Decimal if it's not already
            if not isinstance(item['amount'], Decimal):
                try:
                    item['amount'] = Decimal(str(item['amount']))
                except (ValueError, TypeError):
                    raise ValueError(f"Item {i} amount must be a valid number")
        
        return v
    
    def calculate_total(self) -> Decimal:
        """Calculate the total of all other expenses."""
        return sum(Decimal(str(item['amount'])) for item in self.expense_items)


class CostOfGoodsSold(BaseModel):
    """Cost of Goods Sold section of Schedule C."""
    method_cost: str = Field("/Off", description="Cost method checkbox")
    method_lower_market: str = Field("/Off", description="Lower of cost or market method checkbox")
    method_other: str = Field("/Off", description="Other method checkbox")
    
    beginning_inventory: Decimal = Field(default=Decimal('0'), description="Beginning inventory")
    purchases: Decimal = Field(default=Decimal('0'), description="Purchases")
    labor_costs: Decimal = Field(default=Decimal('0'), description="Labor costs")
    materials_supplies: Decimal = Field(default=Decimal('0'), description="Materials and supplies")
    other_costs: Decimal = Field(default=Decimal('0'), description="Other costs")
    ending_inventory: Decimal = Field(default=Decimal('0'), description="Ending inventory")
    
    personal_items_yes: str = Field("/Off", description="Yes checkbox for personal items")
    personal_items_no: str = Field("/Off", description="No checkbox for personal items")
    
    total_cost: Decimal = Field(default=Decimal('0'), description="Total cost of goods sold")

    @field_validator('method_cost', 'method_lower_market', 'method_other',
                    'personal_items_yes', 'personal_items_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_method(self):
        """Validate that exactly one valuation method is selected."""
        methods = [
            (self.method_cost, "cost"),
            (self.method_lower_market, "lower of cost or market"),
            (self.method_other, "other")
        ]
        
        selected_methods = [name for method, name in methods if method == "/1"]
        
        if len(selected_methods) != 1:
            raise ValueError(f"Exactly one valuation method must be selected, found {len(selected_methods)}: {selected_methods}")
            
        return self
    
    @model_validator(mode='after')
    def validate_personal_items(self):
        """Validate that exactly one personal items option is selected."""
        yes_selected = self.personal_items_yes == "/1"
        no_selected = self.personal_items_no == "/1"
        
        if yes_selected and no_selected:
            raise ValueError("Cannot select both Yes and No for personal items")
        
        if not (yes_selected or no_selected):
            raise ValueError("Must select either Yes or No for personal items")
            
        return self
    
    @model_validator(mode='after')
    def calculate_total_cost(self):
        """Calculate total cost of goods sold."""
        self.total_cost = (
            self.beginning_inventory + 
            self.purchases + 
            self.labor_costs + 
            self.materials_supplies + 
            self.other_costs - 
            self.ending_inventory
        )
        return self


class VehicleInformation(BaseModel):
    """Vehicle Information section of Schedule C."""
    vehicle_description: Optional[str] = Field(None, description="Vehicle description")
    date_placed_in_service: Optional[str] = Field(None, description="Date vehicle placed in service")
    business_miles: Optional[Decimal] = Field(None, description="Business miles")
    commuting_miles: Optional[Decimal] = Field(None, description="Commuting miles")
    other_miles: Optional[Decimal] = Field(None, description="Other personal miles")
    
    vehicle_personal_yes: Optional[str] = Field(None, description="Yes checkbox for personal use")
    vehicle_personal_no: Optional[str] = Field(None, description="No checkbox for personal use")
    
    another_vehicle_yes: Optional[str] = Field(None, description="Yes checkbox for another vehicle")
    another_vehicle_no: Optional[str] = Field(None, description="No checkbox for another vehicle")
    
    evidence_yes: Optional[str] = Field(None, description="Yes checkbox for written evidence")
    evidence_no: Optional[str] = Field(None, description="No checkbox for written evidence")
    
    evidence_written_yes: Optional[str] = Field(None, description="Yes checkbox for written evidence")
    evidence_written_no: Optional[str] = Field(None, description="No checkbox for written evidence")

    @field_validator('vehicle_personal_yes', 'vehicle_personal_no',
                    'another_vehicle_yes', 'another_vehicle_no',
                    'evidence_yes', 'evidence_no',
                    'evidence_written_yes', 'evidence_written_no')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_vehicle_information(self):
        """Validate that vehicle information is consistent."""
        # If any vehicle information is provided, validate all required fields
        has_vehicle_info = any([
            self.vehicle_description,
            self.date_placed_in_service,
            self.business_miles is not None,
            self.commuting_miles is not None,
            self.other_miles is not None
        ])
        
        if has_vehicle_info:
            missing_fields = []
            
            if not self.vehicle_description:
                missing_fields.append("vehicle_description")
            
            if not self.date_placed_in_service:
                missing_fields.append("date_placed_in_service")
            
            if self.business_miles is None:
                missing_fields.append("business_miles")
            
            if self.commuting_miles is None:
                missing_fields.append("commuting_miles")
            
            if self.other_miles is None:
                missing_fields.append("other_miles")
            
            if missing_fields:
                raise ValueError(f"If any vehicle information is provided, the following fields must also be provided: {', '.join(missing_fields)}")
            
            # Validate yes/no pairs
            if not self._validate_yes_no_pair(self.vehicle_personal_yes, self.vehicle_personal_no, "vehicle personal use"):
                raise ValueError("Must select either Yes or No for vehicle personal use")
            
            if not self._validate_yes_no_pair(self.another_vehicle_yes, self.another_vehicle_no, "another vehicle"):
                raise ValueError("Must select either Yes or No for another vehicle")
            
            if not self._validate_yes_no_pair(self.evidence_yes, self.evidence_no, "evidence"):
                raise ValueError("Must select either Yes or No for evidence")
            
            if not self._validate_yes_no_pair(self.evidence_written_yes, self.evidence_written_no, "written evidence"):
                raise ValueError("Must select either Yes or No for written evidence")
        
        return self
    
    def _validate_yes_no_pair(self, yes_value, no_value, field_name):
        """Helper to validate yes/no pairs."""
        if yes_value is None and no_value is None:
            return False
        
        yes_selected = yes_value == "/1"
        no_selected = no_value == "/1"
        
        if yes_selected and no_selected:
            raise ValueError(f"Cannot select both Yes and No for {field_name}")
        
        if not (yes_selected or no_selected):
            return False
        
        return True


class HomeOfficeInformation(BaseModel):
    """Home Office Information section of Schedule C."""
    simplified_method_used: Optional[str] = Field(None, description="Checkbox for simplified method")
    home_business_percentage: Optional[Decimal] = Field(None, description="Percentage of home used for business")
    home_office_deduction: Optional[Decimal] = Field(None, description="Home office deduction")

    @field_validator('simplified_method_used')
    @classmethod
    def validate_checkbox(cls, v):
        if v is not None and v not in ["/1", "/Off"]:
            raise ValueError(f"Checkbox value must be '/1' (checked) or '/Off' (unchecked), got '{v}'")
        return v
    
    @field_validator('home_business_percentage')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError(f"Home business percentage must be between 0 and 100, got {v}")
        return v


class F1040scDocument(BaseModel):
    """Complete F1040 Schedule C document structure."""
    configuration: F1040scConfiguration
    business_information: BusinessInformation
    income: Income
    expenses: Expenses
    other_expenses: Optional[OtherExpenses] = None
    cost_of_goods_sold: Optional[CostOfGoodsSold] = None
    vehicle_information: Optional[VehicleInformation] = None
    home_office_information: Optional[HomeOfficeInformation] = None
    
    net_profit_loss: Decimal = Field(default=Decimal('0'), description="Net profit or loss")

    @model_validator(mode='after')
    def calculate_net_profit_loss(self):
        """Calculate net profit or loss."""
        # Calculate total expenses
        total_expenses = sum([
            self.expenses.advertising,
            self.expenses.car_truck_expenses,
            self.expenses.commissions_fees,
            self.expenses.contract_labor,
            self.expenses.depletion,
            self.expenses.depreciation,
            self.expenses.employee_benefits,
            self.expenses.insurance,
            self.expenses.interest_mortgage,
            self.expenses.interest_other,
            self.expenses.legal_professional,
            self.expenses.office_expense,
            self.expenses.pension_profit_sharing,
            self.expenses.rent_lease_vehicles,
            self.expenses.rent_lease_other,
            self.expenses.repairs_maintenance,
            self.expenses.supplies,
            self.expenses.taxes_licenses,
            self.expenses.travel,
            self.expenses.meals,
            self.expenses.utilities,
            self.expenses.wages
        ])
        
        # Add other expenses if provided
        if self.other_expenses:
            other_expenses_total = self.other_expenses.calculate_total()
            self.expenses.other_expenses_total = other_expenses_total
            total_expenses += other_expenses_total
        
        # Set total expenses
        self.expenses.total_expenses = total_expenses
        
        # Add cost of goods sold if provided
        cost_of_goods = Decimal('0')
        if self.cost_of_goods_sold:
            cost_of_goods = self.cost_of_goods_sold.total_cost
        
        # Calculate net profit or loss
        self.net_profit_loss = self.income.gross_income - self.expenses.total_expenses - cost_of_goods
        
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

    # TODO: Define the actual tags for Schedule C in tax_form_tags.py module
    # and use them here to write to the PDF
    F1040sc_dict = F1040sc_doc.model_dump()

    # This is a placeholder that would be implemented with actual PDF field tags
    """
    for key in F1040sc_dict:
        if key == "configuration":
            continue
            
        # Process any additional sub-keys that have corresponding tag fields
        for sub_key, sub_value in F1040sc_dict[key].items():
            # Skip special keys
            if sub_key == '_comment' in sub_key:
                continue
            else:
                tag_key = f"{sub_key}_tag"
                if tag_key in tax_form_tags_dict["F1040SC"][key]:
                    write_field_pdf(writer, tax_form_tags_dict["F1040SC"][key][tag_key], sub_value)
                else:
                    raise ValueError(f"Cannot find tag_key: {tag_key} in tax_form_tags_dict")
    """
    
    print("NOTE: PDF field mapping not yet implemented for Schedule C")
    print("You'll need to add Schedule C tags to the tax_form_tags.py dictionary")

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
        print(f"Net profit/loss: {validated_data.net_profit_loss}")
        
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
