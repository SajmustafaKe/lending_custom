import frappe
from frappe.utils import add_days, getdate, cint, flt

def execute():
	"""Enable historical interest accrual processing by patching core functions"""
	
	# Patch the loan interest accrual module
	from lending.loan_management.doctype.loan_interest_accrual import loan_interest_accrual
	
	# Store original functions
	original_get_last_accrual_date = loan_interest_accrual.get_last_accrual_date
	original_calculate_accrual = loan_interest_accrual.calculate_accrual_amount_for_demand_loans
	
	def patched_get_last_accrual_date(loan, posting_date):
		"""Modified to only consider accruals up to the posting_date for historical processing"""
		last_posting_date = frappe.db.sql(
			""" SELECT MAX(posting_date) from `tabLoan Interest Accrual`
			WHERE loan = %s and docstatus = 1 and posting_date <= %s""",
			(loan, posting_date),
		)

		if last_posting_date[0][0]:
			last_interest_accrual_date = last_posting_date[0][0]
			# interest for last interest accrual date is already booked, so add 1 day
			last_disbursement_date = loan_interest_accrual.get_last_disbursement_date(loan, posting_date)

			if last_disbursement_date and getdate(last_disbursement_date) > add_days(
				getdate(last_interest_accrual_date), 1
			):
				last_interest_accrual_date = last_disbursement_date

			return add_days(last_interest_accrual_date, 1)
		else:
			return frappe.db.get_value("Loan", loan, "disbursement_date")
	
	def patched_calculate_accrual_amount_for_demand_loans(loan, posting_date, process_loan_interest, accrual_type):
		"""Modified to prevent duplicate accruals"""
		from lending.loan_management.doctype.loan_repayment.loan_repayment import (
			calculate_amounts,
			get_pending_principal_amount,
		)
		
		# Check for existing accrual to prevent duplicates
		existing_accrual = frappe.db.exists("Loan Interest Accrual", {
			"loan": loan.name, 
			"posting_date": posting_date, 
			"docstatus": 1
		})
		if existing_accrual:
			frappe.logger().info(f"Accrual already exists for loan {loan.name} on {posting_date}")
			return

		no_of_days = loan_interest_accrual.get_no_of_days_for_interest_accural(loan, posting_date)
		precision = cint(frappe.db.get_default("currency_precision")) or 2

		if no_of_days <= 0:
			frappe.logger().info(f"No days to accrue for loan {loan.name} on {posting_date}")
			return

		pending_principal_amount = get_pending_principal_amount(loan)

		if loan.is_term_loan:
			pending_amounts = calculate_amounts(loan.name, posting_date)
			pending_principal_amount = pending_principal_amount - flt(
				pending_amounts["payable_principal_amount"]
			)
		else:
			pending_amounts = calculate_amounts(loan.name, posting_date, payment_type="Loan Closure")

		payable_interest = loan_interest_accrual.get_interest_amount(
			no_of_days, pending_principal_amount, loan.rate_of_interest, loan.company, posting_date
		)

		args = frappe._dict(
			{
				"loan": loan.name,
				"applicant_type": loan.applicant_type,
				"applicant": loan.applicant,
				"interest_income_account": loan.interest_income_account,
				"loan_account": loan.loan_account,
				"pending_principal_amount": pending_principal_amount,
				"interest_amount": payable_interest,
				"total_pending_interest_amount": pending_amounts["interest_amount"],
				"penalty_amount": pending_amounts["penalty_amount"],
				"process_loan_interest": process_loan_interest,
				"posting_date": posting_date,
				"due_date": posting_date,
				"accrual_type": accrual_type,
			}
		)

		if flt(payable_interest, precision) > 0.0:
			loan_interest_accrual.make_loan_interest_accrual_entry(args)
	
	def patched_get_term_loans(date, term_loan=None, loan_product=None):
		"""Modified to allow historical processing by not requiring active status for old loans"""
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
				& (loan_schedule.docstatus == 1)  # Added missing condition
				# Removed: & (loan_schedule.status == "Active")  # Allow historical processing
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
	
	# Apply patches
	loan_interest_accrual.get_last_accrual_date = patched_get_last_accrual_date
	loan_interest_accrual.calculate_accrual_amount_for_demand_loans = patched_calculate_accrual_amount_for_demand_loans
	loan_interest_accrual.get_term_loans = patched_get_term_loans
	
	frappe.logger().info("Historical interest accrual processing enabled")