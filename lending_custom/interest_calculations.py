import frappe
from frappe import _
from frappe.utils import flt, cint, date_diff, getdate, add_days, get_last_day
import math

# Override the get_monthly_repayment_amount function for one-time percentage calculation
def get_monthly_repayment_amount_custom(loan_amount, rate_of_interest, repayment_periods, interest_calculation_method=None):
	"""
	Calculate monthly repayment amount based on interest calculation method
	This function overrides the original get_monthly_repayment_amount function
	"""
	# Use the passed parameter, or try to get from context if not provided
	if interest_calculation_method is None:
		# Try to get the interest calculation method from the current context
		# This will be set by the overridden LoanApplication class
		import frappe

		# Check if we're in a loan application context
		if hasattr(frappe, 'form_dict') and frappe.form_dict:
			interest_calculation_method = frappe.form_dict.get('interest_calculation_method', 'Monthly Prorated')
		elif hasattr(frappe, 'local') and hasattr(frappe.local, 'form_dict') and frappe.local.form_dict:
			interest_calculation_method = frappe.local.form_dict.get('interest_calculation_method', 'Monthly Prorated')
		else:
			# Default to Monthly Prorated if we can't determine the method
			interest_calculation_method = 'Monthly Prorated'

	if interest_calculation_method == "One-time Percentage":
		# For one-time percentage, calculate total interest upfront
		total_interest = loan_amount * (rate_of_interest / 100)
		total_amount = loan_amount + total_interest

		# Divide total amount equally over repayment periods
		if repayment_periods and repayment_periods > 0:
			return total_amount / repayment_periods  # Remove math.ceil to avoid rounding issues
		else:
			return total_amount
	else:
		# Original monthly prorated calculation
		if rate_of_interest and repayment_periods:
			monthly_interest_rate = flt(rate_of_interest) / (12 * 100)
			if monthly_interest_rate:
				return math.ceil(loan_amount * (
					monthly_interest_rate * (1 + monthly_interest_rate) ** repayment_periods
				) / ((1 + monthly_interest_rate) ** repayment_periods - 1))
			else:
				return math.ceil(loan_amount / repayment_periods)
		else:
			return math.ceil(loan_amount / (repayment_periods or 1))

# Override the calculate_payable_amount method for loan applications
def calculate_payable_amount_custom(doc):
	"""
	Calculate total payable amount based on interest calculation method
	"""
	if doc.interest_calculation_method == "One-time Percentage":
		# For one-time percentage, calculate total interest upfront
		doc.total_payable_interest = doc.loan_amount * (doc.rate_of_interest / 100)
		doc.total_payable_amount = doc.loan_amount + doc.total_payable_interest
	else:
		# Original monthly prorated calculation
		balance_amount = doc.loan_amount
		doc.total_payable_amount = 0
		doc.total_payable_interest = 0

		while balance_amount > 0:
			interest_amount = flt(balance_amount * doc.rate_of_interest / (12 * 100))
			balance_amount = flt(balance_amount + interest_amount - doc.repayment_amount)
			
			if balance_amount < 0:
				interest_amount += balance_amount  # Adjust for overpayment
				balance_amount = 0
			
			doc.total_payable_interest += interest_amount

		doc.total_payable_amount = doc.loan_amount + doc.total_payable_interest

# Custom interest accrual function for one-time percentage method
def get_per_day_interest_custom(principal_amount, rate_of_interest, company, posting_date=None, interest_day_count_convention=None, interest_calculation_method="Monthly Prorated"):
	"""
	Get per day interest based on calculation method
	"""
	if interest_calculation_method == "One-time Percentage":
		# For one-time percentage, no daily interest accrual - interest is calculated upfront
		return 0.0
	else:
		# Original calculation
		if not posting_date:
			posting_date = getdate()

		if not interest_day_count_convention:
			interest_day_count_convention = frappe.get_cached_value(
				"Company", company, "interest_day_count_convention"
			)

		if interest_day_count_convention == "Actual/365" or interest_day_count_convention == "30/365":
			year_divisor = 365
		elif interest_day_count_convention == "30/360" or interest_day_count_convention == "Actual/360":
			year_divisor = 360
		else:
			# Default is Actual/Actual
			from frappe.utils import days_in_year
			year_divisor = days_in_year(getdate(posting_date).year)

		return flt((principal_amount * rate_of_interest) / (year_divisor * 100))