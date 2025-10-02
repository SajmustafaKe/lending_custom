import frappe
from frappe import _
from frappe.utils import flt, cint, date_diff, getdate, add_days, get_last_day, add_months
import math

from lending.loan_management.doctype.loan_application.loan_application import LoanApplication
from lending_custom.interest_calculations import (
	calculate_payable_amount_custom,
	get_per_day_interest_custom
)


class LoanApplicationOverride(LoanApplication):
	def validate(self):
		# Set interest calculation method from loan product if not set
		if not self.interest_calculation_method and self.loan_product:
			self.interest_calculation_method = frappe.db.get_value(
				"Loan Product", self.loan_product, "interest_calculation_method"
			) or "Monthly Prorated"

		# Call parent validate
		super().validate()

	def get_repayment_details(self):
		"""Calculate repayment details based on repayment method and interest calculation method"""
		if self.is_term_loan:
			if self.repayment_method == "Repay Over Number of Periods":
				from lending_custom.interest_calculations import get_monthly_repayment_amount_custom
				self.repayment_amount = get_monthly_repayment_amount_custom(
					self.loan_amount, self.rate_of_interest, self.repayment_periods, self.interest_calculation_method
				)
				print(f"DEBUG: Calculated repayment_amount = {self.repayment_amount}")

			if self.repayment_method == "Repay Fixed Amount per Period":
				if self.interest_calculation_method == "One-time Percentage":
					# For one-time percentage, calculate periods based on total amount
					total_amount = self.loan_amount * (1 + self.rate_of_interest / 100)
					if self.repayment_amount and self.repayment_amount > 0:
						self.repayment_periods = math.ceil(total_amount / self.repayment_amount)
					else:
						self.repayment_periods = 1
				else:
					# Original calculation for monthly prorated
					monthly_interest_rate = flt(self.rate_of_interest) / (12 * 100)
					if monthly_interest_rate:
						min_repayment_amount = self.loan_amount * monthly_interest_rate
						if self.repayment_amount - min_repayment_amount <= 0:
							frappe.throw(_("Repayment Amount must be greater than " + str(flt(min_repayment_amount, 2))))
						self.repayment_periods = math.ceil(
							(math.log(self.repayment_amount) - math.log(self.repayment_amount - min_repayment_amount))
							/ (math.log(1 + monthly_interest_rate))
						)
					else:
						self.repayment_periods = math.ceil(self.loan_amount / self.repayment_amount)

			# Use custom payable amount calculation
			calculate_payable_amount_custom(self)
		else:
			self.total_payable_amount = self.loan_amount