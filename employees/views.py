from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from employees.forms import AddEmployeeForm
from employees.models import Employee, JobRole


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
