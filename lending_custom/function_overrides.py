"""
Function overrides for lending module
"""
import frappe
from frappe.utils import flt
from frappe.query_builder.functions import Sum


def get_term_loans_override(date, term_loan=None, loan_product=None):
	"""
	Override for lending.loan_management.doctype.loan_interest_accrual.loan_interest_accrual.get_term_loans
	
	Modified to allow historical processing by removing the loan_schedule.status == "Active" restriction.
	This enables processing of closed/paid loans for historical interest accrual.
	"""
	loan = frappe.qb.DocType("Loan")
	loan_schedule = frappe.qb.DocType("Loan Repayment Schedule")
	loan_repayment_schedule = frappe.qb.DocType("Repayment Schedule")

	query = (
		frappe.qb.from_(loan)
		.inner_join(loan_schedule)
		.on(loan.name == loan_schedule.loan)
		.inner_join(loan_repayment_schedule)
		.on(loan_repayment_schedule.parent == loan_schedule.name)
		.select(
			loan.name,
			loan.total_payment,
			loan.total_amount_paid,
			loan.loan_account,
			loan.interest_income_account,
			loan.is_term_loan,
			loan.disbursement_date,
			loan.applicant_type,
			loan.applicant,
			loan.rate_of_interest,
			loan.total_interest_payable,
			loan.repayment_start_date,
			loan_repayment_schedule.name.as_("payment_entry"),
			loan_repayment_schedule.payment_date,
			loan_repayment_schedule.principal_amount,
			loan_repayment_schedule.interest_amount,
			loan_repayment_schedule.is_accrued,
			loan_repayment_schedule.balance_loan_amount,
		)
		.where(
			(loan.docstatus == 1)
			& (loan.status == "Disbursed")
			& (loan.is_term_loan == 1)
			& (loan_schedule.docstatus == 1)
			# REMOVED: & (loan_schedule.status == "Active")  # This line was preventing historical processing
			& (loan_repayment_schedule.principal_amount > 0)
			& (loan_repayment_schedule.payment_date <= date)
			& (loan_repayment_schedule.is_accrued == 0)
			& (loan_repayment_schedule.docstatus == 1)
		)
	)

	if term_loan:
		query = query.where(loan.name == term_loan)

	if loan_product:
		query = query.where(loan.loan_product == loan_product)

	term_loans = query.run(as_dict=1)

	return term_loans


def apply_lending_overrides(bootinfo=None):
	"""Apply all lending-related overrides"""
	try:
		from lending.loan_management.doctype.loan_interest_accrual import loan_interest_accrual
		
		# Override the core function
		loan_interest_accrual.get_term_loans = get_term_loans_override
		
		frappe.logger().info("✅ Applied lending_custom overrides for get_term_loans successfully")
		
	except Exception as e:
		frappe.log_error(f"Error applying lending overrides: {str(e)}", "Lending Custom Overrides")
		frappe.logger().error(f"❌ Failed to apply lending overrides: {str(e)}")