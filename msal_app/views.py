from functools import wraps
import logging
import uuid
from django.shortcuts import redirect, render
from django.http import HttpRequest
from msal import ConfidentialClientApplication
from msal_app.models import CustomUser
from msal_project.settings import MSAL_CONFIG
from django.contrib import auth
import random
from django.contrib.auth.hashers import make_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = ConfidentialClientApplication(
    MSAL_CONFIG['CLIENT_ID'],
    authority=MSAL_CONFIG['AUTHORITY'],
    client_credential=MSAL_CONFIG['SECRET'],
)


def msal_login_required(func):
    @wraps(func)
    def wrapper(request: HttpRequest, *args, **kwargs):
        logger.info("Entering msal_login_required")

        access_token = request.session.get('access_token')
        refresh_token = request.session.get('refresh_token')
        
        if refresh_token == None:
            return redirect("login")

        if access_token == None:
            return redirect("login")

        result = app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=MSAL_CONFIG['SCOPE']
        )
        
        if 'access_token' in result:
            request.session['access_token'] = result.get('access_token')
            return func(request, *args, **kwargs)
            
        return redirect("login")
        
    return wrapper


@msal_login_required
def index(request: HttpRequest):

    context = {}

    return render(context=context, request=request, template_name='index.html')


def login(request: HttpRequest):
    logger.info("Entering login view")

    request.session["state"] = str(uuid.uuid4())

    auth_url = app.get_authorization_request_url(
        scopes=MSAL_CONFIG['SCOPE'],
        redirect_uri='http://localhost:8000/auth/callback',
        state=request.session["state"]
    )

    logger.info(f"Redirecting to auth URL: {auth_url}")
    
    return redirect(auth_url)


def auth_callback(request: HttpRequest):
    logger.info("Entering auth_callback view")\
    
    code = request.GET.get('code')

    result = app.acquire_token_by_authorization_code(
        code,
        scopes=MSAL_CONFIG['SCOPE'],
        redirect_uri='http://localhost:8000/auth/callback',
    )

    if 'access_token' in result:
        logger.info("Access token acquired")
        user_data = result['id_token_claims']
        request.session['code'] = code

        fullname: str = user_data['name']
        splitted_fullname: list[str] = fullname.split(' ')

        username = f"{splitted_fullname[0].lower()}.{splitted_fullname[-1].lower()}{random_number_with_length(3)}"
        
        default_password= f"{splitted_fullname[0].lower()}.{splitted_fullname[-1].lower()}1239"
        
        user, _ = CustomUser.objects.get_or_create(
            msal_id=user_data['oid'],
            defaults={'username': username, 'email': user_data['preferred_username'],
                      'first_name': splitted_fullname[0], 'last_name': splitted_fullname[-1],
                      'password': make_password(default_password)}
        )

        auth.login(request=request, user=user)
        request.session['access_token'] = result.get('access_token')
        request.session['refresh_token'] = result.get('refresh_token')

        logger.info("User authenticated and session set, redirecting to home")
        return redirect("/")
        
    logger.warning("Access token not acquired, redirecting to login")
    request.session.flush()
    
    return redirect("login")


def random_number_with_length(x):
    if x <= 0:
        raise ValueError("Length must be a positive integer.")
    start = 10**(x - 1)
    end = 10**x - 1
    return random.randint(start, end)