from django import forms
from .models import Users, TestSchedules, Results
from django.core.exceptions import ValidationError

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['username', 'email', 'first_name', 'last_name']
        
class PasswordForm(forms.ModelForm):
    old_password = forms.CharField(required=True, widget=forms.PasswordInput, label="Old Password")
    password = forms.CharField(required=True, widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(required=True, widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Users
        fields = ['password']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if self.user and not self.user.check_password(old_password):
            self.add_error('old_password', "Old password is incorrect.")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password confirmation does not match.")
        
        return cleaned_data

class ResetPasswordForm(forms.ModelForm):
    password = forms.CharField(required=True, widget=forms.PasswordInput)
    confirm_password = forms.CharField(required=True, widget=forms.PasswordInput)

    class Meta:
        model = Users
        fields = ['password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password confirmation does not match.")

class SignUpForm(forms.ModelForm):
    password = forms.CharField(required=True, widget=forms.PasswordInput)
    confirm_password = forms.CharField(required=True, widget=forms.PasswordInput)

    class Meta:
        model = Users
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password confirmation does not match.")
        
        return cleaned_data
    
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = TestSchedules
        fields = ['Name', 'Psychologist', 'Description', 'Date', 'Location', 'Capacity', 'Image']

class ResultForm(forms.ModelForm):
    class Meta:
        model = Results
        fields = ['Summary', 'Recommendation']
        
    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)
        
        self.fields['Summary'].required = False
        self.fields['Recommendation'].required = False