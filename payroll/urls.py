from django.urls import path
from payroll import views

urlpatterns = [
    path('', views.list_payrolls, name='list_payrolls'),
    path('process/', views.process_payroll, name='process_payroll'),
    path('<int:payroll_id>/', views.payroll_detail, name='payroll_detail'),
]

