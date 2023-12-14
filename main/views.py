import re
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse
import utils
from .forms import *
from .constants import CONST

db_handle, client = utils.get_db_handle_local('megafilmdb')
RGX_CLEAN_LIST_TO_STR = re.compile(r"\[|\]|\'")

RENTALS_PIPELINE = [
                {
                    "$lookup":{
                        "from":"clients",
                        "localField":"username",
                        "foreignField":"_id",
                        "as":"client"
                    }
                },
                {
                    "$lookup":{
                        "from":"films",
                        "localField":"slug",
                        "foreignField":"slug",
                        "as":"movie"
                    }
                },
                {
                    "$unwind": "$client"
                },
                {
                    "$unwind": "$movie"
                },
                {
                    "$project":{
                        "name": "$client.name",
                        "surname": "$client.surname",
                        "phone": "$client.phone",
                        "slug": "$movie.slug",
                        "title": "$movie.title",
                        "rentDate":1,
                        "plannedReturnDate":1,
                        "returnDate":1,
                        "_id":0
                    }
                }
            ]

def get_search_rentals_pipeline(search_query: list) -> list:
    return RENTALS_PIPELINE + search_query

def __sorting(response, collection, query: dict|list|None = None) -> tuple | None:
    if order_by := response.GET.get('order_by'):
        sort = response.GET.get('sort')
        if not sort or sort == 'desc':
            asc = -1
        else:
            asc = 1
        if isinstance(query, list):
            # db.rentals.aggregate([{"$match": {"$expr": {"$eq":[{"$month":"$rentDate"}, 11] } } }, {"$sort":{"clientSurname":1}}])
            query.append({"$sort":{order_by: asc}})            
            all_items = collection.aggregate(query)            
        else:
            all_items = collection.find(query).sort(order_by, asc)
        new_sort = 'desc' if asc == 1 else 'asc'
        return all_items, new_sort

def __regex_query(search_string: str) -> dict:
    return {'$regex': f'.*{search_string}.*', "$options" :'i'}

def __get_query_date_part(val1, val2) -> dict:
    return {"$match": {"$expr": {"$eq":[val1, val2] } } }

def __get_query_regex(field_name: str, search_str: str) -> dict:
    return {"$match": {field_name: __regex_query(search_str) }}

# Create your views here. 

def index(response):
    return render(response, "main/index.html", {})


#region movies
def movies_search(response):
    col_films = db_handle['films']
    form = SearchMovies()
    if response.method == 'GET':
        search_query = {}
        search_str = ''
        if search_title := response.GET.get('title'):
            search_query['title'] = __regex_query(search_title)
            search_str += f'title={search_title}&'

        if search_genre := response.GET.get('genre'):
            search_genre_str = CONST.genres[int(search_genre)]
            if search_genre_str:
                search_query['genre'] = search_genre_str
                search_str += f'genre={search_genre}&'

        all_movies = col_films.find(search_query)
        sorting = __sorting(response, col_films, search_query)
        if sorting:
            all_movies, new_sort = sorting
            return render(response, 'main/movies.html',
                          {
                "movies":enumerate(all_movies), 
                "sort": new_sort, 
                'form':form,
                'search' : search_str
            })
    return render(response, 'main/movies.html',
        {
            "movies":enumerate(all_movies), 
            'sort':'asc', 
            'form':form,
            'search' : search_str
    })    

def movie(response, slug: str):
    col_films = db_handle['films']
    movie = next(iter(col_films.find({'slug': slug})), None)
    if movie:
        return render(response, 'main/movie.html', {'movie': movie})
    else:
        return render(response, 'main/404.html', {})
    
def movie_edit(response, slug: str):
    if not response.user.is_superuser:
        return redirect(index)
    
    col_films = db_handle['films']
    movie = next(iter(col_films.find({'slug': slug})), None)
    form = EditMovie()
    for field_name in form.fields.keys():
        form.fields[field_name].initial = movie.get(field_name, '')
    form.fields['cast'].initial = re.sub(RGX_CLEAN_LIST_TO_STR, '', str(movie.get('cast','')))    

    form.fields['title'].initial = movie.get('title','')
    return render(response, 'main/movie_edit.html', {
        'form':form, 
        'header': 'Edytuj',
        'desc': movie.get('title'),
        'action': f'/movie-action/edited/{movie.get('slug')}'
        })

def movie_add(response):
    if not response.user.is_superuser:
        return redirect(index)
        
    form = EditMovie()
    return render(response, 'main/movie_edit.html', {
        'form':form, 
        'header': 'Dodaj film',
        'action': '/movie-action/added'
        })    

def movie_edited(response, action: str|None = None, slug: str|None= None):
    if not response.user.is_superuser:
        return redirect(index)
            
    if response.method == 'POST':        
        form = EditMovie(response.POST)
        if form.is_valid():
            col_films = db_handle['films']
            query = {}
            data = form.cleaned_data
            query['slug'] = re.sub(r'\s', '-', f'{data.get("title")}-{data.get("year")}'.strip().lower())
            query['title'] = data.get('title','').strip()
            query['director'] = data.get('director').strip()
            genre_nbr = data.get('genre')
            if genre_nbr.isnumeric():
                genre_nbr = int(genre_nbr)
            else:
                genre_nbr = 0
            query['genre'] = CONST.genres[genre_nbr]
            query['cast'] = [actor.strip() for actor in data.get('cast','').split(',')]
            query['synopsis'] = data.get('synopsis').strip()
            query['rating'] = data.get('rating')
            query['duration'] = data.get('duration')
            query['year'] = data.get('year')

            if action == 'added':
                filter_q = {'slug': query['slug']}
                existing_movie = col_films.find_one(filter_q)
                if existing_movie:
                    return render(response, 'main/info.html', {'info':'Taki film już istnieje', 'return_href': '/movies/'})
                query['isRented'] = False
                query['created'] = datetime.now()
                col_films.insert_one(query)
                info = 'Dodano film'

            else:
                # edited
                filter_q= {'slug': slug}
                col_films.update_one(filter_q, {"$set": query}, upsert=True)
                info = 'Zapisano zmiany'
    return render(response, 'main/info.html', {'info':info, 'return_href': '/movies/'})

def movie_delete(response, slug: str):
    if not response.user.is_superuser:
        return redirect(index)
            
    # check if film in currently rented
    col_films = db_handle['films']
    movie = col_films.find_one({'slug':slug})
    if movie.get('isRented'):
        return render(response, 'main/info.html', {'info': 'Film jest obecnie wypożyczony', 'return_href':'/movies/'})

    form = ConfirmForm()
    return render(response, 'main/confirm.html', {
        'form':form,
        'action_href': f'/movie/{slug}/deleted',
        'return_href': '/movies/',
        'message': 'Na pewno usunąć?'
        })

def movie_deleted(response, slug:str):
    if not response.user.is_superuser:
        return redirect(index)
            
    if response.method == 'POST':
        form = ConfirmForm(response.POST)
        if form.is_valid():
            if form.cleaned_data['confirm']:
                # delete movie
                col_films = db_handle['films']
                col_films.delete_one({'slug': slug})
                return render(response, 'main/info.html', {'info':'Film usunięty','return_href':'/movies/'})
            else:
                return redirect(movies_search)
    return redirect(movies_search)

#endregion

#region rentals
def my_rentals(response):    
    if response.user.is_authenticated and not response.user.is_superuser:
        rentals = db_handle['rentals']
        all_rentals = rentals.find({'username': response.user.username})
        if all_rentals.count():
            all_rentals = all_rentals.sort('rentDate', -1)
        return render(response, 'main/my_rentals.html', {'rentals':enumerate(all_rentals)})
    else:
        return redirect(index)

def rent(response, slug: str):
    # cheks if user is authenticated, if has < 3 films rented at the moment, if the film is available
    if response.user.is_authenticated and not response.user.is_superuser:
        clients = db_handle['clients']
        user = clients.find_one({'_id': response.user.username})
        if not user:
            return render(response, 'main/info.html', {'info': 'Coś poszło nie tak :('})
        if user.get('moviesRented') > 2:
            return render(response, 'main/info.html', {'info': 'Została wypożyczona maksymalna ilość filmów! (3)'})
        
        films = db_handle['films']
        film = films.find_one({'slug': slug})
        if not film:
            return render(response, 'main/info.html', {'info': 'Nie ma takiego filmu'})
        if film.get('isRented'):
            return render(response, 'main/info.html', {'info': 'Film jest już wypożyczony'})
        
        query = {
            'username': user.get('_id'),
            'slug': slug,
            'rentDate': datetime.now(),
            'plannedReturnDate': datetime.now()+timedelta(days=2),
            'returnDate': None
        }
        db_handle['rentals'].insert_one(query)
        films.update_one({'slug':slug}, {'$set':{'isRented':True}})
        clients.update_one({'_id':user.get('_id')}, {'$set':{'moviesRented': user.get('moviesRented') + 1}})
        
    return redirect(my_rentals)

def rentals(response):  
    if not response.user.is_superuser:
        return redirect(index)
            
    name = 'name'
    surname = 'surname'
    movie_slug = 'slug'
    movie_title ='title'
    client_phone = 'phone'

    rent_date = 'rentDate'
    rent_date_d = 'rentDate_day'
    rent_date_m = 'rentDate_month'    
    rent_date_y = 'rentDate_year'

    planned_return_date = 'plannedReturnDate'
    planned_return_date_d = 'plannedReturnDate_day'
    planned_return_date_m = 'plannedReturnDate_month'
    planned_return_date_y = 'plannedReturnDate_year'
    
    return_date = 'returnDate'
    return_date_d = 'returnDate_day'
    return_date_m = 'returnDate_month'
    return_date_y = 'returnDate_year'
   
    col_rentals = db_handle['rentals']
    form = SearchRentals()
    search_query = {}

    # IMPORTANT! aggregation query - list
    '''
        db.rentals.aggregate([
            {"$match": {$expr: {$eq:[{"$month":"$rentDate"}, 11] } } }, 
            {"$match": {"clientName": {"$regex": ".*mariola.*", "$options":"i"  } }}
            ])
    '''        
    if response.method == 'GET':
        search_query = []
        search_str = ''
        for field in [name, surname, movie_title, movie_slug, client_phone]:
            if search_part := response.GET.get(field):
                search_query.append(__get_query_regex(field, search_part))
                search_str += f'{field}={search_part}&'

        fields = [
            ("$dayOfMonth", rent_date_d, rent_date),
            ("$month", rent_date_m, rent_date), 
            ("$year", rent_date_y, rent_date),

            ("$dayOfMonth", planned_return_date_d, planned_return_date),
            ("$month", planned_return_date_m, planned_return_date), 
            ("$year", planned_return_date_y, planned_return_date),

            ("$dayOfMonth", return_date_d, return_date),
            ("$month", return_date_m, return_date), 
            ("$year", return_date_y, return_date)                        
        ]
        for fun, field, what_date in fields:
            if search_part := response.GET.get(field):
                search_query.append(__get_query_date_part({fun: f"${what_date}"}, int(search_part)))
                search_str += f'{field}={search_part}&'  
        
        sorting = __sorting(response, col_rentals, get_search_rentals_pipeline(search_query))
        if sorting:
            all_rentals, new_sort = sorting
            return render(response, 'main/rentals.html',
                          {
                "rentals":enumerate(all_rentals), 
                "sort": new_sort, 
                'form':form,
                'search' : search_str
            })

    all_rentals = col_rentals.aggregate(get_search_rentals_pipeline(search_query))
    return render(response, 'main/rentals.html',
        {
            "rentals": enumerate(all_rentals), 
            'sort':'asc', 
            'form':form,
            'search' : search_str
    })     

def return_movie(response, slug: str):
    if not response.user.is_superuser:
        return redirect(index)
            
    # check if film in currently rented
    col_films = db_handle['films']
    movie = col_films.find_one({'slug':slug})
    if movie.get('isRented'):        
        rental = db_handle['rentals'].find_one({'slug': slug})
        message = f'Zwrócić film wypożyczony przez: {rental.get("username")}?'
        form = ConfirmForm()
        return render(
             response, 'main/confirm.html', {
            'form':form,
            'action_href': f'/returned/{slug}/',
            'return_href': '/rentals/',
            'message': message
            })
    else:
        return render(response, 'main/info.html', {'info': 'Wystąpił błąd'})

def returned_movie(response, slug: str):
    if not response.user.is_superuser:
        return redirect(index)
    
    form = ConfirmForm()
    if response.method == 'POST':
        form = ConfirmForm(response.POST)        
        if form.is_valid():            
            if form.cleaned_data['confirm']:
                # return film
                col_films = db_handle['films']
                col_rentals = db_handle['rentals']
                col_clients = db_handle['clients']

                rental = col_rentals.find_one({'slug':slug, 'returnDate':None})
                col_films.update_one({'slug':slug}, {'$set':{'isRented':False}})
                col_rentals.update_one({'slug':slug, 'returnDate':None}, {'$set':{'returnDate':datetime.now()}})
                col_clients.update_one({'_id': rental.get('username')}, {'$inc':{'moviesRented':-1}})

                return render(response, 'main/info.html', {'info':'Film oddano','return_href':'/rentals/'})
            else:
                return redirect(rentals)
    return redirect(rentals)    

def rent_admin(response, slug:str):
    if not response.user.is_superuser:
        return redirect(index)
    
    if response.method == 'GET':
        form = RentForm()
        return render(response, 'main/rent_admin.html', {
            'form': form,
            'action_href': f'/rent_admin/{slug}',
            'return_href': '/movies/'
            })
    elif response.method == 'POST':
        form = RentForm(response.POST)
        if form.is_valid():
            username = form.cleaned_data['username']            
            username = dict(form.fields['username'].choices)[int(username)]

            clients = db_handle['clients']
            user = clients.find_one({'_id': username})
            if user.get('moviesRented') > 2:
                return render(response, 'main/info.html', {'info': 'Została wypożyczona maksymalna ilość filmów! (3)'})
            
            films = db_handle['films']
            film = films.find_one({'slug': slug})
            if not film:
                return render(response, 'main/info.html', {'info': 'Nie ma takiego filmu'})
            if film.get('isRented'):
                return render(response, 'main/info.html', {'info': 'Film jest już wypożyczony'})
            
            query = {
                'username': user.get('_id'),
                'slug': slug,
                'rentDate': datetime.now(),
                'plannedReturnDate': datetime.now()+timedelta(days=2),
                'returnDate': None
            }
            db_handle['rentals'].insert_one(query)
            films.update_one({'slug':slug}, {'$set':{'isRented':True}})
            clients.update_one({'_id':username}, {'$set':{'moviesRented': user.get('moviesRented') + 1}})            

            return redirect(rentals)
    return redirect(index)
            
             
#endregion


#region clients
def clients_search(response):
    if not response.user.is_superuser:
        return redirect(index)
            
    name = 'name'
    surname = 'surname'
    adress = 'adress'
    phone = 'phone'
    movies_rented = 'moviesRented'

    col_clients = db_handle['clients']
    form = SearchClients()
    if response.method == 'GET':
        search_query = []
        search_str = ''

        for field in [name, surname, adress, phone]:
            if search_part := response.GET.get(field):
                search_query.append(__get_query_regex(field, search_part))
                search_str += f'{field}={search_part}&'  

        if search_part := response.GET.get(movies_rented):
            if search_part.isnumeric():
                search_query.append({'$match':{movies_rented : int(search_part)}})
                search_str += f'{field}={search_part}'

        all_clients = col_clients.aggregate(search_query)
        sorting = __sorting(response, col_clients, search_query)
        if sorting:
            all_clients, new_sort = sorting
            return render(response, 'main/clients.html',
                          {
                "clients":enumerate(all_clients), 
                "sort": new_sort, 
                'form':form,
                'search' : search_str
            })
    return render(response, 'main/clients.html',
        {
            "clients":enumerate(all_clients), 
            'sort':'asc', 
            'form':form,
            'search' : search_str
    })  

def client_add(response):
    pass
    # instead of this view, goes to register panel
    # if not response.user.is_superuser:
    #     return redirect(index)
            
    # form = EditClient()
    # return render(response, 'main/client_edit.html', {
    #     'form':form, 
    #     'header': 'Dodaj nowego klienta',
    #     'action': '/client-action/added'
    #     })        

def client(response, username: str):
    if not response.user.is_superuser:
        return redirect(index)            
    col_clients = db_handle['clients']
    client = col_clients.find_one({'_id': username})
    return render(response, 'main/client.html', {'client':client})

def client_edit(response, username: str):
    if not response.user.is_superuser:
        return redirect(index)
            
    col_clients = db_handle['clients']
    client = next(iter(col_clients.find({'_id': username})), None)
    if not client:
        render(response, 'main/info.html', {'info': 'Błąd: nie znaleziono takiego klienta', 'return_href':'/clients/'})

    form = EditClient()
    for field_name in form.fields.keys():
        form.fields[field_name].initial = client.get(field_name, '')   

    return render(response, 'main/client_edit.html', {
        'form':form, 
        'header': 'Edytuj',
        'desc': f'{client.get("name","").title()} {client.get("surname","").title()}',
        'action': f'/client-action/edited/{client.get('_id')}'
        })

def client_edited(response, action: str|None = None, username: str|None= None):
    if not response.user.is_superuser:
        return redirect(index)
            
    if response.method == 'POST':        
        form = EditClient(response.POST)
        if form.is_valid():
            col_clients = db_handle['clients']
            query = {}
            data = form.cleaned_data
            query['name'] = data.get('name','').strip()
            query['surname']  = data.get('surname', '').strip()
            query['adress'] = data.get('adress','').strip()
            query['phone'] = data.get('phone','').strip()

            # filter_q = {'_id': query['username']}
            # existing_client = col_clients.find_one(filter_q)
            # if phone != query['phone'] and existing_client:
            #     return render(response, 'main/info.html', {'info':'Numer telefonu został już wykorzystany', 'return_href': '/clients/'})

            if action == 'added':
                query['addDate'] = datetime.now()
                query['moviesRented'] = 0
                col_clients.insert_one(query)
                info = 'Dodano nowego klienta'
            else:
                # edited
                filter_q= {'_id': username}
                col_clients.update_one(filter_q, {"$set": query}, upsert=True)
                info = 'Zapisano zmiany'
    return render(response, 'main/info.html', {'info':info, 'return_href': '/clients/'})

def client_delete(response, username: str):
    if not response.user.is_superuser:
        return redirect(index)
            
    # check if film in currently rented
    col_clients = db_handle['clients']
    client = col_clients.find_one({'_id':username})
    if client.get('moviesRented'):
        return render(response, 'main/info.html', {'info': 'Klient nie zwrócił wszystkich filmów!', 'return_href':'/clients/'})

    form = ConfirmForm()
    return render(response, 'main/confirm.html', {
        'form':form,
        'action_href': f'/client/{username}/deleted',
        'return_href': '/clients/',
        'message': 'Na pewno usunąć?'
        })


def client_deleted(response, username:str):
    if not response.user.is_superuser:
        return redirect(index)
            
    if response.method == 'POST':
        form = ConfirmForm(response.POST)
        if form.is_valid():
            if form.cleaned_data['confirm']:
                # delete client
                col_clients = db_handle['clients']
                col_clients.delete_one({'_id': username})
                return render(response, 'main/info.html', {'info':'Klient usunięty','return_href':'/clients/'})
            else:
                return redirect(clients_search)
    return redirect(clients_search)
#endregion
