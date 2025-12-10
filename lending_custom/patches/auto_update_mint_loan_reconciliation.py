"""
Patch to automatically update mint and lending apps for loan reconciliation
"""
import os
import frappe


def execute():
    """
    Execute the automatic update for loan reconciliation integration
    """
    try:
        # Update mint app files
        updated = update_mint_app_for_loan_reconciliation()
        
        if updated:
            frappe.logger().info("✅ Successfully updated mint app for loan reconciliation")
            print("✅ Successfully updated mint app for loan reconciliation")
        else:
            frappe.logger().info("✅ Mint app already configured for loan reconciliation")
            print("✅ Mint app already configured for loan reconciliation")
            
    except Exception as e:
        frappe.logger().error(f"Failed to update mint app for loan reconciliation: {str(e)}")
        print(f"❌ Failed to update mint app for loan reconciliation: {str(e)}")
        raise


def update_mint_app_for_loan_reconciliation():
    """
    Update mint app files to include loan document types
    """
    # Use the correct path - mint app files are in the apps/mint directory
    mint_frontend_path = "/Users/mac/ERPNext/loan/apps/mint/frontend"
    updated = False
    
    # Update MatchFilters.tsx
    match_filters_file = os.path.join(
        mint_frontend_path, 
        "src", 
        "components", 
        "features", 
        "BankReconciliation", 
        "MatchFilters.tsx"
    )
    
    print(f"Looking for MatchFilters.tsx at: {match_filters_file}")
    
    if os.path.exists(match_filters_file):
        with open(match_filters_file, 'r') as f:
            content = f.read()
        
        if 'loan_repayment' not in content:
            print("Adding loan document types to MatchFilters.tsx...")
            # Add loan document types after Expense Claim
            original_line = '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />'
            new_content = (
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />\n'
                '                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />\n'
                '                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'
            )
            
            content = content.replace(original_line, new_content)
            
            with open(match_filters_file, 'w') as f:
                f.write(content)
            
            updated = True
            frappe.logger().info("Updated MatchFilters.tsx with loan document types")
            print("✅ Updated MatchFilters.tsx with loan document types")
        else:
            print("✅ MatchFilters.tsx already contains loan document types")
    
    # Update bankRecAtoms.ts
    atoms_file = os.path.join(
        mint_frontend_path, 
        "src", 
        "components", 
        "features", 
        "BankReconciliation", 
        "bankRecAtoms.ts"
    )
    
    print(f"Looking for bankRecAtoms.ts at: {atoms_file}")
    
    if os.path.exists(atoms_file):
        with open(atoms_file, 'r') as f:
            content = f.read()
        
        if 'loan_repayment' not in content:
            print("Adding loan document types to bankRecAtoms.ts...")
            content = content.replace(
                "['payment_entry', 'journal_entry']",
                "['payment_entry', 'journal_entry', 'loan_repayment', 'loan_disbursement']"
            )
            
            with open(atoms_file, 'w') as f:
                f.write(content)
            
            updated = True
            frappe.logger().info("Updated bankRecAtoms.ts with loan document types")
            print("✅ Updated bankRecAtoms.ts with loan document types")
        else:
            print("✅ bankRecAtoms.ts already contains loan document types")
    
    return updated