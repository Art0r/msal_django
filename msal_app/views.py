from django.shortcuts import redirect, render
from django.http import HttpRequest
from msal import ConfidentialClientApplication

from msal_project.settings import MSAL_CONFIG

def index(request: HttpRequest):

    access_token = request.session.get('access_token')
    if not access_token:
        return redirect('login')
    
    context = {}

    return render(context=context, request=request, template_name='index.html')


def login(request: HttpRequest):

    app = ConfidentialClientApplication(
        MSAL_CONFIG.get('CLIENT_ID'),
        authority=MSAL_CONFIG.get('AUTHORITY'),
        client_credential=MSAL_CONFIG.get('SECRET'),
    )

    auth_url = app.get_authorization_request_url(MSAL_CONFIG.get('SCOPE'))

    return redirect(auth_url)


def auth_callback(request: HttpRequest):
    code = request.GET.get('code')

    app = ConfidentialClientApplication(
        MSAL_CONFIG.get('CLIENT_ID'),
        authority=MSAL_CONFIG.get('AUTHORITY'),
        client_credential=MSAL_CONFIG.get('SECRET'),
    )

    result = app.acquire_token_by_authorization_code(
        code,
        scopes=MSAL_CONFIG.get('SCOPE'),
        redirect_uri='http://localhost:8000/auth/callback',
    )

    request.session['access_token'] = result['access_token']

    return redirect("/")