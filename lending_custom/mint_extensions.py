import frappe

def extend_mint_bank_reconciliation(bootinfo=None):
    """
    Extend mint app's bank reconciliation to include Loan Repayment and Loan Disbursement
    """
    # This function is called during boot session
    # The actual mint app updates are handled by the patch system
    pass