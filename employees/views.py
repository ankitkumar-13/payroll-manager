from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from employees.forms import AddEmployeeForm, UpdateProfileForm
from employees.models import Employee, JobRole, BankDetails
from payroll.models import Payslip


@login_required
def list_employees(request):
    """List all employees - only HR and Admin can access"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get all employees with related data
    employees = Employee.objects.select_related('user', 'job_role', 'bank_details').order_by('-date_of_joining')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'employees': employees,
        'is_hr_or_admin': True,
    }
    
    return render(request, 'list_employees.html', context)


@login_required
def add_employee(request):
    """Add a new employee - only HR and Admin can access"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            try:
                employee = form.save()
                employee_name = employee.user.get_full_name() or employee.user.username
                messages.success(request, f'Employee {employee_name} has been added successfully!')
                return redirect('list_employees')
            except Exception as e:
                messages.error(request, f'Error adding employee: {str(e)}')
    else:
        form = AddEmployeeForm()
    
    # Check if job roles exist
    job_roles_count = JobRole.objects.count()
    if job_roles_count == 0:
        messages.warning(request, 'No job roles found. Please create job roles in the admin panel before adding employees.')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'form': form,
        'is_hr_or_admin': True,
    }
    
    return render(request, 'add_employee.html', context)


@login_required
def view_my_payslips(request):
    """View all payslips for the logged-in employee"""
    user = request.user
    
    # Check if user is an employee
    if user.is_hr() or user.is_admin():
        messages.error(request, 'This page is only for employees.')
        return redirect('dashboard')
    
    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    # Get all payslips for this employee, ordered by most recent
    payslips = Payslip.objects.filter(employee=employee).select_related(
        'payroll'
    ).prefetch_related(
        'allowances__allowance_type',
        'deductions__deduction_type'
    ).order_by('-payroll__year', '-payroll__month')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'employee': employee,
        'payslips': payslips,
        'is_hr_or_admin': False,
    }
    
    return render(request, 'employees/my_payslips.html', context)


@login_required
def view_payslip_detail(request, payslip_id):
    """View detailed payslip for the logged-in employee"""
    user = request.user
    
    # Check if user is an employee
    if user.is_hr() or user.is_admin():
        messages.error(request, 'This page is only for employees.')
        return redirect('dashboard')
    
    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    # Get payslip and verify it belongs to this employee
    payslip = get_object_or_404(
        Payslip.objects.select_related('payroll', 'employee__user').prefetch_related(
            'allowances__allowance_type',
            'deductions__deduction_type'
        ),
        id=payslip_id,
        employee=employee
    )
    
    # Get allowances and deductions
    allowances = payslip.allowances.all().select_related('allowance_type')
    deductions = payslip.deductions.all().select_related('deduction_type')
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'employee': employee,
        'payslip': payslip,
        'allowances': allowances,
        'deductions': deductions,
        'is_hr_or_admin': False,
    }
    
    return render(request, 'employees/payslip_detail.html', context)


@login_required
def update_profile(request):
    """Update employee profile - only for employees"""
    user = request.user
    
    # Check if user is an employee
    if user.is_hr() or user.is_admin():
        messages.error(request, 'This page is only for employees.')
        return redirect('dashboard')
    
    try:
        employee = Employee.objects.select_related('user', 'bank_details', 'job_role').get(user=user)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, employee=employee)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user fields
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.email = form.cleaned_data['email']
                    user.phone_number = form.cleaned_data['phone_number']
                    user.save()
                    
                    # Update bank details
                    bank_details = employee.bank_details
                    bank_details.bank_name = form.cleaned_data['bank_name']
                    bank_details.account_number = form.cleaned_data['account_number']
                    bank_details.ifsc_code = form.cleaned_data['ifsc_code']
                    bank_details.save()
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('update_profile')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
    else:
        form = UpdateProfileForm(employee=employee)
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'employee': employee,
        'form': form,
        'is_hr_or_admin': False,
    }
    
    return render(request, 'employees/update_profile.html', context)
