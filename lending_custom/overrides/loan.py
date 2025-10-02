import frappe
from frappe import _
from frappe.utils import flt, cint, date_diff, getdate, add_days, get_last_day, add_months
import math

from lending.loan_management.doctype.loan.loan import Loan
from lending_custom.interest_calculations import (
	calculate_payable_amount_custom,
	get_per_day_interest_custom
)


class LoanOverride(Loan):
	def validate(self):
		# Set interest calculation method from loan product if not set
		if not self.interest_calculation_method and self.loan_product:
			self.interest_calculation_method = frappe.db.get_value(
				"Loan Product", self.loan_product, "interest_calculation_method"
			) or "Monthly Prorated"
			print(f"DEBUG Loan.validate: Set interest_calculation_method to {self.interest_calculation_method} from loan_product {self.loan_product}")

		print(f"DEBUG Loan.validate: interest_calculation_method={self.interest_calculation_method}, loan_product={self.loan_product}")

		# Set loan amount if not set
		self.set_loan_amount()

		# Calculate repayment details for term loans
		if self.is_term_loan:
			self.calculate_repayment_details()

		# Call parent validate
		super().validate()

	def after_insert(self):
		# Handle term loan schedule creation ourselves to avoid duplicate schedules
		if self.is_term_loan:
			self.make_draft_schedule()
			# Don't call calculate_totals here - it will be called by the system when needed
		# Don't call super().after_insert() to prevent duplicate schedule creation

	def calculate_repayment_details(self):
		"""Calculate repayment details based on repayment method and interest calculation method"""
		print(f"DEBUG Loan.calculate_repayment_details: START - method={self.repayment_method}, interest_calc={self.interest_calculation_method}, loan_amount={self.loan_amount}, rate={self.rate_of_interest}, periods={self.repayment_periods}")
		
		# Skip if required fields are not set
		if not self.loan_amount or not self.rate_of_interest:
			return
			
		if self.repayment_method == "Repay Over Number of Periods":
			from lending_custom.interest_calculations import get_monthly_repayment_amount_custom
			self.monthly_repayment_amount = get_monthly_repayment_amount_custom(
				self.loan_amount, self.rate_of_interest, self.repayment_periods, self.interest_calculation_method
			)
			print(f"DEBUG Loan: Calculated monthly_repayment_amount = {self.monthly_repayment_amount}")

		if self.repayment_method == "Repay Fixed Amount per Period":
			if self.interest_calculation_method == "One-time Percentage":
				# For one-time percentage, calculate periods based on total amount
				total_amount = self.loan_amount * (1 + self.rate_of_interest / 100)
				if self.monthly_repayment_amount and self.monthly_repayment_amount > 0:
					self.repayment_periods = math.ceil(total_amount / self.monthly_repayment_amount)
				else:
					self.repayment_periods = 1
				print(f"DEBUG Loan: One-time percentage - total_amount={total_amount}, periods={self.repayment_periods}")
			else:
				# Original calculation for monthly prorated
				if not self.monthly_repayment_amount:
					return
				monthly_interest_rate = flt(self.rate_of_interest) / (12 * 100)
				if monthly_interest_rate:
					min_repayment_amount = self.loan_amount * monthly_interest_rate
					if self.monthly_repayment_amount - min_repayment_amount <= 0:
						frappe.throw(_("Monthly Repayment Amount must be greater than " + str(flt(min_repayment_amount, 2))))
					self.repayment_periods = math.ceil(
						(math.log(self.monthly_repayment_amount) - math.log(self.monthly_repayment_amount - min_repayment_amount))
						/ (math.log(1 + monthly_interest_rate))
					)
				else:
					self.repayment_periods = math.ceil(self.loan_amount / self.monthly_repayment_amount)

		# Calculate total payable amount and interest
		self.calculate_total_payable()
		print(f"DEBUG Loan.calculate_repayment_details: END - monthly_repayment_amount={self.monthly_repayment_amount}")

	def calculate_total_payable(self):
		"""Calculate total payable amount and interest based on interest calculation method"""
		if self.interest_calculation_method == "One-time Percentage":
			# For one-time percentage, calculate total interest upfront
			self.total_interest_payable = self.loan_amount * (self.rate_of_interest / 100)
			self.total_payment = self.loan_amount + self.total_interest_payable
			print(f"DEBUG Loan.calculate_total_payable: One-time percentage - total_payment={self.total_payment}, total_interest_payable={self.total_interest_payable}")
		else:
			# Use the original calculation for monthly prorated
			print(f"DEBUG Loan.calculate_total_payable: Using original calculation for method={self.interest_calculation_method}")
			# Call the parent method or implement the original logic
			# For now, we'll set basic values - the original logic would be more complex
			# This is a simplified version
			if hasattr(super(), 'calculate_total_payable'):
				super().calculate_total_payable()
			else:
				# Fallback calculation
				self.total_payment = self.loan_amount
				self.total_interest_payable = 0

	def calculate_totals(self, on_insert=False):
		"""Override to prevent original calculate_totals from overriding our custom calculations"""
		print(f"DEBUG Loan.calculate_totals: on_insert={on_insert}, interest_calculation_method={self.interest_calculation_method}")

		if self.interest_calculation_method == "One-time Percentage":
			# For one-time percentage, we've already calculated the totals in calculate_total_payable
			# Just ensure the schedule values are correct
			if self.is_term_loan and on_insert:
				schedule = frappe.get_doc("Loan Repayment Schedule", {"loan": self.name, "docstatus": 0})
				# Update schedule values if needed
				if schedule.monthly_repayment_amount != self.monthly_repayment_amount:
					schedule.monthly_repayment_amount = self.monthly_repayment_amount
					schedule.save()
					print(f"DEBUG Loan.calculate_totals: Updated schedule monthly_repayment_amount to {self.monthly_repayment_amount}")

				# Set the database values
				self.db_set("total_interest_payable", self.total_interest_payable)
				self.db_set("monthly_repayment_amount", self.monthly_repayment_amount)
				self.db_set("total_payment", self.total_payment)
				print(f"DEBUG Loan.calculate_totals: Set DB values - total_payment={self.total_payment}, total_interest_payable={self.total_interest_payable}, monthly_repayment_amount={self.monthly_repayment_amount}")
		else:
			# Use original calculation for other methods
			super().calculate_totals(on_insert)

	def make_draft_schedule(self):
		print(f"DEBUG Loan.make_draft_schedule: Creating schedule with monthly_repayment_amount={self.monthly_repayment_amount}, interest_calc={self.interest_calculation_method}")
		schedule = frappe.get_doc(
			{
				"doctype": "Loan Repayment Schedule",
				"loan": self.name,
				"repayment_method": self.repayment_method,
				"repayment_start_date": self.repayment_start_date,
				"repayment_periods": self.repayment_periods,
				"loan_amount": self.loan_amount,
				"monthly_repayment_amount": self.monthly_repayment_amount,
				"loan_product": self.loan_product,
				"rate_of_interest": self.rate_of_interest,
				"posting_date": self.posting_date,
			}
		)
		schedule.insert()
		print(f"DEBUG Loan.make_draft_schedule: Schedule created with monthly_repayment_amount={schedule.monthly_repayment_amount}")