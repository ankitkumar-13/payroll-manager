from django.urls import path
from reports import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
]

