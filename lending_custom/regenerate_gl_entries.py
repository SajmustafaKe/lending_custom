"""
Script to regenerate GL entries for Loan Repayments that are missing them.

Usage:
    bench --site <sitename> regenerate-loan-gl-entries --preview
    bench --site <sitename> regenerate-loan-gl-entries --limit 50
    bench --site <sitename> regenerate-loan-gl-entries
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate
from erpnext.accounts.general_ledger import make_gl_entries


def get_loan_repayments_without_gl_entries():
    """Get all submitted Loan Repayments that don't have GL entries"""
    
    # Get all submitted Loan Repayments
    submitted_lr = frappe.get_all('Loan Repayment',
        filters={'docstatus': 1},
        fields=['name', 'amount_paid', 'posting_date', 'payment_account', 'against_loan', 
                'applicant', 'applicant_type', 'company'],
        order_by='posting_date'
    )
    
    # Get LRs with GL Entries
    lr_with_gl = frappe.db.sql("""
        SELECT DISTINCT voucher_no 
        FROM `tabGL Entry` 
        WHERE voucher_type = 'Loan Repayment' 
        AND is_cancelled = 0
    """, as_list=True)
    lr_with_gl_set = set([x[0] for x in lr_with_gl])
    
    # Find ones without GL entries
    lr_without_gl = [lr for lr in submitted_lr if lr['name'] not in lr_with_gl_set]
    
    return lr_without_gl


def create_gl_entries_for_loan_repayment(doc):
    """
    Create GL entries for a loan repayment that's missing them.
    
    This handles the case where repayments were imported without triggering
    the normal on_submit hooks.
    
    GL entries created:
    1. Debit: Payment Account (bank/cash) - Money received
    2. Credit: Loan Account - Reducing the loan receivable
    """
    
    precision = cint(frappe.db.get_default("currency_precision")) or 2
    
    # Get payment account
    payment_account = doc.payment_account
    if not payment_account:
        loan = frappe.get_doc('Loan', doc.against_loan)
        payment_account = loan.payment_account
    
    # Get loan account
    loan_account = doc.loan_account
    if not loan_account:
        loan = frappe.get_doc('Loan', doc.against_loan)
        loan_account = loan.loan_account
    
    if not payment_account or not loan_account:
        raise ValueError(f"Missing payment_account ({payment_account}) or loan_account ({loan_account})")
    
    # Calculate amount to post
    # Use principal_amount_paid if available, otherwise use amount_paid
    amount = flt(doc.principal_amount_paid, precision) or flt(doc.amount_paid, precision)
    
    if amount <= 0:
        return 0
    
    remarks = f"Loan Repayment against Loan: {doc.against_loan}"
    
    gle_map = []
    
    # Debit: Payment Account (money received)
    # Use the document's get_gl_dict method to get proper GL Entry structure
    gle_map.append(
        doc.get_gl_dict(
            {
                "account": payment_account,
                "against": loan_account,
                "debit": amount,
                "debit_in_account_currency": amount,
                "against_voucher_type": "Loan",
                "against_voucher": doc.against_loan,
                "remarks": remarks,
                "cost_center": doc.cost_center,
                "posting_date": getdate(doc.posting_date),
            },
            item=doc,
        )
    )
    
    # Credit: Loan Account (reducing loan receivable)
    gle_map.append(
        doc.get_gl_dict(
            {
                "account": loan_account,
                "party_type": doc.applicant_type,
                "party": doc.applicant,
                "against": payment_account,
                "credit": amount,
                "credit_in_account_currency": amount,
                "against_voucher_type": "Loan",
                "against_voucher": doc.against_loan,
                "remarks": remarks,
                "cost_center": doc.cost_center,
                "posting_date": getdate(doc.posting_date),
            },
            item=doc,
        )
    )
    
    # Create GL Entries
    if gle_map:
        make_gl_entries(gle_map, merge_entries=False)
    
    return len(gle_map)


def regenerate_gl_for_loan_repayment(loan_repayment_name, dry_run=False):
    """Regenerate GL entries for a single Loan Repayment"""
    
    try:
        doc = frappe.get_doc('Loan Repayment', loan_repayment_name)
        
        if doc.docstatus != 1:
            return {
                'status': 'skipped',
                'reason': f'Document is not submitted (docstatus={doc.docstatus})'
            }
        
        # Check if GL entries already exist
        existing_gl = frappe.db.count('GL Entry', {
            'voucher_type': 'Loan Repayment',
            'voucher_no': loan_repayment_name,
            'is_cancelled': 0
        })
        
        if existing_gl > 0:
            return {
                'status': 'skipped',
                'reason': f'GL entries already exist ({existing_gl} entries)'
            }
        
        if dry_run:
            return {
                'status': 'would_create',
                'amount': doc.amount_paid,
                'posting_date': doc.posting_date
            }
        
        # Create GL entries directly using our custom function
        # This handles the case where the standard make_gl_entries doesn't work
        # because repayment_details is empty and pending_principal_amount is 0
        gl_count = create_gl_entries_for_loan_repayment(doc)
        
        return {
            'status': 'success',
            'gl_entries_created': gl_count,
            'amount': doc.amount_paid
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def regenerate_missing_gl_entries(preview=False, limit=None):
    """
    Regenerate GL entries for all Loan Repayments that are missing them.
    
    Args:
        preview: If True, only show what would be done without making changes
        limit: Maximum number of repayments to process
    """
    
    print("\n" + "="*60)
    print("REGENERATING GL ENTRIES FOR LOAN REPAYMENTS")
    print("="*60)
    
    # Get loan repayments without GL entries
    lr_without_gl = get_loan_repayments_without_gl_entries()
    
    print(f"\nFound {len(lr_without_gl)} Loan Repayments without GL entries")
    
    if limit:
        lr_without_gl = lr_without_gl[:int(limit)]
        print(f"Processing first {limit} repayments")
    
    if preview:
        print("\n*** PREVIEW MODE - No changes will be made ***\n")
    
    # Statistics
    stats = {
        'processed': 0,
        'success': 0,
        'skipped': 0,
        'errors': 0,
        'total_amount': 0
    }
    
    errors = []
    
    for i, lr in enumerate(lr_without_gl, 1):
        print(f"\n[{i}/{len(lr_without_gl)}] Processing {lr['name']}...")
        print(f"  Loan: {lr['against_loan']}")
        print(f"  Amount: {lr['amount_paid']}")
        print(f"  Date: {lr['posting_date']}")
        
        result = regenerate_gl_for_loan_repayment(lr['name'], dry_run=preview)
        
        stats['processed'] += 1
        
        if result['status'] == 'success':
            stats['success'] += 1
            stats['total_amount'] += float(lr['amount_paid'])
            print(f"  ✅ SUCCESS - Created {result['gl_entries_created']} GL entries")
            
        elif result['status'] == 'would_create':
            stats['success'] += 1
            stats['total_amount'] += float(lr['amount_paid'])
            print(f"  📋 Would create GL entries (preview mode)")
            
        elif result['status'] == 'skipped':
            stats['skipped'] += 1
            print(f"  ⏭️  SKIPPED - {result['reason']}")
            
        elif result['status'] == 'error':
            stats['errors'] += 1
            errors.append({'name': lr['name'], 'error': result['error']})
            print(f"  ❌ ERROR - {result['error']}")
        
        # Commit every 50 records to avoid memory issues
        if not preview and i % 50 == 0:
            frappe.db.commit()
            print(f"\n--- Committed {i} records ---\n")
    
    # Final commit
    if not preview:
        frappe.db.commit()
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Processed: {stats['processed']}")
    print(f"Successfully Created GL Entries: {stats['success']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")
    print(f"Total Amount Processed: {stats['total_amount']:,.2f}")
    
    if errors:
        print("\n" + "-"*40)
        print("ERRORS:")
        print("-"*40)
        for err in errors[:20]:  # Show first 20 errors
            print(f"  {err['name']}: {err['error']}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
    
    return stats


@frappe.whitelist()
def preview_missing_gl_entries():
    """API to preview Loan Repayments missing GL entries"""
    
    lr_without_gl = get_loan_repayments_without_gl_entries()
    
    total_amount = sum([float(lr['amount_paid']) for lr in lr_without_gl])
    
    # Group by month
    from collections import defaultdict
    by_month = defaultdict(lambda: {'count': 0, 'amount': 0})
    for lr in lr_without_gl:
        key = str(lr['posting_date'])[:7]
        by_month[key]['count'] += 1
        by_month[key]['amount'] += float(lr['amount_paid'])
    
    return {
        'total_count': len(lr_without_gl),
        'total_amount': total_amount,
        'by_month': dict(by_month),
        'sample': lr_without_gl[:20]  # First 20 as sample
    }


@frappe.whitelist()
def regenerate_gl_entries_api(limit=None):
    """API to regenerate GL entries"""
    
    frappe.only_for('System Manager')
    
    stats = regenerate_missing_gl_entries(preview=False, limit=limit)
    
    return stats


# Bench command function
def execute(preview=False, limit=None):
    """Entry point for bench execute command"""
    regenerate_missing_gl_entries(preview=preview, limit=limit)
