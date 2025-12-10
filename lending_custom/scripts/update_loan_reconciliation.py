#!/usr/bin/env python3
"""
Script to automatically update mint app and lending app for loan reconciliation integration
"""
import os
import frappe
from frappe.utils import get_bench_path


def update_mint_app_files():
    """
    Update mint app files to include loan document types
    """
    mint_app_path = frappe.get_app_path("mint")
    
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
        
        # Check if loan document types are already added
        if 'loan_repayment' not in content:
            # Add loan document types to the component
            loan_components = '''                    <ToggleSwitch label={_("Loan Repayment")} id="loan_repayment" />
                    <ToggleSwitch label={_("Loan Disbursement")} id="loan_disbursement" />'''
            
            # Insert before the Bank Transaction line
            content = content.replace(
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />',
                '<ToggleSwitch label={_("Expense Claim")} id="expense_claim" />\n' + loan_components
            )
            
            # Write the updated content back
            with open(match_filters_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated mint MatchFilters.tsx with loan document types")
            return True
    
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
        
        # Update the default match filters to include loan types
        if 'loan_repayment' not in content:
            content = content.replace(
                "['payment_entry', 'journal_entry']",
                "['payment_entry', 'journal_entry', 'loan_repayment', 'loan_disbursement']"
            )
            
            with open(atoms_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated mint bankRecAtoms.ts with loan document types")
            return True
    
    return False


def update_lending_app_hooks():
    """
    Ensure lending app hooks include bank reconciliation doctypes
    """
    lending_app_path = frappe.get_app_path("lending")
    hooks_file = os.path.join(lending_app_path, "lending", "hooks.py")
    
    if os.path.exists(hooks_file):
        with open(hooks_file, 'r') as f:
            content = f.read()
        
        # Check if bank_reconciliation_doctypes is already present
        if 'bank_reconciliation_doctypes' in content:
            print("✅ Lending app hooks already include bank reconciliation doctypes")
            return True
        else:
            print("❌ Lending app hooks missing bank reconciliation doctypes")
            return False
    
    return False


def create_backup_files():
    """
    Create backup files before modification
    """
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(frappe.get_app_path("lending_custom"), "backups", timestamp)
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup mint files
        mint_app_path = frappe.get_app_path("mint")
        files_to_backup = [
            os.path.join(mint_app_path, "frontend", "src", "components", "features", "BankReconciliation", "MatchFilters.tsx"),
            os.path.join(mint_app_path, "frontend", "src", "components", "features", "BankReconciliation", "bankRecAtoms.ts")
        ]
        
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                print(f"✅ Backed up {os.path.basename(file_path)}")
        
        return backup_dir
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None


def rebuild_mint_app():
    """
    Rebuild mint app after file changes
    """
    try:
        os.system("cd {} && bench build --app mint".format(get_bench_path()))
        print("✅ Rebuilt mint app successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to rebuild mint app: {e}")
        return False


def main():
    """
    Main function to update all necessary files
    """
    print("🚀 Starting Loan Reconciliation Integration Script")
    print("=" * 60)
    
    # Check if required apps are installed
    required_apps = ['mint', 'lending', 'lending_custom']
    for app in required_apps:
        if not frappe.db.exists("Module Def", app):
            print(f"❌ {app} app is not installed")
            return False
    
    print("✅ All required apps are installed")
    
    # Create backups
    backup_dir = create_backup_files()
    if backup_dir:
        print(f"✅ Backups created at: {backup_dir}")
    
    # Update mint app files
    print("\n📝 Updating mint app files...")
    mint_updated = update_mint_app_files()
    
    # Check lending app hooks
    print("\n📝 Checking lending app hooks...")
    lending_hooks_ok = update_lending_app_hooks()
    
    # Rebuild mint app if files were updated
    if mint_updated:
        print("\n🔨 Rebuilding mint app...")
        rebuild_success = rebuild_mint_app()
    else:
        print("\n✅ No mint app files needed updating")
        rebuild_success = True
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 INTEGRATION SUMMARY:")
    print(f"   Mint app updated: {'✅' if mint_updated else '✅ (already up-to-date)'}")
    print(f"   Lending hooks: {'✅' if lending_hooks_ok else '❌'}")
    print(f"   Rebuild status: {'✅' if rebuild_success else '❌'}")
    
    if mint_updated and rebuild_success and lending_hooks_ok:
        print("\n🎉 SUCCESS! Loan reconciliation integration is complete!")
        print("\n📝 Next Steps:")
        print("   1. Access the mint app bank reconciliation")
        print("   2. Use the Settings button to enable loan document types")
        print("   3. Match loan repayments with bank transactions")
    else:
        print("\n⚠️  Some issues occurred. Please check the logs above.")
    
    return mint_updated and rebuild_success and lending_hooks_ok


if __name__ == "__main__":
    frappe.init(site='county')
    frappe.connect()
    main()