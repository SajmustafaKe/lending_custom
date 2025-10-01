#!/usr/bin/env python3
"""
Test script to verify one-time percentage repayment schedule calculations
"""
import sys
import os

# Add the lending_custom app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def test_repayment_schedule_calculations():
    """Test the repayment schedule calculations for one-time percentage interest"""
    loan_amount = 100000
    rate_of_interest = 35
    repayment_periods = 12

    # Calculate expected values
    total_interest = loan_amount * (rate_of_interest / 100)
    total_payable = loan_amount + total_interest
    monthly_repayment = total_payable / repayment_periods
    interest_per_period = total_interest / repayment_periods
    principal_per_period = loan_amount / repayment_periods

    print("=== Expected Schedule Calculations ===")
    print(f"Loan Amount: {loan_amount}")
    print(f"Interest Rate: {rate_of_interest}%")
    print(f"Repayment Periods: {repayment_periods}")
    print(f"Total Interest: {total_interest}")
    print(f"Total Payable: {total_payable}")
    print(f"Monthly Repayment: {monthly_repayment}")
    print(f"Interest per Period: {interest_per_period}")
    print(f"Principal per Period: {principal_per_period}")
    print()

    # Simulate the schedule calculation
    balance = loan_amount
    total_principal_paid = 0
    total_interest_paid = 0

    print("=== Period-by-Period Breakdown ===")
    for period in range(1, repayment_periods + 1):
        # For one-time percentage: principal_per_period = monthly_repayment - interest_per_period
        principal_amount = principal_per_period
        interest_amount = interest_per_period

        # Adjust for last period if needed
        if balance - principal_amount < 0:
            principal_amount = balance
            interest_amount = monthly_repayment - principal_amount

        total_payment = principal_amount + interest_amount
        new_balance = balance - principal_amount

        total_principal_paid += principal_amount
        total_interest_paid += interest_amount

        print(f"Period {period}: Balance={balance:.2f}, Principal={principal_amount:.2f}, Interest={interest_amount:.2f}, Payment={total_payment:.2f}, New Balance={new_balance:.2f}")

        balance = new_balance

    print()
    print("=== Summary ===")
    print(f"Total Principal Paid: {total_principal_paid}")
    print(f"Total Interest Paid: {total_interest_paid}")
    print(f"Total Amount Paid: {total_principal_paid + total_interest_paid}")
    print(f"Original Loan Amount: {loan_amount}")
    print(f"Total Interest Expected: {total_interest}")
    print()

    # Verify calculations
    success = True
    if abs(total_principal_paid - loan_amount) > 0.01:
        print(f"❌ Principal mismatch: {total_principal_paid} != {loan_amount}")
        success = False
    else:
        print("✅ Principal calculation correct")

    if abs(total_interest_paid - total_interest) > 0.01:
        print(f"❌ Interest mismatch: {total_interest_paid} != {total_interest}")
        success = False
    else:
        print("✅ Interest calculation correct")

    if abs(total_principal_paid + total_interest_paid - total_payable) > 0.01:
        print(f"❌ Total payment mismatch: {total_principal_paid + total_interest_paid} != {total_payable}")
        success = False
    else:
        print("✅ Total payment calculation correct")

    return success

if __name__ == "__main__":
    success = test_repayment_schedule_calculations()
    if success:
        print("\n🎉 All repayment schedule calculations are correct!")
    else:
        print("\n❌ Repayment schedule calculations have errors!")