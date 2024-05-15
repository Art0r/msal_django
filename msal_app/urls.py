from django.urls import path
from msal_app import views

urlpatterns = [
    path(route='', view=views.index, name='index'),
    path(route='login', view=views.login, name='login'),
    path(route='auth/callback', view=views.auth_callback, name='auth_callback')
]
