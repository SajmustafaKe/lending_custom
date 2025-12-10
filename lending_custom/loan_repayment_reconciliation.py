import frappe
import json
from frappe import _
from frappe.utils import flt


def get_loan_repayments_for_bank_reconciliation(
	bank_account, from_date=None, to_date=None, filter_by_reference_date=None, reference_date=None
):
	"""
	Get Loan Repayments for bank reconciliation matching
	"""
	conditions = []
	params = [bank_account]
	
	if from_date:
		conditions.append("lr.posting_date >= %s")
		params.append(from_date)
		
	if to_date:
		conditions.append("lr.posting_date <= %s")
		params.append(to_date)
		
	if filter_by_reference_date and reference_date:
		conditions.append("lr.reference_date = %s")
		params.append(reference_date)
	
	where_clause = ""
	if conditions:
		where_clause = "AND " + " AND ".join(conditions)
	
	query = """
		SELECT 
			lr.name,
			lr.posting_date,
			lr.amount_paid,
			lr.reference_number,
			lr.reference_date,
			lr.against_loan,
			l.applicant_type,
			l.applicant,
			'Loan Repayment' as payment_doctype,
			lr.name as payment_name
		FROM `tabLoan Repayment` lr
		INNER JOIN `tabLoan` l ON lr.against_loan = l.name
		WHERE lr.docstatus = 1 
		AND lr.payment_account = %s
		{where_clause}
		ORDER BY lr.posting_date DESC
	""".format(where_clause=where_clause)
	
	return frappe.db.sql(query, params, as_dict=True)


@frappe.whitelist()
def reconcile_loan_repayments_with_bank_transaction(bank_transaction_name, loan_repayments):
	"""
	Reconcile selected loan repayments with a bank transaction
	"""
	loan_repayments = json.loads(loan_repayments) if isinstance(loan_repayments, str) else loan_repayments
	
	vouchers = []
	for repayment in loan_repayments:
		vouchers.append({
			"payment_doctype": "Loan Repayment",
			"payment_name": repayment["name"],
			"amount": repayment["amount_paid"]
		})
	
	# Use the existing reconcile_vouchers function
	from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import reconcile_vouchers
	
	return reconcile_vouchers(bank_transaction_name, json.dumps(vouchers))


@frappe.whitelist() 
def get_loan_repayment_amount_for_bank_reconciliation(loan_repayment_name):
	"""
	Get the loan repayment amount for bank reconciliation
	This is used by the bank transaction allocation logic
	"""
	return frappe.db.get_value("Loan Repayment", loan_repayment_name, "amount_paid") or 0


def get_loan_repayment_gl_entries(loan_repayment_name, bank_account):
	"""
	Get GL entries for loan repayment for the specific bank account
	This helps in calculating allocated amounts
	"""
	return frappe.db.sql("""
		SELECT posting_date, debit, credit
		FROM `tabGL Entry`
		WHERE voucher_type = 'Loan Repayment' 
		AND voucher_no = %s 
		AND account = %s
		AND docstatus = 1
	""", (loan_repayment_name, bank_account), as_dict=True)