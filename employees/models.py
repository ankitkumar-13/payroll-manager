from django.db import models
from django.conf import settings

# Create your models here.

class JobRole(models.Model):
    title = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.title}"

class BankDetails(models.Model):
    account_number = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee")
    job_role = models.ForeignKey(JobRole, on_delete=models.CASCADE, related_name="employees", null=True, blank=True)
    bank_details = models.ForeignKey(BankDetails, on_delete=models.CASCADE, related_name="employee")
    date_of_joining = models.DateField()
    salary_base = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Employee - {self.user}"