from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from employees.models import Employee
from payroll.models import Payslip, Payroll, PayslipAllowance, PayslipDeduction
from datetime import datetime, timedelta
from decimal import Decimal
import json


@login_required
def reports_dashboard(request):
    """Reports dashboard with charts and visualizations - only HR and Admin can access"""
    user = request.user
    
    # Check if user is HR or Admin
    if not (user.is_hr() or user.is_admin()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get date range (last 12 months by default)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # 1. Payroll Trends Over Time (Monthly)
    payrolls = Payroll.objects.filter(
        processed_date__gte=start_date
    ).order_by('year', 'month')
    
    monthly_payroll_data = []
    monthly_labels = []
    for payroll in payrolls:
        month_name = datetime(payroll.year, payroll.month, 1).strftime('%b %Y')
        monthly_labels.append(month_name)
        monthly_payroll_data.append({
            'gross_salary': float(payroll.total_gross_salary),
            'deductions': float(payroll.total_deductions),
            'net_salary': float(payroll.total_net_salary),
            'employee_count': payroll.employee_count,
        })
    
    # 2. Department-wise Employee Distribution
    dept_data = Employee.objects.values('job_role__department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    dept_labels = [item['job_role__department'] or 'No Department' for item in dept_data]
    dept_counts = [item['count'] for item in dept_data]
    
    # 3. Salary Distribution by Department
    salary_by_dept = Employee.objects.values('job_role__department').annotate(
        avg_salary=Avg('salary_base'),
        total_employees=Count('id')
    ).order_by('-avg_salary')
    
    salary_dept_labels = [item['job_role__department'] or 'No Department' for item in salary_by_dept]
    salary_dept_avg = [float(item['avg_salary']) for item in salary_by_dept]
    
    # 4. Top Allowance Types (from recent payslips)
    recent_payslips = Payslip.objects.filter(
        payroll__processed_date__gte=start_date
    ).select_related('payroll')
    
    allowance_totals = PayslipAllowance.objects.filter(
        payslip__in=recent_payslips
    ).values('allowance_type__name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:10]
    
    allowance_labels = [item['allowance_type__name'] for item in allowance_totals]
    allowance_amounts = [float(item['total_amount']) for item in allowance_totals]
    
    # 5. Top Deduction Types (from recent payslips)
    deduction_totals = PayslipDeduction.objects.filter(
        payslip__in=recent_payslips
    ).values('deduction_type__name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:10]
    
    deduction_labels = [item['deduction_type__name'] for item in deduction_totals]
    deduction_amounts = [float(item['total_amount']) for item in deduction_totals]
    
    # 6. Job Role Distribution
    job_role_data = Employee.objects.values('job_role__title').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    job_role_labels = [item['job_role__title'] or 'No Role' for item in job_role_data]
    job_role_counts = [item['count'] for item in job_role_data]
    
    # 7. Overall Statistics
    total_employees = Employee.objects.count()
    total_payrolls = Payroll.objects.count()
    total_payslips = Payslip.objects.count()
    
    # Calculate total payroll amounts
    total_gross = Payroll.objects.aggregate(Sum('total_gross_salary'))['total_gross_salary__sum'] or Decimal('0.00')
    total_deductions = Payroll.objects.aggregate(Sum('total_deductions'))['total_deductions__sum'] or Decimal('0.00')
    total_net = Payroll.objects.aggregate(Sum('total_net_salary'))['total_net_salary__sum'] or Decimal('0.00')
    
    # Average salary
    avg_salary = Employee.objects.aggregate(Avg('salary_base'))['salary_base__avg'] or Decimal('0.00')
    
    # 8. Recent Payroll Activity (Last 6 months)
    recent_months = []
    recent_gross = []
    recent_net = []
    
    for i in range(6, 0, -1):
        month_date = end_date - timedelta(days=30 * i)
        month_payrolls = Payroll.objects.filter(
            year=month_date.year,
            month=month_date.month
        )
        if month_payrolls.exists():
            payroll = month_payrolls.first()
            recent_months.append(month_date.strftime('%b %Y'))
            recent_gross.append(float(payroll.total_gross_salary))
            recent_net.append(float(payroll.total_net_salary))
        else:
            recent_months.append(month_date.strftime('%b %Y'))
            recent_gross.append(0)
            recent_net.append(0)
    
    context = {
        'user': user,
        'name': user.first_name or user.username,
        'is_hr_or_admin': True,
        'active_nav': 'reports',
        
        # Statistics
        'total_employees': total_employees,
        'total_payrolls': total_payrolls,
        'total_payslips': total_payslips,
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'total_net': total_net,
        'avg_salary': avg_salary,
        
        # Chart Data (as JSON for JavaScript)
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_payroll_data': json.dumps(monthly_payroll_data),
        
        'dept_labels': json.dumps(dept_labels),
        'dept_counts': json.dumps(dept_counts),
        
        'salary_dept_labels': json.dumps(salary_dept_labels),
        'salary_dept_avg': json.dumps(salary_dept_avg),
        
        'allowance_labels': json.dumps(allowance_labels),
        'allowance_amounts': json.dumps(allowance_amounts),
        
        'deduction_labels': json.dumps(deduction_labels),
        'deduction_amounts': json.dumps(deduction_amounts),
        
        'job_role_labels': json.dumps(job_role_labels),
        'job_role_counts': json.dumps(job_role_counts),
        
        'recent_months': json.dumps(recent_months),
        'recent_gross': json.dumps(recent_gross),
        'recent_net': json.dumps(recent_net),
    }
    
    return render(request, 'reports/dashboard.html', context)
