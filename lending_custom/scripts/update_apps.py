#!/usr/bin/env python3
"""
Manual script to update mint and lending apps for loan reconciliation integration
Usage: python update_apps.py
"""
import os
import sys

def update_mint_app():
    """Update mint app files"""
    print("🔧 Updating mint app files...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Navigate to mint app directory
    mint_frontend_path = os.path.join(script_dir, "..", "..", "..", "mint", "frontend", "src", "components", "features", "BankReconciliation")
    
    # Update MatchFilters.tsx
    match_filters_file = os.path.join(mint_frontend_path, "MatchFilters.tsx")
    
    if os.path.exists(match_filters_file):
        with open(match_filters_file, 'r') as f:
            content = f.read()
        
        if 'loan_repayment' not in content:
            content = content.replace(
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />',
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />\n'
                '                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />\n'
                '                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'
            )
            
            with open(match_filters_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated MatchFilters.tsx")
        else:
            print("✅ MatchFilters.tsx already updated")
    else:
        print("❌ MatchFilters.tsx not found")
    
    # Update bankRecAtoms.ts
    atoms_file = os.path.join(mint_frontend_path, "bankRecAtoms.ts")
    
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
            
            print("✅ Updated bankRecAtoms.ts")
        else:
            print("✅ bankRecAtoms.ts already updated")
    else:
        print("❌ bankRecAtoms.ts not found")


def main():
    """Main function"""
    print("🚀 Loan Reconciliation Integration Updater")
    print("=" * 50)
    
    update_mint_app()
    
    print("\n🎉 Update completed!")
    print("\n📝 Next steps:")
    print("1. Run: bench build --app mint")
    print("2. Restart bench")
    print("3. Access mint app to test loan reconciliation")


if __name__ == "__main__":
    main()