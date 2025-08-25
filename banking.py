import pandas as pd
import random
from faker import Faker

fake = Faker()

num_rows = 100

account_types = ['Savings', 'Current', 'Business', 'Fixed Deposit']
transaction_types = ['Deposit', 'Withdrawal', 'Transfer', 'Bill Payment', 'Loan Payment']
branches = ['Riyadh', 'Jeddah', 'Dammam', 'Makkah', 'Madinah']
loan_statuses = ['Approved', 'Pending', 'Rejected']

data = []

for _ in range(num_rows):
    customer_name = fake.name()
    account_number = fake.random_number(digits=12, fix_len=True)
    account_type = random.choice(account_types)
    branch_location = random.choice(branches)
    transaction_type = random.choice(transaction_types)
    transaction_amount = round(random.uniform(10, 10000), 2)
    transaction_date = fake.date_between(start_date='-1y', end_date='today')
    loan_applications = random.randint(0, 3)
    loan_amount = round(random.uniform(1000, 50000), 2) if loan_applications > 0 else 0
    loan_status = random.choice(loan_statuses) if loan_applications > 0 else None
    credit_score = random.randint(300, 850)
    aggregated_credit_risk_score = round(random.uniform(0, 1), 2)  # 0 low risk, 1 high risk
    account_balance = round(random.uniform(0, 100000), 2)
    email = fake.email()
    phone_number = fake.phone_number()

    data.append([
        customer_name, account_number, account_type, branch_location, transaction_type,
        transaction_amount, transaction_date, loan_applications, loan_amount,
        loan_status, credit_score, aggregated_credit_risk_score, account_balance,
        email, phone_number
    ])

columns = [
    'Customer_Name', 'Account_Number', 'Account_Type', 'Branch_Location', 'Transaction_Type',
    'Transaction_Amount', 'Transaction_Date', 'Loan_Applications', 'Loan_Amount',
    'Loan_Status', 'Credit_Score', 'Aggregated_Credit_Risk_Score', 'Account_Balance',
    'Email', 'Phone_Number'
]

df_banking = pd.DataFrame(data, columns=columns)
df_banking.to_csv("Banking_Sample_Dataset.csv", index=False)
print("Banking_Sample_Dataset.csv created")
