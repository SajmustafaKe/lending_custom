"""
Patch to automatically update mint and lending apps for loan reconciliation
"""
import os
import frappe


def execute():
    """
    Execute the automatic update for loan reconciliation integration
    """
    if not frappe.db.exists("Module Def", "mint"):
        frappe.logger().info("Mint app not installed, skipping update")
        return
    
    try:
        # Update mint app files
        updated = update_mint_app_for_loan_reconciliation()
        
        if updated:
            frappe.logger().info("✅ Successfully updated mint app for loan reconciliation")
        else:
            frappe.logger().info("✅ Mint app already configured for loan reconciliation")
            
    except Exception as e:
        frappe.logger().error(f"Failed to update mint app for loan reconciliation: {str(e)}")


def update_mint_app_for_loan_reconciliation():
    """
    Update mint app files to include loan document types
    """
    mint_app_path = frappe.get_app_path("mint")
    updated = False
    
    # Update MatchFilters.tsx
    match_filters_file = os.path.join(
        mint_app_path, 
        "frontend", 
        "src", 
        "components", 
        "features", 
        "BankReconciliation", 
        "MatchFilters.tsx"
    )
    
    if os.path.exists(match_filters_file):
        with open(match_filters_file, 'r') as f:
            content = f.read()
        
        if 'loan_repayment' not in content:
            # Add loan document types before Bank Transaction
            content = content.replace(
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />',
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />\n'
                '                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />\n'
                '                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'
            )
            
            with open(match_filters_file, 'w') as f:
                f.write(content)
            
            updated = True
            frappe.logger().info("Updated MatchFilters.tsx with loan document types")
    
    # Update bankRecAtoms.ts
    atoms_file = os.path.join(
        mint_app_path, 
        "frontend", 
        "src", 
        "components", 
        "features", 
        "BankReconciliation", 
        "bankRecAtoms.ts"
    )
    
    if os.path.exists(atoms_file):
        with open(atoms_file, 'r') as f:
            content = f.read()
        
        if 'loan_repayment' not in content:
            content = content.replace(
                "['payment_entry', 'journal_entry']",
                "['payment_entry', 'journal_entry', 'loan_repayment', 'loan_disbursement']"
            )
            
            with open(atoms_file, 'w') as f:
                f.write(content)
            
            updated = True
            frappe.logger().info("Updated bankRecAtoms.ts with loan document types")
    
    return updated