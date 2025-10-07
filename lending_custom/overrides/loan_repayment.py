import frappe
from frappe import _
from lending.loan_management.doctype.loan_repayment.loan_repayment import LoanRepayment


class LoanRepaymentOverride(LoanRepayment):
	def check_future_entries(self):
		"""
		Override the check_future_entries method to allow repayments
		even if future repayments exist (for one-time percentage loans)
		"""
		# Get the loan's interest calculation method
		interest_calc_method = frappe.db.get_value("Loan", self.against_loan, "interest_calculation_method")

		if interest_calc_method == "One-time Percentage":
			# For one-time percentage loans, allow repayments even if future entries exist
			# This bypasses the standard validation that prevents overlapping repayment dates
			return

		# For monthly prorated loans, use the original validation
		future_repayment_date = frappe.db.get_value(
			"Loan Repayment",
			{"posting_date": (">", self.posting_date), "docstatus": 1, "against_loan": self.against_loan},
			"posting_date",
		)

		if future_repayment_date:
			frappe.throw("Repayment already made till date {0}".format(frappe.utils.get_datetime(future_repayment_date)))