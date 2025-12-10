import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.bank_transaction.bank_transaction import BankTransaction


class BankTransactionOverride(BankTransaction):
	"""
	Override Bank Transaction to support Loan Repayments in reconciliation
	"""
	
	def get_payment_entry_amount(self, payment_entry_doc):
		"""
		Override to handle Loan Repayment documents
		"""
		if payment_entry_doc.get("payment_document") == "Loan Repayment":
			return self.get_loan_repayment_amount(payment_entry_doc.get("payment_entry"))
		else:
			# Call parent method for other document types
			return super().get_payment_entry_amount(payment_entry_doc)
	
	def get_loan_repayment_amount(self, loan_repayment_name):
		"""
		Get the amount from a Loan Repayment document
		"""
		return flt(frappe.db.get_value("Loan Repayment", loan_repayment_name, "amount_paid")) or 0.0
	
	def get_clearance_details_for_loan_repayment(self, payment_entry_doc, pe_allocations, gl_entries):
		"""
		Calculate clearance details for Loan Repayment documents
		"""
		loan_repayment_name = payment_entry_doc.get("payment_entry")
		
		# Get the total amount from the loan repayment
		total_amount = self.get_loan_repayment_amount(loan_repayment_name)
		
		# Calculate already allocated amount from other bank transactions
		allocated_amount = sum(pe_allocations.values()) if pe_allocations else 0
		
		# Calculate allocable amount
		allocable_amount = total_amount - allocated_amount
		
		# Get posting date for clearance
		posting_date = frappe.db.get_value("Loan Repayment", loan_repayment_name, "posting_date")
		
		# Should clear if allocable amount matches remaining or is fully allocated
		should_clear = allocable_amount > 0
		
		return allocable_amount, should_clear, posting_date