from django.shortcuts import render, redirect
from .forms import RegisterForm
from datetime import datetime
import utils


db_handle, client = utils.get_db_handle_local('megafilmdb')


# Create your views here.

def register(response):
    clients = db_handle['clients']
    form = RegisterForm()
    if response.method == 'POST':
        form = RegisterForm(response.POST)
        phone_number = response.POST.get('phone')
        username = response.POST.get('username')
        if existing_user := clients.find_one({'phone': phone_number}):
            return render(response, 'main/info.html', {'info':'Numer jest już przypisany do użytkownika.'})
        if existing_user := clients.find_one({'_id': username}):
            return render(response, 'main/info.html', {'info':'Ta nazwa jest już zajęta.'})
        if form.is_valid():                        
            add_user_query = dict()
            add_user_query['_id'] = username
            add_user_query['username'] = username
            add_user_query['name'] = response.POST.get('name')
            add_user_query['surname'] = response.POST.get('surname')
            add_user_query['address'] = response.POST.get('address')
            add_user_query['phone'] = phone_number
            add_user_query['moviesRented'] = 0
            add_user_query['addDate'] = datetime.now()
            clients.insert_one(add_user_query)
            form.save()        
            return render(response, 'main/index.html', {})
    else:
        form = RegisterForm()
    return render(response, 'register/register.html', {'form':form})