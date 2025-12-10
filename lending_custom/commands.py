"""
Management commands for lending_custom app
"""
import click
import frappe
from frappe.commands import pass_context, get_site


@click.command('update-mint-loan-filters')
@click.option('--site', help='Site name')
@pass_context
def update_mint_loan_filters(context, site=None):
	"""Update mint app with loan reconciliation filters"""
	if not site:
		site = get_site(context)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			from lending_custom.patches.auto_update_mint_loan_reconciliation import execute
			
			click.echo("🔧 Updating mint app with loan reconciliation filters...")
			execute()
			click.echo("✅ Successfully updated mint app!")
			
		except Exception as e:
			click.echo(f"❌ Error updating mint app: {str(e)}", err=True)
			raise
		finally:
			frappe.destroy()


commands = [
	update_mint_loan_filters
]