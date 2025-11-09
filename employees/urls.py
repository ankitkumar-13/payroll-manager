from django.urls import path
from employees import views

urlpatterns = [
    path('', views.list_employees, name='list_employees'),
    path('add/', views.add_employee, name='add_employee'),
    path('my-payslips/', views.view_my_payslips, name='view_my_payslips'),
    path('payslip/<int:payslip_id>/', views.view_payslip_detail, name='view_payslip_detail'),
    path('payslip/<int:payslip_id>/generate/', views.generate_payslip, name='generate_payslip'),
    path('update-profile/', views.update_profile, name='update_profile'),
]

