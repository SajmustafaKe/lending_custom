import frappe
from frappe import _

def execute():
	"""Create custom fields for interest calculation method"""
	
	# Add interest calculation method to Loan Product
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan Product",
		"fieldname": "interest_calculation_method",
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	}).insert(ignore_if_duplicate=True)
	
	# Add interest calculation method to Loan Application
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan Application", 
		"fieldname": "interest_calculation_method",
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	}).insert(ignore_if_duplicate=True)
	
	# Add interest calculation method to Loan
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Loan",
		"fieldname": "interest_calculation_method", 
		"fieldtype": "Select",
		"label": "Interest Calculation Method",
		"options": "Monthly Prorated\nOne-time Percentage",
		"default": "Monthly Prorated",
		"insert_after": "rate_of_interest",
		"description": "Monthly Prorated: Interest calculated monthly (rate/12 * principal). One-time Percentage: Interest calculated as percentage of principal amount."
	}).insert(ignore_if_duplicate=True)