from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from employees.models import Employee, JobRole
from users.models import CustomUser


# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return render(request,'index.html', {'user': request.user, 'name' : request.user.first_name})
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'index.html')

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'name': user.first_name or user.username,
    }
    
    # Role-based data
    if user.is_hr() or user.is_admin():
        # HR/Admin Dashboard Stats
        total_employees = Employee.objects.count()
        from users.models import Role
        total_users = CustomUser.objects.filter(role=Role.EMPLOYEE).count()
        total_job_roles = JobRole.objects.count()
        
        # Get recent employees
        recent_employees = Employee.objects.select_related('user', 'job_role').order_by('-date_of_joining')[:5]
        
        context.update({
            'total_employees': total_employees,
            'total_users': total_users,
            'total_job_roles': total_job_roles,
            'recent_employees': recent_employees,
            'is_hr_or_admin': True,
        })
    else:
        # Employee Dashboard
        try:
            employee = Employee.objects.select_related('job_role', 'bank_details').get(user=user)
            from payroll.models import Payslip
            from django.db.models import Sum
            from datetime import datetime
            
            # Get payslip statistics
            all_payslips = Payslip.objects.filter(employee=employee)
            current_month = datetime.now().month
            current_year = datetime.now().year
            this_month_payslips = all_payslips.filter(
                payroll__month=current_month,
                payroll__year=current_year
            )
            total_earnings = all_payslips.aggregate(Sum('net_salary'))['net_salary__sum'] or 0
            
            context.update({
                'employee': employee,
                'payslips_count': this_month_payslips.count(),
                'total_earnings': total_earnings,
                'total_payslips': all_payslips.count(),
                'is_hr_or_admin': False,
            })
        except Employee.DoesNotExist:
            context.update({
                'employee': None,
                'payslips_count': 0,
                'total_earnings': 0,
                'total_payslips': 0,
                'is_hr_or_admin': False,
            })
    
    return render(request, 'dashboard.html', context)