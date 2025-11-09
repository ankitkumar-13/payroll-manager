from django import forms
from .models import Payroll


class ProcessPayrollForm(forms.Form):
    """Form for processing monthly payroll"""
    month = forms.IntegerField(
        min_value=1,
        max_value=12,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Month (1-12)'
        })
    )
    year = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Year (e.g., 2024)'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Optional notes for this payroll'
        })
    )

