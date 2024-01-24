
from rest_framework import serializers
from .models import Loan, Customer
class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    age = serializers.IntegerField()
    monthly_salary = serializers.IntegerField()
    phone_number = serializers.IntegerField()

class LoanEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    
class LoanApprove(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']

class LoanDetailsSerializer(serializers.ModelSerializer):


    class Meta:
        model = Loan
        fields = ['id', 'customer id', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure']