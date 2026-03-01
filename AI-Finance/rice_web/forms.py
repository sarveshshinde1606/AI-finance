from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True, min_value=10, max_value=100, help_text="Enter your age")

    class Meta:
        model = User
        fields = ("username", "email", "age", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.age = self.cleaned_data.get('age')  # store in cleaned_data
        if commit:
            user.save()
        return user


from django import forms
from .models import BudgetPlan

class BudgetForm(forms.ModelForm):
    class Meta:
        model = BudgetPlan
        fields = ['salary', 'rent', 'food', 'transport', 'savings_percent']
        widgets = {
            'salary': forms.NumberInput(attrs={'class':'form-control', 'placeholder':'Enter your monthly salary'}),
            'rent': forms.NumberInput(attrs={'class':'form-control', 'placeholder':'Rent expenses'}),
            'food': forms.NumberInput(attrs={'class':'form-control', 'placeholder':'Food expenses'}),
            'transport': forms.NumberInput(attrs={'class':'form-control', 'placeholder':'Transport expenses'}),
            'savings_percent': forms.NumberInput(attrs={'class':'form-control', 'placeholder':'Savings %'}),
        }
