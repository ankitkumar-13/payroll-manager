from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import date
from decimal import Decimal

from employees.models import Employee
from .models import (
    Payroll, Payslip, PayslipAllowance, PayslipDeduction,
    EmployeeAllowanceConfig, EmployeeDeductionConfig
)
from .forms import ProcessPayrollForm


@login_required
def list_payrolls(request):
    """List all payrolls - only HR and Admin can access"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get all payrolls ordered by date
    payrolls = Payroll.objects.select_related('processed_by').order_by('-year', '-month')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'payrolls': payrolls,
        'is_hr_or_admin': True,
    }
    
    return render(request, 'payroll/list_payrolls.html', context)


@login_required
def process_payroll(request):
    """Process payroll for a given month/year - only HR and Admin can access"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProcessPayrollForm(request.POST)
        if form.is_valid():
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            notes = form.cleaned_data.get('notes', '')
            
            # Check if payroll already exists
            if Payroll.objects.filter(month=month, year=year).exists():
                messages.error(request, f'Payroll for {month}/{year} already exists.')
                return render(request, 'payroll/process_payroll.html', {
                    'user': user,
                    'name': user.first_name or user.username,
                    'form': form,
                    'is_hr_or_admin': True,
                })
            
            try:
                with transaction.atomic():
                    # Create payroll record
                    payroll = Payroll.objects.create(
                        month=month,
                        year=year,
                        status='PROCESSED',
                        processed_by=user,
                        notes=notes
                    )
                    
                    # Get all active employees
                    employees = Employee.objects.select_related('user', 'job_role').all()
                    
                    total_gross = Decimal('0.00')
                    total_deductions = Decimal('0.00')
                    total_net = Decimal('0.00')
                    employee_count = 0
                    
                    # Process each employee
                    for employee in employees:
                        base_salary = employee.salary_base
                        
                        # Calculate allowances
                        allowance_configs = EmployeeAllowanceConfig.objects.filter(
                            employee=employee,
                            is_active=True
                        ).select_related('allowance_type')
                        
                        # Check date validity for allowances
                        current_date = date(year, month, 1)
                        valid_allowances = []
                        for config in allowance_configs:
                            if config.effective_from and config.effective_from > current_date:
                                continue
                            if config.effective_to and config.effective_to < current_date:
                                continue
                            valid_allowances.append(config)
                        
                        total_allowances = Decimal('0.00')
                        payslip_allowances = []
                        
                        for config in valid_allowances:
                            if config.is_percentage_type():
                                amount = base_salary * (config.percentage / Decimal('100'))
                            else:
                                amount = config.amount
                            
                            total_allowances += amount
                            payslip_allowances.append({
                                'allowance_type': config.allowance_type,
                                'amount': amount,
                                'description': f"{config.allowance_type.name}"
                            })
                        
                        # Calculate deductions
                        deduction_configs = EmployeeDeductionConfig.objects.filter(
                            employee=employee,
                            is_active=True
                        ).select_related('deduction_type')
                        
                        # Check date validity for deductions
                        valid_deductions = []
                        for config in deduction_configs:
                            if config.effective_from and config.effective_from > current_date:
                                continue
                            if config.effective_to and config.effective_to < current_date:
                                continue
                            valid_deductions.append(config)
                        
                        total_deductions_amount = Decimal('0.00')
                        payslip_deductions = []
                        
                        for config in valid_deductions:
                            if config.is_percentage_type():
                                # For deductions, percentage can be of base or gross
                                # Using base salary for now (can be changed to gross if needed)
                                amount = base_salary * (config.percentage / Decimal('100'))
                            else:
                                amount = config.amount
                            
                            total_deductions_amount += amount
                            payslip_deductions.append({
                                'deduction_type': config.deduction_type,
                                'amount': amount,
                                'description': f"{config.deduction_type.name}"
                            })
                        
                        # Calculate totals
                        gross_salary = base_salary + total_allowances
                        net_salary = gross_salary - total_deductions_amount
                        
                        # Create payslip
                        payslip = Payslip.objects.create(
                            payroll=payroll,
                            employee=employee,
                            base_salary=base_salary,
                            gross_salary=gross_salary,
                            total_deductions=total_deductions_amount,
                            net_salary=net_salary
                        )
                        
                        # Create payslip allowances
                        for allowance_data in payslip_allowances:
                            PayslipAllowance.objects.create(
                                payslip=payslip,
                                allowance_type=allowance_data['allowance_type'],
                                amount=allowance_data['amount'],
                                description=allowance_data['description']
                            )
                        
                        # Create payslip deductions
                        for deduction_data in payslip_deductions:
                            PayslipDeduction.objects.create(
                                payslip=payslip,
                                deduction_type=deduction_data['deduction_type'],
                                amount=deduction_data['amount'],
                                description=deduction_data['description']
                            )
                        
                        # Update totals
                        total_gross += gross_salary
                        total_deductions += total_deductions_amount
                        total_net += net_salary
                        employee_count += 1
                    
                    # Update payroll totals
                    payroll.total_gross_salary = total_gross
                    payroll.total_deductions = total_deductions
                    payroll.total_net_salary = total_net
                    payroll.employee_count = employee_count
                    payroll.save()
                    
                    messages.success(
                        request,
                        f'Payroll for {month}/{year} processed successfully! '
                        f'{employee_count} employees processed.'
                    )
                    return redirect('payroll_detail', payroll_id=payroll.id)
                    
            except Exception as e:
                messages.error(request, f'Error processing payroll: {str(e)}')
    else:
        # Pre-fill with current month/year
        today = timezone.now().date()
        form = ProcessPayrollForm(initial={
            'month': today.month,
            'year': today.year
        })
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'form': form,
        'is_hr_or_admin': True,
    }
    
    return render(request, 'payroll/process_payroll.html', context)


@login_required
def payroll_detail(request, payroll_id):
    """View details of a specific payroll"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    payroll = get_object_or_404(
        Payroll.objects.select_related('processed_by'),
        id=payroll_id
    )
    
    payslips = Payslip.objects.filter(payroll=payroll).select_related(
        'employee__user', 'employee__job_role'
    ).order_by('employee__user__first_name', 'employee__user__last_name')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'payroll': payroll,
        'payslips': payslips,
        'is_hr_or_admin': True,
    }
    
    return render(request, 'payroll/payroll_detail.html', context)
