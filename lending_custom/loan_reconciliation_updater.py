"""
Frappe command to update mint and lending apps for loan reconciliation
"""
import os
import frappe
from frappe import _


@frappe.whitelist()
def update_loan_reconciliation_integration():
    """
    Update mint and lending apps for loan reconciliation integration
    """
    results = {
        'mint_updated': False,
        'lending_checked': False,
        'rebuild_needed': False,
        'success': False,
        'messages': []
    }
    
    try:
        # Update mint app files
        mint_updated = update_mint_app_files()
        results['mint_updated'] = mint_updated
        
        if mint_updated:
            results['messages'].append("✅ Updated mint app files with loan document types")
            results['rebuild_needed'] = True
        else:
            results['messages'].append("✅ Mint app files already up-to-date")
        
        # Check lending app
        lending_ok = check_lending_app_hooks()
        results['lending_checked'] = lending_ok
        
        if lending_ok:
            results['messages'].append("✅ Lending app hooks are configured correctly")
        else:
            results['messages'].append("❌ Lending app hooks need manual verification")
        
        results['success'] = True
        
    except Exception as e:
        results['messages'].append(f"❌ Error: {str(e)}")
        frappe.log_error(f"Loan reconciliation update failed: {str(e)}")
    
    return results


def update_mint_app_files():
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
            # Add loan document types
            content = content.replace(
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />',
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />\n'
                '                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />\n'
                '                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'
            )
            
            with open(match_filters_file, 'w') as f:
                f.write(content)
            
            updated = True
    
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
    
    return updated


def check_lending_app_hooks():
    """
    Check if lending app hooks are properly configured
    """
    try:
        from erpnext.accounts.doctype.bank_transaction.bank_transaction import get_doctypes_for_bank_reconciliation
        doctypes = get_doctypes_for_bank_reconciliation()
        
        loan_types = ['Loan Repayment', 'Loan Disbursement']
        return all(dt in doctypes for dt in loan_types)
    except:
        return False


@frappe.whitelist()
def rebuild_mint_app():
    """
    Trigger mint app rebuild
    """
    try:
        # This would need to be called via bench command
        return {
            'success': True,
            'message': 'Please run: bench build --app mint'
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }


def execute_update_script():
    """
    Execute the update script - can be called from patches
    """
    return update_loan_reconciliation_integration()