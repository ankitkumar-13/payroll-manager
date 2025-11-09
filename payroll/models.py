from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from employees.models import Employee
from decimal import Decimal


class AllowanceType(models.Model):
    """Types of allowances that can be added to payroll (HRA, DA, Bonus, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=True, help_text="Whether this allowance is taxable")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DeductionType(models.Model):
    """Types of deductions that can be applied to payroll (TDS, PF, ESI, Fines, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_statutory = models.BooleanField(default=False, help_text="Whether this is a statutory deduction (TDS, PF, ESI, etc.)")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Payroll(models.Model):
    """Main payroll record for a monthly pay period"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PROCESSED', 'Processed'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
    ]
    
    month = models.IntegerField(help_text="Month (1-12)")
    year = models.IntegerField(help_text="Year (e.g., 2024)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    processed_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payrolls'
    )
    employee_count = models.IntegerField(default=0, help_text="Number of employees processed in this payroll")
    total_gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_net_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['month', 'year']
    
    def __str__(self):
        return f"Payroll - {self.month}/{self.year} ({self.status})"


class Payslip(models.Model):
    """Individual payslip for an employee for a specific pay period"""
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='payslips')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    
    # Basic salary components
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, help_text="Base salary + all allowances")
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, help_text="Gross salary - total deductions")
    
    # Payment details
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, default='BANK_TRANSFER', choices=[
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CHEQUE', 'Cheque'),
        ('CASH', 'Cash'),
    ])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payroll__year', '-payroll__month', 'employee']
        unique_together = ['payroll', 'employee']
    
    def __str__(self):
        return f"Payslip - {self.employee.user.get_full_name()} - {self.payroll.month}/{self.payroll.year}"


class PayslipAllowance(models.Model):
    """Allowances added to a payslip (HRA, DA, Bonus, Overtime, etc.)"""
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='allowances')
    allowance_type = models.ForeignKey(AllowanceType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['allowance_type__name']
    
    def __str__(self):
        return f"{self.allowance_type.name} - ₹{self.amount}"


class PayslipDeduction(models.Model):
    """Deductions applied to a payslip (TDS, PF, ESI, Fines, etc.)"""
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='deductions')
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['deduction_type__name']
    
    def __str__(self):
        return f"{self.deduction_type.name} - ₹{self.amount}"


class EmployeeAllowanceConfig(models.Model):
    """Employee-specific allowance configuration template (e.g., HRA percentage, fixed bonus)"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='allowance_configs')
    allowance_type = models.ForeignKey(AllowanceType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Fixed amount if applicable")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percentage of base salary if applicable")
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['employee', 'allowance_type']
        ordering = ['allowance_type__name']
        verbose_name = "Employee Allowance Configuration"
        verbose_name_plural = "Employee Allowance Configurations"
    
    def is_percentage_type(self):
        """Returns True if this is a percentage-based allowance"""
        return self.percentage is not None and self.percentage > 0
    
    def is_amount_type(self):
        """Returns True if this is a fixed amount-based allowance"""
        return self.amount is not None and self.amount > 0
    
    def get_allowance_type_display(self):
        """Returns 'Percentage' or 'Amount' based on which field is set"""
        if self.is_percentage_type():
            return 'Percentage'
        elif self.is_amount_type():
            return 'Amount'
        return 'Not Set'
    
    def clean(self):
        """Validate that only one of amount or percentage is set"""
        if self.amount and self.percentage:
            raise ValidationError("Cannot set both amount and percentage. Please set only one.")
        if not self.amount and not self.percentage:
            raise ValidationError("Either amount or percentage must be set.")
        if self.amount and self.amount < 0:
            raise ValidationError("Amount cannot be negative.")
        if self.percentage and (self.percentage < 0 or self.percentage > 100):
            raise ValidationError("Percentage must be between 0 and 100.")
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError("Effective from date cannot be after effective to date.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.allowance_type.name}"


class EmployeeDeductionConfig(models.Model):
    """Employee-specific deduction configuration template (e.g., TDS, PF, ESI, Fines, etc.)"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deduction_configs')
    deduction_type = models.ForeignKey(DeductionType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Fixed amount if applicable")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Percentage of base salary if applicable")
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['employee', 'deduction_type']
        ordering = ['deduction_type__name']
        verbose_name = "Employee Deduction Configuration"
        verbose_name_plural = "Employee Deduction Configurations"
    
    def is_percentage_type(self):
        """Returns True if this is a percentage-based deduction"""
        return self.percentage is not None and self.percentage > 0
    
    def is_amount_type(self):
        """Returns True if this is a fixed amount-based deduction"""
        return self.amount is not None and self.amount > 0
    
    def get_deduction_type_display(self):
        """Returns 'Percentage' or 'Amount' based on which field is set"""
        if self.is_percentage_type():
            return 'Percentage'
        elif self.is_amount_type():
            return 'Amount'
        return 'Not Set'
    
    def clean(self):
        """Validate that only one of amount or percentage is set"""
        if self.amount and self.percentage:
            raise ValidationError("Cannot set both amount and percentage. Please set only one.")
        if not self.amount and not self.percentage:
            raise ValidationError("Either amount or percentage must be set.")
        if self.amount and self.amount < 0:
            raise ValidationError("Amount cannot be negative.")
        if self.percentage and (self.percentage < 0 or self.percentage > 100):
            raise ValidationError("Percentage must be between 0 and 100.")
        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError("Effective from date cannot be after effective to date.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.deduction_type.name}"
