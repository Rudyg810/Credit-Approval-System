from django.core.management.base import BaseCommand
import pandas as pd
from api.models import Customer, Loan

class Command(BaseCommand):
    help = 'Import data from Excel sheets'

    def handle(self, *args, **options):
        # Implement your data import logic here
        customer_data = pd.read_excel('C:\\Users\\username\\Downloads\\customer_data.xlsx')
        loan_data = pd.read_excel('C:\\Users\\username\\Downloads\\loan_data.xlsx')

        # Iterate through customer data and create Customer instances
        for _, row in customer_data.iterrows():
            # Perform basic data validation
            if not pd.notna(row['Customer ID']):
                self.stdout.write(self.style.WARNING(f'Skipping invalid data in Customer row: {row}'))
                continue

            # Create Customer instance with computed fields
            try:
                customer = Customer.objects.create(
                    customer_id=row['Customer ID'],
                    first_name=row['First Name'],
                    last_name=row['Last Name'],
                    phone_number=row['Phone Number'],
                    age=row['Age'],
                    monthly_salary=row['Monthly Salary'],
                    approved_limit=row['Approved Limit'],
                    current_debt=0
                    # 'current_debt' is not present in the Excel sheet, so we skip it
                )

                # Calculate and update Full Name
                customer.full_name = f"{row['First Name']} {row['Last Name']}"
                customer.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating Customer instance: {e}'))

        # Iterate through loan data and create Loan instances
        for _, row in loan_data.iterrows():
            # Perform basic data validation
            if not pd.notna(row['Customer ID']):
                self.stdout.write(self.style.WARNING(f'Skipping invalid data in Loan row: {row}'))
                continue

            # Create Loan instance
            try:
                Loan.objects.create(
                    customer_id=row['Customer ID'],
                    loan_amount=row['Loan Amount'],
                    loan_id=row['Loan ID'],
                    tenure=row['Tenure'],
                    interest_rate=row['Interest Rate'],
                    monthly_repayment=row['Monthly payment'],
                    emis_paid_on_time=row['EMIs paid on Time'],
                    end_date=row['End Date'],
                    start_date=row['Date of Approval'],
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating Loan instance: {e}'))

        self.stdout.write(self.style.SUCCESS('Data import completed successfully'))
