"""
Enhanced Auto Reconciliation for Loan Repayments

This script provides automatic bank reconciliation for Loan Repayments by matching:
- reference_number on Loan Repayment == reference_number on Bank Transaction
- amount_paid on Loan Repayment == deposit on Bank Transaction
- posting_date on Loan Repayment == date on Bank Transaction

Usage:
    - Via bench command: bench --site [site] execute lending_custom.loan_auto_reconciliation.auto_reconcile_loan_repayments
    - Via API: frappe.call("lending_custom.loan_auto_reconciliation.auto_reconcile_loan_repayments")
"""

import json

import frappe
from frappe import _
from frappe.utils import flt, getdate


@frappe.whitelist()
def auto_reconcile_loan_repayments(bank_account=None, from_date=None, to_date=None):
    """
    Auto reconcile Loan Repayments with Bank Transactions based on exact matching criteria:
    - reference_number matches
    - amount matches (deposit == amount_paid)
    - date matches (date == posting_date)
    
    Args:
        bank_account: Optional - Specific bank account to reconcile
        from_date: Optional - Filter bank transactions from this date
        to_date: Optional - Filter bank transactions to this date
    
    Returns:
        dict: Summary of reconciliation results
    """
    frappe.flags.auto_reconcile_vouchers = True
    
    # Get unreconciled bank transactions
    bank_transactions = get_unreconciled_bank_transactions(bank_account, from_date, to_date)
    
    reconciled = []
    failed = []
    skipped = []
    
    for transaction in bank_transactions:
        try:
            result = reconcile_single_transaction(transaction)
            if result.get("status") == "reconciled":
                reconciled.append(result)
            elif result.get("status") == "skipped":
                skipped.append(result)
        except Exception as e:
            frappe.log_error(
                title=f"Auto Reconciliation Error for {transaction.name}",
                message=str(e)
            )
            failed.append({
                "bank_transaction": transaction.name,
                "error": str(e)
            })
    
    frappe.flags.auto_reconcile_vouchers = False
    
    # Generate summary
    summary = {
        "total_processed": len(bank_transactions),
        "reconciled": len(reconciled),
        "skipped": len(skipped),
        "failed": len(failed),
        "reconciled_details": reconciled,
        "failed_details": failed
    }
    
    # Show message to user
    if reconciled:
        frappe.msgprint(
            _("{0} Bank Transaction(s) reconciled with Loan Repayments").format(len(reconciled)),
            title=_("Auto Reconciliation Complete"),
            indicator="green"
        )
    else:
        frappe.msgprint(
            _("No matching Loan Repayments found for reconciliation"),
            title=_("Auto Reconciliation Complete"),
            indicator="blue"
        )
    
    return summary


def get_unreconciled_bank_transactions(bank_account=None, from_date=None, to_date=None, limit=1000):
    """
    Get all unreconciled bank transactions (deposits only for loan repayments)
    """
    bt = frappe.qb.DocType("Bank Transaction")
    
    query = (
        frappe.qb.from_(bt)
        .select(
            bt.name,
            bt.date,
            bt.deposit,
            bt.withdrawal,
            bt.reference_number,
            bt.bank_account,
            bt.unallocated_amount,
            bt.status,
            bt.party_type,
            bt.party
        )
        .where(bt.docstatus == 1)
        .where(bt.status.isin(["Pending", "Unreconciled"]))
        .where(bt.deposit > 0)  # Only deposits for loan repayments
        .where(bt.unallocated_amount > 0)
        .where(bt.reference_number.isnotnull())
        .where(bt.reference_number != "")
        .orderby(bt.date)
        .limit(limit)
    )
    
    if bank_account:
        query = query.where(bt.bank_account == bank_account)
    
    if from_date:
        query = query.where(bt.date >= getdate(from_date))
    
    if to_date:
        query = query.where(bt.date <= getdate(to_date))
    
    return query.run(as_dict=True)


def reconcile_single_transaction(transaction):
    """
    Try to reconcile a single bank transaction with a matching Loan Repayment
    
    Matching criteria:
    - reference_number on Loan Repayment == reference_number on Bank Transaction
    - amount_paid on Loan Repayment == deposit on Bank Transaction
    - posting_date on Loan Repayment == date on Bank Transaction
    """
    # Get bank account's GL account
    bank_account_info = frappe.db.get_value(
        "Bank Account", 
        transaction.bank_account, 
        ["account", "company"], 
        as_dict=True
    )
    
    if not bank_account_info:
        return {
            "status": "skipped",
            "bank_transaction": transaction.name,
            "reason": "Bank account not found"
        }
    
    # Find matching Loan Repayment
    matching_repayment = find_matching_loan_repayment(
        reference_number=transaction.reference_number,
        amount=transaction.deposit,
        date=transaction.date,
        payment_account=bank_account_info.account
    )
    
    if not matching_repayment:
        return {
            "status": "skipped",
            "bank_transaction": transaction.name,
            "reason": "No matching Loan Repayment found"
        }
    
    # Perform reconciliation
    try:
        reconcile_bank_transaction_with_loan_repayment(
            transaction.name, 
            matching_repayment
        )
        
        return {
            "status": "reconciled",
            "bank_transaction": transaction.name,
            "loan_repayment": matching_repayment.name,
            "amount": matching_repayment.amount_paid,
            "reference_number": matching_repayment.reference_number
        }
    except Exception as e:
        return {
            "status": "skipped",
            "bank_transaction": transaction.name,
            "reason": str(e)
        }


def find_matching_loan_repayment(reference_number, amount, date, payment_account):
    """
    Find a Loan Repayment that exactly matches the bank transaction criteria:
    - Same reference number
    - Same amount
    - Same date
    - Same payment account
    - Not already reconciled (clearance_date is null)
    """
    lr = frappe.qb.DocType("Loan Repayment")
    
    query = (
        frappe.qb.from_(lr)
        .select(
            lr.name,
            lr.amount_paid,
            lr.reference_number,
            lr.posting_date,
            lr.applicant_type,
            lr.applicant,
            lr.against_loan
        )
        .where(lr.docstatus == 1)
        .where(lr.clearance_date.isnull())
        .where(lr.reference_number == reference_number)
        .where(lr.amount_paid == flt(amount))
        .where(lr.posting_date == getdate(date))
        .where(lr.payment_account == payment_account)
    )
    
    # Handle repay_from_salary field if it exists
    if frappe.db.has_column("Loan Repayment", "repay_from_salary"):
        query = query.where((lr.repay_from_salary == 0))
    
    results = query.run(as_dict=True)
    
    if results:
        return results[0]
    
    return None


def reconcile_bank_transaction_with_loan_repayment(bank_transaction_name, loan_repayment):
    """
    Reconcile the bank transaction with the loan repayment
    """
    from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import (
        reconcile_vouchers
    )
    
    vouchers = json.dumps([
        {
            "payment_doctype": "Loan Repayment",
            "payment_name": loan_repayment.name,
            "amount": flt(loan_repayment.amount_paid)
        }
    ])
    
    reconcile_vouchers(bank_transaction_name, vouchers)


@frappe.whitelist()
def get_loan_repayment_reconciliation_preview(bank_account=None, from_date=None, to_date=None, limit=100):
    """
    Preview which bank transactions can be reconciled with loan repayments
    without actually performing the reconciliation
    
    Returns a list of potential matches
    """
    bank_transactions = get_unreconciled_bank_transactions(bank_account, from_date, to_date, limit)
    
    if not bank_transactions:
        return []
    
    # Get all reference numbers from bank transactions
    reference_numbers = [t.reference_number for t in bank_transactions if t.reference_number]
    
    if not reference_numbers:
        return []
    
    # Batch query for all potentially matching loan repayments
    lr = frappe.qb.DocType("Loan Repayment")
    
    query = (
        frappe.qb.from_(lr)
        .select(
            lr.name,
            lr.amount_paid,
            lr.reference_number,
            lr.posting_date,
            lr.applicant_type,
            lr.applicant,
            lr.against_loan,
            lr.payment_account
        )
        .where(lr.docstatus == 1)
        .where(lr.clearance_date.isnull())
        .where(lr.reference_number.isin(reference_numbers))
    )
    
    # Handle repay_from_salary field if it exists
    if frappe.db.has_column("Loan Repayment", "repay_from_salary"):
        query = query.where((lr.repay_from_salary == 0))
    
    loan_repayments = query.run(as_dict=True)
    
    # Create lookup dictionaries
    lr_by_ref = {}
    for lr_doc in loan_repayments:
        # Convert datetime to date for proper comparison
        lr_date = getdate(lr_doc.posting_date) if lr_doc.posting_date else None
        key = (lr_doc.reference_number, str(lr_date), flt(lr_doc.amount_paid), lr_doc.payment_account)
        lr_by_ref[key] = lr_doc
    
    # Get bank account to GL account mapping
    bank_accounts = list(set(t.bank_account for t in bank_transactions))
    ba_to_gl = {}
    for ba in bank_accounts:
        gl_account = frappe.db.get_value("Bank Account", ba, "account")
        if gl_account:
            ba_to_gl[ba] = gl_account
    
    matches = []
    
    for transaction in bank_transactions:
        if transaction.bank_account not in ba_to_gl:
            continue
        
        gl_account = ba_to_gl[transaction.bank_account]
        # Convert transaction date to date for proper comparison
        bt_date = getdate(transaction.date) if transaction.date else None
        key = (transaction.reference_number, str(bt_date), flt(transaction.deposit), gl_account)
        
        if key in lr_by_ref:
            lr_doc = lr_by_ref[key]
            matches.append({
                "bank_transaction": transaction.name,
                "bank_transaction_date": transaction.date,
                "bank_transaction_amount": transaction.deposit,
                "bank_transaction_reference": transaction.reference_number,
                "loan_repayment": lr_doc.name,
                "loan_repayment_amount": lr_doc.amount_paid,
                "loan_repayment_date": lr_doc.posting_date,
                "loan": lr_doc.against_loan,
                "applicant": lr_doc.applicant
            })
    
    return matches


@frappe.whitelist()
def reconcile_selected_transactions(transactions):
    """
    Reconcile specific bank transactions with their matching loan repayments
    
    Args:
        transactions: JSON string of list of bank transaction names
    """
    if isinstance(transactions, str):
        transactions = json.loads(transactions)
    
    results = []
    
    for bt_name in transactions:
        transaction = frappe.db.get_value(
            "Bank Transaction",
            bt_name,
            ["name", "date", "deposit", "reference_number", "bank_account", "unallocated_amount"],
            as_dict=True
        )
        
        if not transaction:
            results.append({
                "status": "failed",
                "bank_transaction": bt_name,
                "error": "Bank Transaction not found"
            })
            continue
        
        result = reconcile_single_transaction(transaction)
        results.append(result)
    
    reconciled_count = sum(1 for r in results if r.get("status") == "reconciled")
    
    if reconciled_count:
        frappe.msgprint(
            _("{0} Bank Transaction(s) reconciled").format(reconciled_count),
            indicator="green"
        )
    
    return results
