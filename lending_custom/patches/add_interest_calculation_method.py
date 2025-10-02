import frappe
from frappe import _

def execute():
	"""Create custom fields for interest calculation method"""
	
	# Add interest calculation method to Loan Product
	cf = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan Product",
		"fieldname": "interest_calculation_method",
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	})
	try:
		cf.insert(ignore_if_duplicate=True)
	except:
		pass
	# Ensure column exists
	if not frappe.db.has_column('Loan Product', 'interest_calculation_method'):
		frappe.db.sql("ALTER TABLE `tabLoan Product` ADD COLUMN `interest_calculation_method` varchar(140)")
	
	# Add interest calculation method to Loan Application
	cf = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan Application", 
		"fieldname": "interest_calculation_method",
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	})
	try:
		cf.insert(ignore_if_duplicate=True)
	except:
		pass
	if not frappe.db.has_column('Loan Application', 'interest_calculation_method'):
		frappe.db.sql("ALTER TABLE `tabLoan Application` ADD COLUMN `interest_calculation_method` varchar(140)")
	
	# Add interest calculation method to Loan
	cf = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan",
		"fieldname": "interest_calculation_method", 
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	})
	try:
		cf.insert(ignore_if_duplicate=True)
	except:
		pass
	if not frappe.db.has_column('Loan', 'interest_calculation_method'):
		frappe.db.sql("ALTER TABLE `tabLoan` ADD COLUMN `interest_calculation_method` varchar(140)")