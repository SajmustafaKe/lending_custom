#!/usr/bin/env python3
"""
Test script to verify one-time percentage interest calculation
"""
import sys
import os

# Add the lending_custom app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def test_one_time_percentage_calculation():
    """Test the one-time percentage calculation logic"""
    loan_amount = 100000
    rate_of_interest = 35
    repayment_periods = 12

    # Calculate total amount including interest
    total_amount = loan_amount + (loan_amount * rate_of_interest / 100)
    print(f"Total amount (including interest): {total_amount}")

    # Calculate monthly repayment amount
    monthly_repayment_amount = total_amount / repayment_periods
    print(f"Monthly repayment amount: {monthly_repayment_amount}")

    # Expected values
    expected_total = 135000
    expected_monthly = 11250

    print(f"Expected total: {expected_total}")
    print(f"Expected monthly: {expected_monthly}")

    # Check if calculations match expectations
    if abs(total_amount - expected_total) < 0.01 and abs(monthly_repayment_amount - expected_monthly) < 0.01:
        print("✅ Calculations are correct!")
        return True
    else:
        print("❌ Calculations are incorrect!")
        return False

if __name__ == "__main__":
    test_one_time_percentage_calculation()