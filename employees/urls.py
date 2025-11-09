from django.urls import path
from employees import views

urlpatterns = [
    path('', views.list_employees, name='list_employees'),
    path('add/', views.add_employee, name='add_employee'),
]

