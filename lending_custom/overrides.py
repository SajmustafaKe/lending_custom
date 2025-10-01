import frappe
from frappe import _
from frappe.utils import flt, cint, date_diff, getdate, add_days, get_last_day, add_months
import math

from lending.loan_management.doctype.loan_application.loan_application import LoanApplication
from lending.loan_management.doctype.loan.loan import Loan
from lending.loan_management.doctype.loan_repayment_schedule.loan_repayment_schedule import (
	LoanRepaymentSchedule,
	get_monthly_repayment_amount,
	add_single_month
)
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


class LoanOverride(Loan):
	def validate(self):
		# Set interest calculation method from loan product if not set
		if not self.interest_calculation_method and self.loan_product:
			self.interest_calculation_method = frappe.db.get_value(
				"Loan Product", self.loan_product, "interest_calculation_method"
			) or "Monthly Prorated"
			print(f"DEBUG Loan.validate: Set interest_calculation_method to {self.interest_calculation_method} from loan_product {self.loan_product}")

		print(f"DEBUG Loan.validate: interest_calculation_method={self.interest_calculation_method}, loan_product={self.loan_product}")

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


class LoanRepaymentScheduleOverride(LoanRepaymentSchedule):
	def validate(self):
		print(f"DEBUG LoanRepaymentSchedule.validate: START - loan={self.loan}, loan_product={self.loan_product}")

		# Get interest calculation method
		interest_calc_method = None
		if self.loan_product:
			interest_calc_method = frappe.db.get_value("Loan Product", self.loan_product, "interest_calculation_method")
			print(f"DEBUG LoanRepaymentSchedule.validate: Retrieved interest_calc_method='{interest_calc_method}' from loan_product='{self.loan_product}'")
		else:
			print(f"DEBUG LoanRepaymentSchedule.validate: No loan_product set")

		if interest_calc_method == "One-time Percentage":
			print(f"DEBUG LoanRepaymentSchedule.validate: Using one-time percentage validation flow")
			# Custom validation flow for one-time percentage
			self.validate_repayment_method()
			self.set_missing_fields_one_time()
			self.make_repayment_schedule_one_time()
			self.set_repayment_period()
		else:
			print(f"DEBUG LoanRepaymentSchedule.validate: Using original validation flow for method={interest_calc_method}")
			# Original validation flow
			super().validate()

		print(f"DEBUG LoanRepaymentSchedule.validate: END - monthly_repayment_amount={self.monthly_repayment_amount}, schedule_length={len(self.repayment_schedule) if self.repayment_schedule else 0}")

	def set_missing_fields_one_time(self):
		print(f"DEBUG LoanRepaymentSchedule.set_missing_fields_one_time: START - monthly_repayment_amount={self.monthly_repayment_amount}")

		# Only set monthly_repayment_amount if it's not already set
		if not self.monthly_repayment_amount or self.monthly_repayment_amount == 0:
			if self.repayment_method == "Repay Over Number of Periods":
				# Calculate total amount including interest
				total_amount = self.loan_amount + (self.loan_amount * self.rate_of_interest / 100)
				print(f"DEBUG LoanRepaymentSchedule.set_missing_fields_one_time: total_amount={total_amount}, loan_amount={self.loan_amount}, rate={self.rate_of_interest}")

				# Set monthly repayment amount as total divided by periods
				if self.repayment_periods and self.repayment_periods > 0:
					self.monthly_repayment_amount = total_amount / self.repayment_periods
					print(f"DEBUG LoanRepaymentSchedule.set_missing_fields_one_time: SET monthly_repayment_amount={self.monthly_repayment_amount}")
				else:
					print("DEBUG LoanRepaymentSchedule.set_missing_fields_one_time: no repayment_periods")
		else:
			print(f"DEBUG LoanRepaymentSchedule.set_missing_fields_one_time: monthly_repayment_amount already set to {self.monthly_repayment_amount}")

	def make_repayment_schedule_one_time(self):
		print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule_one_time: START - monthly_repayment_amount={self.monthly_repayment_amount}")

		if not self.repayment_start_date:
			frappe.throw(_("Repayment Start Date is mandatory for term loans"))

		schedule_type_details = frappe.db.get_value(
			"Loan Product", self.loan_product, ["repayment_schedule_type", "repayment_date_on"], as_dict=1
		)

		self.repayment_schedule = []
		payment_date = self.repayment_start_date
		balance_amount = self.loan_amount

		# For one-time percentage, calculate fixed amounts
		total_interest = self.loan_amount * (self.rate_of_interest / 100)
		interest_per_period = total_interest / self.repayment_periods
		principal_per_period = self.monthly_repayment_amount - interest_per_period

		print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule_one_time: total_interest={total_interest}, interest_per_period={interest_per_period}, principal_per_period={principal_per_period}, monthly_repayment_amount={self.monthly_repayment_amount}")

		for period in range(self.repayment_periods):
			# Calculate remaining balance after this payment
			new_balance = balance_amount - principal_per_period

			# For the last period, ensure balance goes to zero
			if period == self.repayment_periods - 1:
				principal_per_period = balance_amount
				new_balance = 0.0

			total_payment = principal_per_period + interest_per_period

			# Calculate days (simplified for one-time percentage)
			days = 30

			print(f"DEBUG Period {period+1}: balance_before={balance_amount}, principal={principal_per_period}, interest={interest_per_period}, total={total_payment}, balance_after={new_balance}")

			self.add_repayment_schedule_row(
				payment_date, principal_per_period, interest_per_period, total_payment, new_balance, days
			)

			# Update balance for next period
			balance_amount = new_balance

			# Calculate next payment date
			if schedule_type_details.repayment_schedule_type == "Pro-rated calendar months":
				next_payment_date = get_last_day(payment_date)
				if schedule_type_details.repayment_date_on == "Start of the next month":
					next_payment_date = add_days(next_payment_date, 1)
				payment_date = next_payment_date
			else:
				payment_date = add_single_month(payment_date)

		print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule_one_time: Generated {len(self.repayment_schedule)} periods")
		# Print first few rows for debugging
		for i, row in enumerate(self.repayment_schedule[:3]):
			print(f"DEBUG Row {i+1}: date={row.payment_date}, principal={row.principal_amount}, interest={row.interest_amount}, total={row.total_payment}, balance={row.balance_loan_amount}")

	def get_amounts(
		self,
		payment_date,
		balance_amount,
		schedule_type,
		repayment_date_on,
		additional_days,
		carry_forward_interest=0,
	):
		# Get interest calculation method from loan product
		interest_calc_method = None
		if self.loan_product:
			interest_calc_method = frappe.db.get_value("Loan Product", self.loan_product, "interest_calculation_method")

		print(f"DEBUG LoanRepaymentSchedule.get_amounts: START - method={interest_calc_method}, balance_amount={balance_amount}, monthly_repayment_amount={self.monthly_repayment_amount}, loan_product={self.loan_product}")

		if interest_calc_method == "One-time Percentage":
			print(f"DEBUG LoanRepaymentSchedule.get_amounts: Using one-time percentage calculation, balance_amount={balance_amount}")
			# For one-time percentage, calculate total interest upfront
			total_interest = self.loan_amount * (self.rate_of_interest / 100)

			# Each period's interest portion is total_interest / periods (fixed amount)
			interest_per_period = total_interest / self.repayment_periods

			# Principal portion is monthly_repayment_amount - interest_per_period
			principal_per_period = self.monthly_repayment_amount - interest_per_period

			# Calculate remaining balance after this payment
			new_balance = balance_amount - principal_per_period

			# Ensure balance doesn't go negative on the last payment
			if new_balance < 0:
				principal_per_period += new_balance
				new_balance = 0.0

			total_payment = principal_per_period + interest_per_period

			# For one-time percentage, days calculation is not relevant for interest
			days = 30  # Default value

			print(f"DEBUG LoanRepaymentSchedule.get_amounts: monthly_repayment_amount={self.monthly_repayment_amount}, interest_per_period={interest_per_period}, principal_per_period={principal_per_period}, new_balance={new_balance}, total_payment={total_payment}")

			return interest_per_period, principal_per_period, new_balance, total_payment, days
		else:
			print(f"DEBUG LoanRepaymentSchedule.get_amounts: Using original calculation, method={interest_calc_method}")
			# Use original calculation for other methods
			return super().get_amounts(
				payment_date, balance_amount, schedule_type, repayment_date_on, additional_days, carry_forward_interest
			)

	def make_repayment_schedule(self):
		# Get interest calculation method
		interest_calc_method = None
		if self.loan_product:
			interest_calc_method = frappe.db.get_value("Loan Product", self.loan_product, "interest_calculation_method")
			print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: Retrieved interest_calc_method='{interest_calc_method}' from loan_product='{self.loan_product}'")
		else:
			print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: No loan_product set")

		print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: START - method={interest_calc_method}, monthly_repayment_amount={self.monthly_repayment_amount}")

		if interest_calc_method == "One-time Percentage":
			print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: Using one-time percentage schedule generation")
			# Use custom schedule generation for one-time percentage
			if not self.repayment_start_date:
				frappe.throw(_("Repayment Start Date is mandatory for term loans"))

			schedule_type_details = frappe.db.get_value(
				"Loan Product", self.loan_product, ["repayment_schedule_type", "repayment_date_on"], as_dict=1
			)

			self.repayment_schedule = []
			payment_date = self.repayment_start_date
			balance_amount = self.loan_amount
			broken_period_interest_days = date_diff(add_months(payment_date, -1), self.posting_date)
			carry_forward_interest = self.adjusted_interest

			period_count = 0
			while balance_amount > 0 and period_count < self.repayment_periods:
				interest_amount, principal_amount, balance_amount, total_payment, days = self.get_amounts(
					payment_date,
					balance_amount,
					schedule_type_details.repayment_schedule_type,
					schedule_type_details.repayment_date_on,
					broken_period_interest_days,
					carry_forward_interest,
				)

				if schedule_type_details.repayment_schedule_type == "Pro-rated calendar months":
					next_payment_date = get_last_day(payment_date)
					if schedule_type_details.repayment_date_on == "Start of the next month":
						next_payment_date = add_days(next_payment_date, 1)
					payment_date = next_payment_date
				else:
					# For other schedule types, use the original date calculation
					next_payment_date = add_single_month(payment_date)
					payment_date = next_payment_date

				self.add_repayment_schedule_row(
					payment_date, principal_amount, interest_amount, total_payment, balance_amount, days
				)

				period_count += 1
				broken_period_interest_days = 0
				carry_forward_interest = 0

			# For one-time percentage, ensure we have exactly the right number of periods
			if len(self.repayment_schedule) < self.repayment_periods:
				# Add remaining periods if needed
				while len(self.repayment_schedule) < self.repayment_periods:
					last_row = self.repayment_schedule[-1]
					payment_date = add_single_month(payment_date) if schedule_type_details.repayment_schedule_type != "Pro-rated calendar months" else payment_date
					self.add_repayment_schedule_row(
						payment_date, 0, 0, 0, 0, 30
					)

			print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: Generated {len(self.repayment_schedule)} periods")
			# Print first few rows for debugging
			for i, row in enumerate(self.repayment_schedule[:3]):
				print(f"DEBUG Row {i+1}: date={row.payment_date}, principal={row.principal_amount}, interest={row.interest_amount}, total={row.total_payment}, balance={row.balance_loan_amount}")
		else:
			print(f"DEBUG LoanRepaymentSchedule.make_repayment_schedule: Using original schedule generation for method={interest_calc_method}")
			# Use original schedule generation for other methods
			super().make_repayment_schedule()