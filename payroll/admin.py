from django.contrib import admin
from .models import (
    AllowanceType, DeductionType, Payroll, Payslip,
    PayslipAllowance, PayslipDeduction,
    EmployeeAllowanceConfig, EmployeeDeductionConfig
)


@admin.register(AllowanceType)
class AllowanceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_taxable', 'is_active')
    list_filter = ('is_taxable', 'is_active')
    search_fields = ('name', 'description')


@admin.register(DeductionType)
class DeductionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_statutory', 'is_active')
    list_filter = ('is_statutory', 'is_active')
    search_fields = ('name', 'description')


class PayslipAllowanceInline(admin.TabularInline):
    model = PayslipAllowance
    extra = 0
    fields = ('allowance_type', 'amount', 'description')


class PayslipDeductionInline(admin.TabularInline):
    model = PayslipDeduction
    extra = 0
    fields = ('deduction_type', 'amount', 'description')


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'payroll', 'base_salary', 'gross_salary', 'total_deductions', 'net_salary', 'payment_date')
    list_filter = ('payroll__year', 'payroll__month', 'payroll__status', 'payment_method')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'employee__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PayslipAllowanceInline, PayslipDeductionInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('payroll', 'employee', 'payment_date', 'payment_method')
        }),
        ('Salary Details', {
            'fields': ('base_salary', 'gross_salary', 'total_deductions', 'net_salary')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('month', 'year', 'status', 'employee_count', 'total_net_salary', 'processed_date')
    list_filter = ('status', 'year', 'month')
    search_fields = ('notes',)
    readonly_fields = ('processed_date', 'total_gross_salary', 'total_deductions', 'total_net_salary')
    date_hierarchy = 'processed_date'
    fieldsets = (
        ('Pay Period', {
            'fields': ('month', 'year', 'status')
        }),
        ('Summary', {
            'fields': ('employee_count', 'total_gross_salary', 'total_deductions', 'total_net_salary')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_date', 'notes')
        }),
    )


@admin.register(EmployeeAllowanceConfig)
class EmployeeAllowanceConfigAdmin(admin.ModelAdmin):
    list_display = ('employee', 'allowance_type', 'get_allowance_type_display', 'amount', 'percentage', 'is_active', 'effective_from', 'effective_to')
    list_filter = ('allowance_type', 'is_active', 'effective_from')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'allowance_type__name')


@admin.register(EmployeeDeductionConfig)
class EmployeeDeductionConfigAdmin(admin.ModelAdmin):
    list_display = ('employee', 'deduction_type', 'get_deduction_type_display', 'amount', 'percentage', 'is_active', 'effective_from', 'effective_to')
    list_filter = ('deduction_type', 'is_active', 'deduction_type__is_statutory')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'deduction_type__name')
