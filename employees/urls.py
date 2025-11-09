from django.urls import path
from employees import views

urlpatterns = [
    path('add/', views.add_employee, name='add_employee'),
]

