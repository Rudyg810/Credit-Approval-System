from django.contrib import admin
from django.urls import path
from api.views import RegisterView  # Adjust the import path
from api.views import CreateLoanView  # Adjust the import path
from api.views import CheckEligibilityView  # Adjust the import path
from api.views import ViewLoanDetails
from api.views import ViewLoancustomer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    path('check-elegibility/', CheckEligibilityView.as_view(), name='check-elegibilty'),
    path('create-loan/', CreateLoanView.as_view(), name='loan'),
    path('view-loan/<int:loan_id>/', ViewLoanDetails.as_view(), name='view_loan_details'),
    path('view-loans/<int:customer_id>/', ViewLoancustomer.as_view(), name='view_loan_details'),

    # other URL patterns
]
