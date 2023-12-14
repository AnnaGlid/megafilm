from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class RegisterForm(UserCreationForm):
    username = forms.CharField(label='Login', max_length=100)
    name = forms.CharField(label='Imię', max_length=100)
    surname = forms.CharField(label='Nazwisko', max_length=100)   
    address = forms.CharField(label='Adres', max_length=500)
    phone = forms.CharField(label='Numer tel.', max_length=12) 
    class Meta:
        model = User
        fields = ['username', 'name','surname','address','phone','password1','password2']