"""
formulas:
Monthly Interest = Balance Loan Amount  x Monthly rate
Principle = Monthly Repayment - Monthly Interest
Monthly Balance = Balance Loan Amount - Monthly Principle
"""

loan = float(input("Loan Amount (RM): "))
down_payment_rate = float(input("Down Payment(%): ")) / 100
interest_rate = float(input("Interest rate (%): ")) / 100
year = float(input("Year: "))

balance = loan * (1 - down_payment_rate)
monthly_interest_rate = interest_rate / 12
number_of_payment = year * 12

# this formula is from https://en.wikipedia.org/wiki/Amortization_calculator
def monthly_repayment(principal, monthly_interest_rate, number_of_payment):
    return principal * (monthly_interest_rate + (monthly_interest_rate / ((1 + monthly_interest_rate)**number_of_payment - 1)))

m_repayment = monthly_repayment(balance, monthly_interest_rate, number_of_payment)

print("Monthly Repayment (RM): ", format(m_repayment, "0.02f"))

total_interest = 0
total_principle = 0

for i in range(1, int(number_of_payment) + 1):
    monthly_interest = balance * monthly_interest_rate
    total_interest = total_interest + monthly_interest
    principle = m_repayment - monthly_interest
    total_principle += principle
    balance -= principle

    print(str(i).ljust(3), format(principle, "0.02f").ljust(20), format(monthly_interest, "0.02f").ljust(20), format(balance, "0.02f").ljust(20) if i != int(number_of_payment) else "0.00")
    # print(f"{i}, {principle}, {monthly_interest}, {balance}")
else:
    print("total principle:", format(total_principle, "0.02f"))
    print("total interest:", format(total_interest, "0.02f"))