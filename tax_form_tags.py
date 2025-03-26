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
        "business_info": {
            "name_of_proprietor_tag": "f1_01[0]",
            "ssn_tag": "f1_02[0]",
            "principal_business_tag": "f1_03[0]",
            "business_code_tag": "f1_04[0]",
            "business_name_tag": "f1_05[0]",
            "ein_tag": "f1_06[0]",
            "business_address_tag": "f1_07[0]",
            "city_state_zip_tag": "f1_08[0]"
        },
        "accounting_method": {
            "cash_tag": "c1_1[0]",
            "accrual_tag": "c1_1[1]",
            "other_tag": "c1_1[2]",
            "other_specify_tag": "f1_09[0]"
        },
        "questions": {
            "material_participation_yes_tag": "c1_2[0]",
            "material_participation_no_tag": "c1_2[1]",
            "started_acquired_tag": "c1_3[0]",
            "payments_requiring_1099_yes_tag": "c1_4[0]",
            "payments_requiring_1099_no_tag": "c1_4[1]",
            "filed_required_1099_yes_tag": "c1_5[0]",
            "filed_required_1099_no_tag": "c1_5[1]"
        },
        "income": {
            "statutory_employee_tag": "c1_6[0]",
            "gross_receipts_tag": "f1_10[0]",
            "returns_allowances_tag": "f1_11[0]",
            "subtract_line2_from_line1_tag": "f1_12[0]",
            "cost_of_goods_sold_tag": "f1_13[0]",
            "gross_profit_tag": "f1_14[0]",
            "other_income_tag": "f1_15[0]",
            "gross_income_tag": "f1_16[0]"
        },
        "expenses": {
            "advertising_tag": "f1_17[0]",
            "car_truck_expenses_tag": "f1_18[0]",
            "commissions_fees_tag": "f1_19[0]",
            "contract_labor_tag": "f1_20[0]",
            "depletion_tag": "f1_21[0]",
            "depreciation_tag": "f1_22[0]",
            "employee_benefits_tag": "f1_23[0]",
            "insurance_tag": "f1_24[0]",
            "mortgage_interest_tag": "f1_25[0]",
            "other_interest_tag": "f1_26[0]",
            "legal_professional_tag": "f1_27[0]",
            "office_expense_tag": "f1_28[0]",
            "pension_profit_sharing_tag": "f1_29[0]",
            "rent_lease_vehicles_tag": "f1_30[0]",
            "rent_lease_other_tag": "f1_31[0]",
            "repairs_maintenance_tag": "f1_32[0]",
            "supplies_tag": "f1_33[0]",
            "taxes_licenses_tag": "f1_34[0]",
            "travel_tag": "f1_35[0]",
            "meals_tag": "f1_36[0]",
            "utilities_tag": "f1_37[0]",
            "wages_tag": "f1_38[0]",
            "other_expenses_tag": "f1_39[0]",
            "energy_efficient_bldg_tag": "f1_40[0]",
            "total_expenses_tag": "f1_41[0]",
            "tentative_profit_loss_tag": "f1_42[0]"
        },
        "home_office": {
            "home_total_area_tag": "f1_43[0]",
            "home_business_area_tag": "f1_44[0]",
            "home_office_expenses_tag": "f1_45[0]"
        },
        "net_profit_loss": {
            "net_profit_loss_tag": "f1_46[0]",
            "all_investment_at_risk_tag": "c1_7[0]",
            "some_investment_not_at_risk_tag": "c1_7[1]"
        },
        "cost_of_goods": {
            "cost_method_tag": "c2_1[0]",
            "lower_cost_market_tag": "c2_1[1]",
            "other_method_tag": "c2_1[2]",
            "change_in_inventory_yes_tag": "c2_2[0]",
            "change_in_inventory_no_tag": "c2_2[1]",
            "inventory_beginning_tag": "f2_01[0]",
            "purchases_tag": "f2_02[0]",
            "cost_of_labor_tag": "f2_03[0]",
            "materials_supplies_tag": "f2_04[0]",
            "other_costs_tag": "f2_05[0]",
            "sum_lines_35_39_tag": "f2_06[0]",
            "inventory_end_tag": "f2_07[0]",
            "cost_of_goods_sold_tag": "f2_08[0]"
        },
        "vehicle_info": {
            "vehicle_service_date_tag": "f2_09[0]",
            "business_miles_tag": "f2_10[0]",
            "commuting_miles_tag": "f2_11[0]",
            "other_miles_tag": "f2_12[0]",
            "personal_use_yes_tag": "c2_3[0]",
            "personal_use_no_tag": "c2_3[1]",
            "another_vehicle_yes_tag": "c2_4[0]",
            "another_vehicle_no_tag": "c2_4[1]",
            "evidence_yes_tag": "c2_5[0]",
            "evidence_no_tag": "c2_5[1]",
            "written_evidence_yes_tag": "c2_6[0]",
            "written_evidence_no_tag": "c2_6[1]"
        },
        "other_expenses": {
            "other_expenses_line1_desc_tag": "f2_13[0]",
            "other_expenses_line1_amount_tag": "f2_14[0]",
            "other_expenses_line2_desc_tag": "f2_15[0]",
            "other_expenses_line2_amount_tag": "f2_16[0]",
            "other_expenses_line3_desc_tag": "f2_17[0]",
            "other_expenses_line3_amount_tag": "f2_18[0]",
            "other_expenses_line4_desc_tag": "f2_19[0]",
            "other_expenses_line4_amount_tag": "f2_20[0]",
            "other_expenses_line5_desc_tag": "f2_21[0]",
            "other_expenses_line5_amount_tag": "f2_22[0]",
            "other_expenses_line6_desc_tag": "f2_23[0]",
            "other_expenses_line6_amount_tag": "f2_24[0]",
            "other_expenses_line7_desc_tag": "f2_25[0]",
            "other_expenses_line7_amount_tag": "f2_26[0]",
            "other_expenses_line8_desc_tag": "f2_27[0]",
            "other_expenses_line8_amount_tag": "f2_28[0]",
            "total_other_expenses_tag": "f2_29[0]"
        }
    }
}
