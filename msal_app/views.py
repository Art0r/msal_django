from functools import wraps
import logging
from django.shortcuts import redirect, render
from django.http import HttpRequest
from msal import ConfidentialClientApplication
from msal_app.models import CustomUser
from msal_project.settings import MSAL_CONFIG
from django.contrib import auth
import random


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def msal_login_required(func):
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        app = ConfidentialClientApplication(
            MSAL_CONFIG['CLIENT_ID'],
            authority=MSAL_CONFIG['AUTHORITY'],
            client_credential=MSAL_CONFIG['SECRET'],
        )
        
        result = app.acquire_token_silent(scopes=MSAL_CONFIG['SCOPE'], account=None)
        
        if not result:
            request.session.flush()
            return redirect('login')    
        
        session_token = request.session.get('access_token')
        result_token = result.get('access_token')
        
        print(session_token)
        print(result_token)
        if session_token == None or result_token == None:
            request.session.flush()
            return redirect('login')    

        if session_token != result_token:
            request.session.flush()
            return redirect('login')    
        
        if request.user.is_anonymous:
            request.session.flush()
            return redirect("login")
        
        return func(request, *args, **kwargs)
    
    return wrapper


@msal_login_required
def index(request: HttpRequest):

    msal_login_required(request)

    context = {}

    return render(context=context, request=request, template_name='index.html')


def login(request: HttpRequest):

    app = ConfidentialClientApplication(
        MSAL_CONFIG['CLIENT_ID'],
        authority=MSAL_CONFIG['AUTHORITY'],
        client_credential=MSAL_CONFIG['SECRET'],
    )

    auth_url = app.get_authorization_request_url(MSAL_CONFIG['SCOPE'])

    return redirect(auth_url)


def auth_callback(request: HttpRequest):
    code = request.GET.get('code')

    app = ConfidentialClientApplication(
        MSAL_CONFIG['CLIENT_ID'],
        authority=MSAL_CONFIG['AUTHORITY'],
        client_credential=MSAL_CONFIG['SECRET'],
    )

    result = app.acquire_token_by_authorization_code(
        code,
        scopes=MSAL_CONFIG['SCOPE'],
        redirect_uri='http://localhost:8000/auth/callback',
    )

    if 'access_token' in result:
        user_data = result['id_token_claims']

        fullname: str = user_data['name']
        splitted_fullname: list[str] = fullname.split(' ')

        username = f"{splitted_fullname[0].lower()}.{splitted_fullname[-1].lower()}{random_number_with_length(3)}"

        user, _ = CustomUser.objects.get_or_create(
            msal_id=user_data['oid'],
            defaults={'username': username, 'email': user_data['preferred_username'], 
                      'first_name': splitted_fullname[0], 'last_name': splitted_fullname[-1]}
        )

        auth.login(request=request, user=user)
        request.session['access_token'] = result['access_token']
        
        return redirect("/")
    
    request.session.flush()
    
    return redirect("login")


def random_number_with_length(x):
    if x <= 0:
        raise ValueError("Length must be a positive integer.")
    start = 10**(x - 1)
    end = 10**x - 1
    return random.randint(start, end)