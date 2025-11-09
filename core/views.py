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
            context.update({
                'employee': employee,
                'is_hr_or_admin': False,
            })
        except Employee.DoesNotExist:
            context.update({
                'employee': None,
                'is_hr_or_admin': False,
            })
    
    return render(request, 'dashboard.html', context)