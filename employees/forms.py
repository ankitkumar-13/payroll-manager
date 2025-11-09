from django import forms
from users.models import CustomUser, Role
from employees.models import Employee, JobRole, BankDetails


class AddEmployeeForm(forms.Form):
    # User fields
    username = forms.CharField(max_length=11, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Username'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Email'
    }))
    first_name = forms.CharField(max_length=25, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=25, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Last Name'
    }))
    phone_number = forms.CharField(max_length=11, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Phone Number'
    }))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Password'
    }))
    
    # Employee fields
    job_role = forms.ModelChoiceField(
        queryset=JobRole.objects.all(),
        required=True,
        empty_label="Select a job role",
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full bg-slate-800 text-white'
        })
    )
    date_of_joining = forms.DateField(required=True, widget=forms.DateInput(attrs={
        'class': 'input input-bordered w-full',
        'type': 'date'
    }))
    salary_base = forms.DecimalField(max_digits=12, decimal_places=2, required=True, widget=forms.NumberInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Base Salary',
        'step': '0.01'
    }))
    
    # Bank details
    bank_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Bank Name'
    }))
    account_number = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'Account Number'
    }))
    ifsc_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full',
        'placeholder': 'IFSC Code'
    }))
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email
    
    def save(self):
        # Create user
        user = CustomUser.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data.get('last_name', ''),
            phone_number=self.cleaned_data.get('phone_number', ''),
            role=Role.EMPLOYEE
        )
        
        # Create bank details
        bank_details = BankDetails.objects.create(
            bank_name=self.cleaned_data['bank_name'],
            account_number=self.cleaned_data['account_number'],
            ifsc_code=self.cleaned_data.get('ifsc_code', '')
        )
        
        # Create employee
        employee = Employee.objects.create(
            user=user,
            job_role=self.cleaned_data['job_role'],
            bank_details=bank_details,
            date_of_joining=self.cleaned_data['date_of_joining'],
            salary_base=self.cleaned_data['salary_base']
        )
        
        return employee


class UpdateProfileForm(forms.Form):
    """Form for employees to update their profile"""
    first_name = forms.CharField(max_length=25, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=25, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'Email'
    }))
    phone_number = forms.CharField(max_length=11, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'Phone Number'
    }))
    
    # Bank details
    bank_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'Bank Name'
    }))
    account_number = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'Account Number'
    }))
    ifsc_code = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'input input-bordered w-full bg-slate-800 text-white',
        'placeholder': 'IFSC Code'
    }))
    
    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        if employee:
            # Pre-fill form with existing data
            self.fields['first_name'].initial = employee.user.first_name
            self.fields['last_name'].initial = employee.user.last_name
            self.fields['email'].initial = employee.user.email
            self.fields['phone_number'].initial = employee.user.phone_number
            self.fields['bank_name'].initial = employee.bank_details.bank_name
            self.fields['account_number'].initial = employee.bank_details.account_number
            self.fields['ifsc_code'].initial = employee.bank_details.ifsc_code
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Allow the employee's current email
        return email