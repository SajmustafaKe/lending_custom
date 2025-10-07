from lending.loan_management.doctype.loan_repayment.loan_repayment import LoanRepayment
import frappe
from frappe import _
from frappe.utils import get_datetime

class LoanRepaymentOverride(LoanRepayment):
	def check_future_entries(self):
		"""
		Override the check_future_entries method to allow overriding the validation
		for specific conditions (e.g., corrections or authorized users)
		"""
		# Check if user has permission to override or if it's marked as a correction
		if self.has_permission("override_repayment_validation") or getattr(self, 'is_correction_entry', False):
			# Skip the future entries check
			frappe.msgprint(_("Repayment date validation overridden for correction entry."), indicator="orange")
			return

		# Original validation logic
		future_repayment_date = frappe.db.get_value(
			"Loan Repayment",
			{"posting_date": (">", self.posting_date), "docstatus": 1, "against_loan": self.against_loan},
			"posting_date",
		)

		if future_repayment_date:
			frappe.throw("Repayment already made till date {0}".format(get_datetime(future_repayment_date)))