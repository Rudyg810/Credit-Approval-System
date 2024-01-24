from rest_framework import status
from rest_framework.response import Response
from datetime import datetime
from rest_framework.views import APIView
from .serializers import CustomerRegistrationSerializer
from .models import Loan, Customer
from .serializers import LoanApprove
from .serializers import LoanEligibilitySerializer
from django.shortcuts import render
from django.db.models import F
from django.db import models
from django.db.models import Sum
from django.db.models import Max
from dateutil.relativedelta import relativedelta
from .serializers import LoanDetailsSerializer

def landing_page(request):
    return render(request, 'landing_page.html')
                  
class RegisterView(APIView):
    def post(self, request, *args, **kwargs):
        
        serializer = CustomerRegistrationSerializer(data=request.data) 
        if serializer.is_valid():
            # Get the last customer ID and calculate the new customer ID
            last_customer_id = Customer.objects.last().customer_id if Customer.objects.last() else 0
            new_customer_id = last_customer_id + 1
            phone_number=serializer.validated_data['phone_number']
            if Customer.objects.filter(phone_number=phone_number).exists():
                return Response(
                    {'success': False, 'message': 'User already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Create a new customer with the provided data
            new_customer = Customer.objects.create(
                customer_id=new_customer_id,
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                age=serializer.validated_data['age'],
                monthly_salary=serializer.validated_data['monthly_salary'],
                phone_number=serializer.validated_data['phone_number'],
                # Calculate approved_limit based on the formula
                approved_limit=36 * serializer.validated_data['monthly_salary'],
                current_debt=0  # Set current_debt to 0
            )

            # Save the customer instance
            new_customer.save()

            # You can customize the response data based on your needs
            response_data = {
                'customer_id': new_customer.customer_id,
                'name': f"{new_customer.first_name} {new_customer.last_name}",
                'age': new_customer.age,
                'monthly_salary': new_customer.monthly_salary,
                'approved_limit': new_customer.approved_limit,
                'phone_number': new_customer.phone_number,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckEligibilityView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoanEligibilitySerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            
            try:
                customer = Customer.objects.get(customer_id=customer_id)
                loans = Loan.objects.filter(customer_id=customer_id)
                num_loans_taken = loans.count()
                tenure = serializer.validated_data.get('tenure', 0)
                num_loans_paid_on_time = loans.filter(emis_paid_on_time__gte=F('tenure')).count()
                num_loans_in_current_year = loans.filter(start_date__year=datetime.now().year).count()
                total_loan = loans.aggregate(total=Sum('loan_amount'))['total'] or 0
                approved_limit = customer.approved_limit
                loan_amount = serializer.validated_data['loan_amount']
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

            credit_score = self.calculate_credit_score(num_loans_taken, num_loans_paid_on_time, num_loans_in_current_year, total_loan, approved_limit)

            approved, interest_rate = self.check_loan_eligibility(credit_score, serializer.validated_data)
            # Convert installment
            emi = (loan_amount + (loan_amount*interest_rate/100 ) )/ (12* tenure)
            monthly_installment = round(emi,2)
            response_data = {
                'customer_id': customer_id,
                'approved': approved,
                'credit_score': max(credit_score, 0),
                'interest_rate': interest_rate,
                'tenure': serializer.validated_data.get('tenure', 0),
                'monthly_installment': monthly_installment
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def calculate_credit_score(self, num_loans_taken, num_loans_paid_on_time, num_loans_in_current_year, total_loan, approved_limit):
        # Initialize credit score
        credit_score = 70 if num_loans_taken == 0 else 0

        # Calculate credit score based on various factors
        if num_loans_taken > 0:
            credit_score += num_loans_taken * -3
            credit_score += num_loans_paid_on_time * 20
            credit_score -= (num_loans_taken - num_loans_paid_on_time) * 10

        if num_loans_in_current_year == 0:
            credit_score += 15

        credit_score += float(total_loan) * 0.01

        # Review this logic based on business requirements
        if total_loan > approved_limit:
            credit_score = 0
        if credit_score > 100:
            credit_score = 100

        return credit_score

    def check_loan_eligibility(self, credit_score, loan_data):
        # Implement your loan eligibility logic based on credit score
        # Example: Adjust interest rate based on credit score
        if credit_score > 50:
            return True, loan_data['interest_rate']
        elif 30 < credit_score <= 50:
            return True, max(loan_data['interest_rate'], 12.0)
        elif 10 < credit_score <= 30:
            return True, max(loan_data['interest_rate'], 16.0)
        else:
            return False, 0.0  # Not approved
       


class CreateLoanView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoanEligibilitySerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']

            try:
                customer = Customer.objects.get(customer_id=customer_id)
                loans = Loan.objects.filter(customer_id=customer_id)
                num_loans_taken = loans.count()
                tenure = serializer.validated_data.get('tenure', 0)
                num_loans_paid_on_time = loans.filter(emis_paid_on_time__gte=F('tenure')).count()
                num_loans_in_current_year = loans.filter(start_date__year=datetime.now().year).count()                
                total_loan = loans.aggregate(total=Sum('loan_amount'))['total'] or 0
                approved_limit = customer.approved_limit
                loan_amount = serializer.validated_data['loan_amount']
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

            credit_score = self.calculate_credit_score(num_loans_taken, num_loans_paid_on_time, num_loans_in_current_year, total_loan, approved_limit)
            last_loan_id = Loan.objects.aggregate(max_id=Max('loan_id'))['max_id'] or 0
            new_loan_id = last_loan_id + 1
            approved, interest_rate = self.check_loan_eligibility(credit_score, serializer.validated_data)
            emi = (loan_amount + (loan_amount * interest_rate / 100)) / (12 * tenure)
            monthly_installment = round(emi, 2)
            # Additional Step: Create a Loan object
            if approved:
                Loan.objects.create(
                    loan_id=new_loan_id,
                    customer_id=customer_id,
                    loan_amount=loan_amount,
                    interest_rate=interest_rate,
                    tenure=tenure,
                    monthly_repayment=monthly_installment,
                    start_date=datetime.now().date(),
                    end_date=datetime.now().date() + relativedelta(years=serializer.validated_data.get('tenure')),
                    emis_paid_on_time=0
                )

            # Convert installment

            response_data = {
                'loan_id': new_loan_id,
                'customer_id': customer_id,
                'loan_approved': approved,
                'credit_score': max(credit_score, 0),
                'monthly_installment': monthly_installment
            }

            return Response(response_data, status=status.HTTP_200_OK)
        return Response({'error': 'Cannot Proceed', '0': max(credit_score, 0)}, status=status.HTTP_400_BAD_REQUEST)
    def calculate_credit_score(self, num_loans_taken, num_loans_paid_on_time, num_loans_in_current_year, total_loan, approved_limit):
        # Initialize credit score
        credit_score = 70 if num_loans_taken == 0 else 0

        # Calculate credit score based on various factors
        if num_loans_taken > 0:
            credit_score += num_loans_taken * -3
            credit_score += num_loans_paid_on_time * 20
            credit_score -= (num_loans_taken - num_loans_paid_on_time) * 10

        if num_loans_in_current_year == 0:
            credit_score += 15

        credit_score += float(total_loan) * 0.01

        # Review this logic based on business requirements
        if total_loan > approved_limit:
            credit_score = 0
        if credit_score > 100:
            credit_score = 100

        return credit_score

    def check_loan_eligibility(self, credit_score, loan_data):
        # Implement your loan eligibility logic based on credit score
        # Example: Adjust interest rate based on credit score
        if credit_score > 50:
            return True, loan_data['interest_rate']
        elif 30 < credit_score <= 50:
            return True, max(loan_data['interest_rate'], 12.0)
        elif 10 < credit_score <= 30:
            return True, max(loan_data['interest_rate'], 16.0)
        else:
            return False, 0.0  # Not approved



class ViewLoanDetails(APIView):
    def get(self, request, loan_id, *args, **kwargs):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve customer_id from the fetched Loan object
        customer_id = loan.customer_id

        # Fetch Customer object using the retrieved customer_id
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize Loan and Customer data separately
       

        # Combine both serialized data
        response_data = {
            'loan_id': loan.loan_id,
            'customer': {
                'customer_id':customer.customer_id,
                'fisrt_name':customer.first_name,
                'last_name':customer.last_name,
                'Phone_number':customer.phone_number,
                'Age':customer.age
            },
            'loan_amount': loan.loan_amount,
            'interest_rate':loan.interest_rate,
            'monthly_iunstallment':loan.monthly_repayment,
            'tenure':loan.tenure
        }

        return Response(response_data, status=status.HTTP_200_OK)



class ViewLoancustomer(APIView):
    def get(self, request, customer_id, *args, **kwargs):
        try:
            loan = Loan.objects.get(customer_id=customer_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve customer_id from the fetched Loan object
        customer_id = loan.customer_id

        # Fetch Customer object using the retrieved customer_id
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize Loan and Customer data separately
       

        # Combine both serialized data
        response_data = {
            'loan_id': loan.loan_id,
            'loan_amount': loan.loan_amount,
            'interest_rate':loan.interest_rate,
            'monthly_iunstallment':loan.monthly_repayment,
            'repayment_left':loan.emis_paid_on_time
        }

        return Response(response_data, status=status.HTTP_200_OK)