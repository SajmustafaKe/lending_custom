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
			
			click.echo("Updating mint app with loan reconciliation filters...")
			execute()
			click.echo("Successfully updated mint app!")
			
		except Exception as e:
			click.echo(f"Error updating mint app: {str(e)}", err=True)
			raise
		finally:
			frappe.destroy()


@click.command('auto-reconcile-loan-repayments')
@click.option('--site', help='Site name')
@click.option('--bank-account', help='Specific bank account to reconcile')
@click.option('--from-date', help='From date (YYYY-MM-DD)')
@click.option('--to-date', help='To date (YYYY-MM-DD)')
@click.option('--limit', default=100, help='Maximum number of transactions to process (default: 100)')
@click.option('--preview', is_flag=True, help='Preview matches without reconciling')
@pass_context
def auto_reconcile_loan_repayments(context, site=None, bank_account=None, from_date=None, to_date=None, limit=100, preview=False):
	"""
	Auto reconcile Loan Repayments with Bank Transactions
	
	Matching criteria:
	- reference_number on Loan Repayment == reference_number on Bank Transaction
	- amount_paid on Loan Repayment == deposit on Bank Transaction
	- posting_date on Loan Repayment == date on Bank Transaction
	
	Examples:
		bench --site county auto-reconcile-loan-repayments
		bench --site county auto-reconcile-loan-repayments --preview
		bench --site county auto-reconcile-loan-repayments --bank-account "ACC-001"
		bench --site county auto-reconcile-loan-repayments --from-date 2024-01-01 --to-date 2024-12-31
		bench --site county auto-reconcile-loan-repayments --limit 500
	"""
	if not site:
		site = get_site(context)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			from lending_custom.loan_auto_reconciliation import (
				auto_reconcile_loan_repayments as reconcile,
				get_loan_repayment_reconciliation_preview
			)
			
			if preview:
				click.echo("\n=== Loan Repayment Reconciliation Preview ===\n")
				matches = get_loan_repayment_reconciliation_preview(
					bank_account=bank_account,
					from_date=from_date,
					to_date=to_date,
					limit=limit
				)
				
				if not matches:
					click.echo("No matching Loan Repayments found for reconciliation.")
					return
				
				click.echo(f"Found {len(matches)} potential match(es):\n")
				for match in matches:
					click.echo(f"Bank Transaction: {match['bank_transaction']}")
					click.echo(f"  Date: {match['bank_transaction_date']}")
					click.echo(f"  Amount: {match['bank_transaction_amount']}")
					click.echo(f"  Reference: {match['bank_transaction_reference']}")
					click.echo(f"  -> Matches Loan Repayment: {match['loan_repayment']}")
					click.echo(f"     Loan: {match['loan']}")
					click.echo(f"     Applicant: {match['applicant']}")
					click.echo("")
				
				click.echo(f"\nRun without --preview to reconcile these transactions.")
			else:
				click.echo("\n=== Auto Reconciling Loan Repayments ===\n")
				result = reconcile(
					bank_account=bank_account,
					from_date=from_date,
					to_date=to_date
				)
				
				click.echo(f"Total Processed: {result['total_processed']}")
				click.echo(f"Reconciled: {result['reconciled']}")
				click.echo(f"Skipped: {result['skipped']}")
				click.echo(f"Failed: {result['failed']}")
				
				if result['reconciled_details']:
					click.echo("\nReconciled Transactions:")
					for item in result['reconciled_details']:
						click.echo(f"  {item['bank_transaction']} -> {item['loan_repayment']} (Amount: {item['amount']})")
				
				if result['failed_details']:
					click.echo("\nFailed Transactions:")
					for item in result['failed_details']:
						click.echo(f"  {item['bank_transaction']}: {item['error']}")
			
			frappe.db.commit()
			
		except Exception as e:
			click.echo(f"Error: {str(e)}", err=True)
			import traceback
			traceback.print_exc()
			raise
		finally:
			frappe.destroy()


@click.command('regenerate-loan-gl-entries')
@click.option('--site', help='Site name')
@click.option('--limit', default=None, type=int, help='Maximum number of repayments to process')
@click.option('--preview', is_flag=True, help='Preview what would be done without making changes')
@pass_context
def regenerate_loan_gl_entries(context, site=None, limit=None, preview=False):
	"""
	Regenerate GL entries for Loan Repayments that are missing them.
	
	This command finds all submitted Loan Repayments that don't have GL entries
	and regenerates them.
	
	Examples:
		bench --site county regenerate-loan-gl-entries --preview
		bench --site county regenerate-loan-gl-entries --limit 50
		bench --site county regenerate-loan-gl-entries
	"""
	if not site:
		site = get_site(context)
	
	with frappe.init_site(site):
		frappe.connect()
		
		try:
			from lending_custom.regenerate_gl_entries import regenerate_missing_gl_entries
			
			regenerate_missing_gl_entries(preview=preview, limit=limit)
			
			if not preview:
				frappe.db.commit()
			
		except Exception as e:
			click.echo(f"Error: {str(e)}", err=True)
			import traceback
			traceback.print_exc()
			raise
		finally:
			frappe.destroy()


commands = [
	update_mint_loan_filters,
	auto_reconcile_loan_repayments,
	regenerate_loan_gl_entries
]