# tax_form_tags.py Tax Form Tags module for Open Tax Liberty
# Copyright (C) 2025 Todd & Linda Rovito/Qualia Insights LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dictionary of all Tax Form Tags fields:
#
# The following Tax Forms are covered in this dictionary:
#   - IRS F1040 
tax_form_tags_dict = {
    "F1040": {
        "configuration": {
            # No tag fields in configuration section
        },
        "name_address_ssn": {
            "first_name_middle_initial_tag": "f1_04[0]",
            "last_name_tag": "f1_05[0]",
            "ssn_tag": "f1_06[0]",
            "spouse_first_name_middle_inital_tag": "f1_07[0]",
            "spouse_last_name_tag": "f1_08[0]",
            "spouse_ssn_tag": "f1_09[0]",
            "home_address_tag": "f1_10[0]",
            "apartment_no_tag": "f1_11[0]",
            "city_tag": "f1_12[0]",
            "state_tag": "f1_13[0]",
            "zip_tag": "f1_14[0]",
            "foreign_country_name_tag": "f1_15[0]",
            "foreign_country_province_tag": "f1_16[0]",
            "foreign_country_postal_code_tag": "f1_17[0]",
            "presidential_you_tag": "c1_1[0]",
            "presidential_spouse_tag": "c1_2[0]"
        },
        "filing_status": {
            "single_or_HOH_tag": "c1_3[0]",
            "married_filing_jointly_or_QSS_tag": "c1_3[1]",
            "married_filing_separately_tag": "c1_3[2]",
            "treating_nonresident_alien_tag": "c1_4[0]",
            "spouse_or_child_name_tag": "f1_18[0]",
            "nonresident_alien_name_tag": "f1_19[0]"
        },
        "digital_assets": {
            "yes_tag": "c1_5[0]",
            "no_tag": "c1_5[1]"
        },
        "standard_deduction": {
            "you_as_a_dependent_tag": "c1_6[0]",
            "your_spouse_as_a_dependent_tag": "c1_7[0]",
            "spouse_itemizes_tag": "c1_8[0]",
            "born_before_jan_2_1960_tag": "c1_9[0]",
            "are_blind_tag": "c1_10[0]",
            "spouse_born_before_jan_2_1960_tag": "c1_11[0]",
            "spouse_is_blind_tag": "c1_12[0]"
        },
        "dependents": {
            "check_if_more_than_4_dependents_tag": "c1_13[0]",
            "dependent_1_first_last_name_tag": "f1_20[0]",
            "dependent_1_ssn_tag": "f1_21[0]",
            "dependent_1_relationship_tag": "f1_22[0]",
            "dependent_1_child_tax_credit_tag": "c1_14[0]",
            "dependent_1_credit_for_other_dependents_tag": "c1_15[0]",
            "dependent_2_first_last_name_tag": "f1_23[0]",
            "dependent_2_ssn_tag": "f1_24[0]",
            "dependent_2_relationship_tag": "f1_25[0]",
            "dependent_2_child_tax_credit_tag": "c1_16[0]",
            "dependent_2_credit_for_other_dependents_tag": "c1_17[0]",
            "dependent_3_first_last_name_tag": "f1_26[0]",
            "dependent_3_ssn_tag": "f1_27[0]",
            "dependent_3_relationship_tag": "f1_28[0]",
            "dependent_3_child_tax_credit_tag": "c1_18[0]",
            "dependent_3_credit_for_other_dependents_tag": "c1_19[0]",
            "dependent_4_first_last_name_tag": "f1_29[0]",
            "dependent_4_ssn_tag": "f1_30[0]",
            "dependent_4_relationship_tag": "f1_31[0]",
            "dependent_4_child_tax_credit_tag": "c1_19[0]",
            "dependent_4_credit_for_other_dependents_tag": "c1_20[0]"
        },
        "income": {
            "L1a_tag": "f1_32[0]",
            "L1b_tag": "f1_33[0]",
            "L1c_tag": "f1_34[0]",
            "L1d_tag": "f1_35[0]",
            "L1e_tag": "f1_36[0]",
            "L1f_tag": "f1_37[0]",
            "L1g_tag": "f1_38[0]",
            "L1h_tag": "f1_39[0]",
            "L1i_tag": "f1_40[0]",
            "L1z_tag": "f1_41[0]",
            "L2a_tag": "f1_42[0]",
            "L2b_tag": "f1_43[0]",
            "L3a_tag": "f1_44[0]",
            "L3b_tag": "f1_45[0]",
            "L4a_tag": "f1_46[0]",
            "L4b_tag": "f1_47[0]",
            "L5a_tag": "f1_48[0]",
            "L5b_tag": "f1_49[0]",
            "L6a_tag": "f1_50[0]",
            "L6b_tag": "f1_51[0]",
            "L6c_tag": "c1_22[0]",
            "L7cb_tag": "c1_23[0]",
            "L7_tag": "f1_52[0]",
            "L8_tag": "f1_53[0]",
            "L9_tag": "f1_54[0]",
            "L10_tag": "f1_55[0]",
            "L11_tag": "f1_56[0]",
            "L12_tag": "f1_57[0]",
            "L13_tag": "f1_58[0]",
            "L14_tag": "f1_59[0]",
            "L15_tag": "f1_60[0]"
        },
        "tax_and_credits": {
            "L16_check_8814_tag": "c2_1[0]",
            "L16_check_4972_tag": "c2_2[0]",
            "L16_check_3_tag": "c2_3[0]",
            "L16_check_3_field_tag": "f2_01[0]",
            "L16_tag": "f2_02[0]",
            "L17_tag": "f2_03[0]",
            "L18_tag": "f2_04[0]",
            "L19_tag": "f2_05[0]",
            "L20_tag": "f2_06[0]",
            "L21_tag": "f2_07[0]",
            "L22_tag": "f2_08[0]",
            "L23_tag": "f2_09[0]",
            "L24_tag": "f2_10[0]"
        },
        "payments": {
            "L25a_tag": "f2_11[0]",
            "L25b_tag": "f2_12[0]",
            "L25c_tag": "f2_13[0]",
            "L25d_tag": "f2_14[0]",
            "L26_tag": "f2_15[0]",
            "L27_tag": "f2_16[0]",
            "L28_tag": "f2_17[0]",
            "L29_tag": "f2_18[0]",
            "L31_tag": "f2_20[0]",
            "L32_tag": "f2_21[0]",
            "L33_tag": "f2_22[0]"
        },
        "refund": {
            "L34_tag": "f2_23[0]",
            "L35a_check_tag": "c2_4[]0]",
            "L35a_tag": "f2_24[0]",
            "L35a_b_tag": "f2_25[0]",
            "L35c_checking_tag": "c2_5[0]",
            "L35c_savings_tag": "c2_5[1]",
            "L35a_d_tag": "f2_26[0]",
            "L36_tag": "f2_27[0]"
        },
        "amount_you_owe": {
            "L37_tag": "f2_28[0]",
            "L38_tag": "f2_29[0]"
        },
        "third_party_designee": {
            "do_you_want_to_designate_yes_tag": "c2_6[0]",
            "do_you_want_to_designate_no_tag": "c2_6[1]",
            "desginee_name_tag": "f2_30[0]",
            "desginee_phone_tag": "f2_31[0]",
            "desginee_pin_tag": "f2_32[0]"
        },
        "sign_here": {
            "your_occupation_tag": "f2_33[0]",
            "your_pin_tag": "f2_34[0]",
            "spouse_occupation_tag": "f2_35[0]",
            "spouse_pin_tag": "f2_36[0]",
            "phone_no_tag": "f2_37[0]",
            "email_tag": "f2_38[0]"
        }
    },
    "F1040SC": {
        "configuration": {
            # No tag fields in configuration section
        },
        "business_information": {
            "business_name_tag": "f1_1[0]",             # Name of proprietor 
            "ssn_tag": "f1_2[0]",                       # SSN
            "principal_business_tag": "f1_3[0]",        # Principal business
            "business_code_tag": "f1_4[0]",             # Business code
            "business_name_separate_tag": "f1_5[0]",    # Business name 
            "ein_tag": "f1_6[0]",                       # EIN
            "business_address_tag": "f1_7[0]",          # Business address
            "business_city_state_zip_tag": "f1_8[0]",   # City, state, ZIP
            "accounting_method_cash_tag": "c1_1[0]",     # Cash
            "accounting_method_accrual_tag": "c1_1[1]",  # Accrual
            "accounting_method_other_tag": "c1_1[2]",    # Other
            "accounting_method_other_text_tag": "f1_9[0]", # Other specified
            "material_participation_yes_tag": "c1_2[0]", # Participate - Yes
            "material_participation_no_tag": "c1_2[1]",  # Participate - No
            "not_started_business_tag": "c1_3[0]",       # Started business
            "issued_1099_required_yes_tag": "c1_4[0]",   # 1099 payments - Yes
            "issued_1099_required_no_tag": "c1_4[1]",    # 1099 payments - No
            "issued_1099_not_required_yes_tag": "c1_5[0]", # Filed 1099 - Yes
            "issued_1099_not_required_no_tag": "c1_5[1]"   # Filed 1099 - No
        },
        "income": {
            "statutory_employee_tag": "c1_6[0]",         # Statutory employee
            "L1_tag": "f1_10[0]",                        # Gross receipts/sales
            "L2_tag": "f1_11[0]",                        # Returns and allowances
            "L3_tag": "f1_12[0]",                        # Subtract line 2 from line 1
            "L4_tag": "f1_13[0]",                        # Cost of goods sold
            "L5_tag": "f1_14[0]",                        # Gross profit
            "L6_tag": "f1_15[0]",                        # Other income
            "L7_tag": "f1_16[0]"                         # Gross income
        },
        "expenses": {
            "L8_tag": "f1_17[0]",                        # Advertising
            "L9_tag": "f1_18[0]",                        # Car and truck expenses
            "L10_tag": "f1_19[0]",                       # Commissions and fees
            "L11_tag": "f1_20[0]",                       # Contract labor
            "L12_tag": "f1_21[0]",                       # Depletion
            "L13_tag": "f1_22[0]",                       # Depreciation
            "L14_tag": "f1_23[0]",                       # Employee benefits
            "L15_tag": "f1_24[0]",                       # Insurance
            "L16a_tag": "f1_25[0]",                      # Mortgage interest
            "L16b_tag": "f1_26[0]",                      # Other interest
            "L17_tag": "f1_27[0]",                       # Legal and professional
            "L18_tag": "f1_28[0]",                       # Office expense
            "L19_tag": "f1_29[0]",                       # Pension plans
            "L20a_tag": "f1_30[0]",                      # Rent/lease vehicles
            "L20b_tag": "f1_31[0]",                      # Rent/lease other
            "L21_tag": "f1_32[0]",                       # Repairs and maintenance
            "L22_tag": "f1_33[0]",                       # Supplies
            "L23_tag": "f1_34[0]",                       # Taxes and licenses
            "L24a_tag": "f1_35[0]",                      # Travel
            "L24b_tag": "f1_36[0]",                      # Deductible meals
            "L25_tag": "f1_37[0]",                       # Utilities
            "L26_tag": "f1_38[0]",                       # Wages
            "L27a_tag": "f1_39[0]",                      # Other expenses
            "L27b_tag": "f1_40[0]",                      # Energy efficient bldgs
            "L28_tag": "f1_41[0]",                       # Total expenses
            "L29_tag": "f1_42[0]"                        # Tentative profit/loss
        },
        "home_office": {
            "simplified_method_tag": "c1_7[0]",          # Simplified method
            "home_total_area_tag": "f1_43[0]",           # Total sq footage
            "home_business_area_tag": "f1_44[0]",        # Business sq footage
            "L30_tag": "f1_45[0]"                        # Home office expenses
        },
        "net_profit_loss": {
            "L31_tag": "f1_46[0]",                       # Net profit or loss
            "L32a_tag": "c1_7[0]",                       # All investment at risk
            "L32b_tag": "c1_7[1]"                        # Some investment not at risk
        },
        "cost_of_goods_sold": {
            "L33a_tag": "c2_1[0]",                       # Cost method
            "L33b_tag": "c2_1[1]",                       # Lower of cost or market
            "L33c_tag": "c2_1[2]",                       # Other method
            "L34_yes_tag": "c2_2[0]",                    # Inventory change Yes
            "L34_no_tag": "c2_2[1]",                     # Inventory change No
            "L35_tag": "f2_01[0]",                       # Beginning inventory
            "L36_tag": "f2_02[0]",                       # Purchases
            "L37_tag": "f2_03[0]",                       # Cost of labor
            "L38_tag": "f2_04[0]",                       # Materials and supplies
            "L39_tag": "f2_05[0]",                       # Other costs
            "L40_tag": "f2_06[0]",                       # Sum lines 35-39
            "L41_tag": "f2_07[0]",                       # Ending inventory
            "L42_tag": "f2_08[0]"                        # Cost of goods sold
        },
        "vehicle_information": {
            "L43_month_tag": "f2_9[0]",                 # Vehicle service date Month
            "L43_day_tag": "f2_10[0]",                   # Vehicle service date Day
            "L43_year_tag": "f2_11[0]",                  # Vehicle service date Year
            "L44a_tag": "f2_12[0]",                      # Business miles
            "L44b_tag": "f2_13[0]",                      # Commuting miles
            "L44c_tag": "f2_14[0]",                      # Other miles
            "L45_yes_tag": "c2_5[0]",                    # Personal use Yes /1 for check /Off for no check
            "L45_no_tag": "c2_5[1]",                     # Personal use No /2 for check /Off for no check
            "L46_yes_tag": "c2_6[0]",                    # Another vehicle Yes /1 for check /Off for no check
            "L46_no_tag": "c2_6[1]",                     # Another vehicle No /2 for check /Off for no check
            "L47a_yes_tag": "c2_7[0]",                   # Evidence Yes /1 for check /Off for no check
            "L47a_no_tag": "c2_7[1]",                    # Evidence No /2 for check /Off for no check
            "L47b_yes_tag": "c2_8[0]",                   # Written evidence Yes /1 for check /Off for no check
            "L47b_no_tag": "c2_8[1]"                     # Written evidence No /2 for check /Off for no check
        },
        "other_expenses": {
            "other_expense_1_desc_tag": "f2_15[0]",      # Expense 1 description
            "other_expense_1_amount_tag": "f2_16[0]",    # Expense 1 amount
            "other_expense_2_desc_tag": "f2_17[0]",      # Expense 2 description
            "other_expense_2_amount_tag": "f2_18[0]",    # Expense 2 amount
            "other_expense_3_desc_tag": "f2_19[0]",      # Expense 3 description
            "other_expense_3_amount_tag": "f2_20[0]",    # Expense 3 amount
            "other_expense_4_desc_tag": "f2_21[0]",      # Expense 4 description
            "other_expense_4_amount_tag": "f2_22[0]",    # Expense 4 amount
            "other_expense_5_desc_tag": "f2_23[0]",      # Expense 5 description
            "other_expense_5_amount_tag": "f2_24[0]",    # Expense 5 amount
            "other_expense_6_desc_tag": "f2_25[0]",      # Expense 6 description
            "other_expense_6_amount_tag": "f2_26[0]",    # Expense 6 amount
            "other_expense_7_desc_tag": "f2_27[0]",      # Expense 7 description
            "other_expense_7_amount_tag": "f2_28[0]",    # Expense 7 amount
            "other_expense_8_desc_tag": "f2_29[0]",      # Expense 8 description
            "other_expense_8_amount_tag": "f2_30[0]",    # Expense 8 amount
            "other_expense_9_desc_tag": "f2_31[0]",      # Expense 9 description
            "other_expense_9_amount_tag": "f2_32[0]",    # Expense 9 amount
            "L48_tag": "f2_33[0]"                        # Total other expenses
        }
    }
}
