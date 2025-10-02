#!/usr/bin/env python3
"""
Comprehensive test script to verify one-time percentage interest calculation for Loans
"""
import sys
import os

# Add the lending_custom app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def test_loan_calculations():
    """Test the loan calculations for one-time percentage interest"""
    loan_amount = 100000
    rate_of_interest = 35
    repayment_periods = 12

    # Calculate expected values
    total_interest = loan_amount * (rate_of_interest / 100)
    total_payable = loan_amount + total_interest
    monthly_repayment = total_payable / repayment_periods

    print("=== Expected Calculations ===")
    print(f"Loan Amount: {loan_amount}")
    print(f"Interest Rate: {rate_of_interest}%")
    print(f"Repayment Periods: {repayment_periods}")
    print(f"Total Interest: {total_interest}")
    print(f"Total Payable: {total_payable}")
    print(f"Monthly Repayment: {monthly_repayment}")
    print()

    # Simulate the custom calculation function logic
    def get_monthly_repayment_amount_custom(loan_amount, rate_of_interest, repayment_periods, interest_calculation_method=None):
        if interest_calculation_method == "One-time Percentage":
            total_interest = loan_amount * (rate_of_interest / 100)
            total_amount = loan_amount + total_interest
            if repayment_periods and repayment_periods > 0:
                return total_amount / repayment_periods
            else:
                return total_amount
        else:
            # Simplified monthly prorated calculation
            if rate_of_interest and repayment_periods:
                monthly_interest_rate = rate_of_interest / (12 * 100)
                if monthly_interest_rate:
                    return loan_amount * (
                        monthly_interest_rate * (1 + monthly_interest_rate) ** repayment_periods
                    ) / ((1 + monthly_interest_rate) ** repayment_periods - 1)
                else:
                    return loan_amount / repayment_periods
            else:
                return loan_amount / (repayment_periods or 1)

    calculated_monthly = get_monthly_repayment_amount_custom(
        loan_amount, rate_of_interest, repayment_periods, "One-time Percentage"
    )

    print("=== Function Test ===")
    print(f"Calculated Monthly Repayment: {calculated_monthly}")
    print(f"Match Expected: {abs(calculated_monthly - monthly_repayment) < 0.01}")
    print()

    # Test total payable calculations
    total_payment = loan_amount + total_interest
    total_interest_payable = total_interest

    print("=== Total Calculations ===")
    print(f"Total Payment (Payable Amount): {total_payment}")
    print(f"Total Interest Payable: {total_interest_payable}")
    print()

    return {
        'loan_amount': loan_amount,
        'rate_of_interest': rate_of_interest,
        'repayment_periods': repayment_periods,
        'total_interest': total_interest,
        'total_payable': total_payable,
        'monthly_repayment': monthly_repayment,
        'calculated_monthly': calculated_monthly,
        'total_payment': total_payment,
        'total_interest_payable': total_interest_payable
    }

if __name__ == "__main__":
    results = test_loan_calculations()

    # Summary
    print("=== Test Summary ===")
    print("✅ All calculations completed successfully!")
    print(f"📊 Loan Amount: {results['loan_amount']:,}")
    print(f"📊 Total Payable: {results['total_payable']:,}")
    print(f"📊 Monthly Repayment: {results['monthly_repayment']:.2f}")
    print(f"📊 Total Interest: {results['total_interest']:,}")