import frappe
from frappe import _


def extend_bank_reconciliation_with_loan_repayments():
	"""
	Monkey patch the bank reconciliation tool to include Loan Repayments
	"""
	from erpnext.accounts.doctype.bank_reconciliation_tool import bank_reconciliation_tool
	
	# Store original function
	original_get_linked_payments = bank_reconciliation_tool.get_linked_payments
	
	def get_linked_payments_with_loan_repayments(
		bank_transaction_name,
		document_types=None,
		from_date=None,
		to_date=None,
		filter_by_reference_date=None,
		from_reference_date=None,
		to_reference_date=None,
	):
		"""
		Extended version that includes Loan Repayments
		"""
		# Get original results
		results = original_get_linked_payments(
			bank_transaction_name,
			document_types,
			from_date,
			to_date,
			filter_by_reference_date,
			from_reference_date,
			to_reference_date
		)
		
		# If Loan Repayment is in document_types or document_types is None, add loan repayments
		if not document_types or "loan_repayment" in document_types:
			bank_account = frappe.db.get_value("Bank Transaction", bank_transaction_name, "bank_account")
			
			if bank_account:
				# Import our custom function
				from lending_custom.loan_repayment_reconciliation import get_loan_repayments_for_bank_reconciliation
				
				loan_repayments = get_loan_repayments_for_bank_reconciliation(
					bank_account=bank_account,
					from_date=from_date,
					to_date=to_date,
					filter_by_reference_date=filter_by_reference_date,
					reference_date=from_reference_date if filter_by_reference_date else None
				)
				
				# Format loan repayments to match expected structure
				for lr in loan_repayments:
					lr.update({
						"doctype": "Loan Repayment",
						"name": lr["name"],
						"reference_date": lr.get("reference_date"),
						"posting_date": lr.get("posting_date"),
						"paid_amount": lr["amount_paid"],
						"reference_no": lr.get("reference_number"),
						"party_type": lr.get("applicant_type"),
						"party": lr.get("applicant"),
						"currency": frappe.get_cached_value("Company", 
							frappe.db.get_value("Bank Transaction", bank_transaction_name, "company"), 
							"default_currency"
						)
					})
				
				# Add to results
				if not results:
					results = loan_repayments
				else:
					results.extend(loan_repayments)
		
		return results
	
	# Replace the function
	bank_reconciliation_tool.get_linked_payments = get_linked_payments_with_loan_repayments
	
	frappe.logger().info("Bank reconciliation extended with Loan Repayment support")