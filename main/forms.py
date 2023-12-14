from django import forms
from .constants import CONST
import utils

class SearchMovies(forms.Form):
    title = forms.CharField(label='Tytuł', max_length=100, required=False)
    genre = forms.ChoiceField(label='Gatunek', choices=enumerate(CONST.genres), required=False)

class SearchRentals(forms.Form):
    name = forms.CharField(label='Imię', max_length=100, required=False)
    surname = forms.CharField(label='Nazwisko', max_length=100, required=False)    
    phone = forms.CharField(label='Numer tel.', max_length=12, required=False)    
    title = forms.CharField(label='Tytuł filmu', max_length=200, required=False)
    slug = forms.CharField(label='Id filmu', max_length=100, required=False)
    years = list(range(1990, 2050))
    widget = forms.SelectDateWidget(years=years)
    rentDate = forms.DateField(label='Data wypożyczenia', required=False, widget=widget)
    plannedReturnDate = forms.DateField(label='Przewidywana data zwrotu', required=False, widget=widget)
    returnDate = forms.DateField(label='Data zwrotu', required=False, widget=widget)

class SearchClients(forms.Form):
    name = forms.CharField(label='Imię', max_length=100, required=False)
    surname = forms.CharField(label='Nazwisko', max_length=100, required=False)
    address = forms.CharField(label='Adres', max_length=500, required=False)
    phone = forms.CharField(label='Numer tel.', max_length=12, required=False)    
    moviesRented = forms.IntegerField(label='Obecnie wypożyczonych filmów', min_value=0, max_value=3, required=False)



class EditMovie(forms.Form):
    title = forms.CharField(label='Tytuł', max_length=200, required=True)
    genre = forms.ChoiceField(label='Gatunek', choices=enumerate(CONST.genres), required=True)
    text_area = widget=forms.Textarea(attrs={
        'rows': 2,
        'cols':80,
        'style': 'resize:none'
    })
    synopsis = forms.CharField(label='Opis', max_length=2000, required=True,widget=text_area)
    director = forms.CharField(label='Reżyser', max_length=200, required=True)
    cast = forms.CharField(label='Obsada (rodziel przecinkiem)', max_length=2000, required=True)
    rating = forms.FloatField(label='Ocena', max_value=10, min_value=0, required=True)
    duration = forms.IntegerField(label='Czas trwania w minutach', required=True)
    year = forms.IntegerField(label='Rok', min_value=1900, max_value=2050, required=True)

class EditClient(forms.Form):
    name = forms.CharField(label='Imię', max_length=100, required=True)
    surname = forms.CharField(label='Nazwisko', max_length=100, required=True)
    address = forms.CharField(label='Adres', max_length=500, required=True)
    phone = forms.CharField(label='Numer tel.', max_length=12, required=True)        

class ConfirmForm(forms.Form):
    confirm = forms.BooleanField(label='Wykonaj', required=False, initial=False)
    
class RentForm(forms.Form):
    db_handle, db_client = utils.get_db_handle_local('megafilmdb')   
    usernames = [client.get('_id') for client in db_handle['clients'].find()]
    username = forms.ChoiceField(label='Klient', choices=enumerate(usernames), required=True)
