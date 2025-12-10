import frappe
from frappe import _


@frappe.whitelist()
def get_mint_document_types_for_bank_reconciliation():
    """
    Get all document types for bank reconciliation including loan document types
    for the mint app
    """
    from erpnext.accounts.doctype.bank_transaction.bank_transaction import get_doctypes_for_bank_reconciliation
    
    doctypes = get_doctypes_for_bank_reconciliation()
    
    # Convert to the format expected by mint app
    formatted_types = []
    for doctype in doctypes:
        # Convert to snake_case for mint app compatibility
        snake_case = frappe.scrub(doctype)
        formatted_types.append({
            'label': doctype,
            'value': snake_case,
            'id': snake_case
        })
    
    return formatted_types


@frappe.whitelist()
def get_extended_match_filters():
    """
    Get extended match filters including loan document types
    """
    base_filters = ['payment_entry', 'journal_entry', 'purchase_invoice', 'sales_invoice', 'expense_claim', 'bank_transaction']
    loan_filters = ['loan_repayment', 'loan_disbursement']
    
    return base_filters + loan_filters