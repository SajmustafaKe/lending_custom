import frappe
from frappe.utils import nowdate, getdate, add_days, date_diff

from lending.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual import ProcessLoanInterestAccrual
from lending.loan_management.doctype.loan_interest_accrual.loan_interest_accrual import (
	make_accrual_interest_entry_for_demand_loans,
	make_accrual_interest_entry_for_term_loans,
)


class ProcessLoanInterestAccrualOverride(ProcessLoanInterestAccrual):
	def on_submit(self):
		"""Override to support date range processing for historical accruals"""
		open_loans = []
		loan_doc = None

		if self.loan:
			loan_doc = frappe.get_doc("Loan", self.loan)
			if loan_doc:
				open_loans.append(loan_doc)

		# Check if date range is provided for batch processing
		if hasattr(self, 'start_date') and hasattr(self, 'end_date') and self.start_date and self.end_date:
			start = getdate(self.start_date)
			end = getdate(self.end_date)
			
			# Process each date in the range
			current_date = start
			while current_date <= end:
				self._process_for_date(current_date, open_loans, loan_doc)
				current_date = add_days(current_date, 1)
		else:
			# Single date processing (original behavior)
			self._process_for_date(getdate(self.posting_date), open_loans, loan_doc)

	def _process_for_date(self, posting_date, open_loans, loan_doc):
		"""Process accrual for a specific date"""
		# Process demand loans when process_type is not set or is "Demand Loans"
		if (not self.loan or (loan_doc and not loan_doc.is_term_loan)) and (not self.process_type or self.process_type != "Term Loans"):
			make_accrual_interest_entry_for_demand_loans(
				posting_date,
				self.name,
				open_loans=open_loans,
				loan_product=self.loan_product,
				accrual_type=self.accrual_type or "Regular",
			)

		# Process term loans when process_type is not set or is "Term Loans"
		if (not self.loan or (loan_doc and loan_doc.is_term_loan)) and (not self.process_type or self.process_type != "Demand Loans"):
			make_accrual_interest_entry_for_term_loans(
				posting_date,
				self.name,
				term_loan=self.loan,
				loan_product=self.loan_product,
				accrual_type=self.accrual_type or "Regular",
			)