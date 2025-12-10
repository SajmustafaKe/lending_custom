"""
Patch to extend mint app's bank reconciliation functionality with loan document types
"""
import frappe
import os
import json


def extend_mint_match_filters():
    """
    Extend mint app's match filters to include loan document types
    """
    try:
        # Path to mint app's MatchFilters.tsx file
        mint_path = frappe.get_app_path("mint")
        match_filters_file = os.path.join(mint_path, "frontend", "src", "components", "features", "BankReconciliation", "MatchFilters.tsx")
        
        if os.path.exists(match_filters_file):
            with open(match_filters_file, 'r') as f:
                content = f.read()
            
            # Check if loan document types are already added
            if 'loan_repayment' not in content:
                # Add loan document types to the component
                loan_components = '''                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />
                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'''
                
                # Insert before the Bank Transaction line
                content = content.replace(
                    '<ToggleSwitch label={_("Bank Transaction")} id="bank_transaction" />',
                    loan_components + '\n                    <ToggleSwitch label={_("Bank Transaction")} id="bank_transaction" />'
                )
                
                # Write the updated content back
                with open(match_filters_file, 'w') as f:
                    f.write(content)
                
                frappe.logger().info("Extended mint MatchFilters component with loan document types")
                return True
        
        # Also update the bankRecAtoms.ts file to include loan types in default
        atoms_file = os.path.join(mint_path, "frontend", "src", "components", "features", "BankReconciliation", "bankRecAtoms.ts")
        
        if os.path.exists(atoms_file):
            with open(atoms_file, 'r') as f:
                content = f.read()
            
            # Update the default match filters to include loan types
            if 'loan_repayment' not in content:
                content = content.replace(
                    "['payment_entry', 'journal_entry']",
                    "['payment_entry', 'journal_entry', 'loan_repayment', 'loan_disbursement']"
                )
                
                with open(atoms_file, 'w') as f:
                    f.write(content)
                
                frappe.logger().info("Extended mint bankRecAtoms with loan document types")
                return True
                
    except Exception as e:
        frappe.logger().error(f"Failed to extend mint match filters: {e}")
        return False
    
    return False


def execute():
    """
    Execute the patch
    """
    if frappe.db.exists("Module Def", "mint"):
        extend_mint_match_filters()