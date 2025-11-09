from django.contrib import admin

from .models import Employee, JobRole, BankDetails


# Register your models here.
@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ("title", "department")
    search_fields =    ("title", "department")

@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ("account_number", "ifsc_code", "bank_name")
    search_fields =    ("account_number", "bank_name")

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("user", "job_role", "bank_details", "date_of_joining", "salary_base")
    search_fields =    ("user__username", "user__first_name", "job_role__title", "bank_details__bank_name")
