import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


class Base(models.Model):
    '''
    This is the class that will be extended from all other models
    '''
    __slots__ = ('id', 'created', 'updated')

    id = models.UUIDField(name='id', primary_key=True,
                          default=uuid.uuid4, editable=False)
    created = models.DateTimeField(
        name='created', auto_now_add=True, editable=False)
    updated = models.DateTimeField(name='updated', auto_now=True)

    class Meta:
        abstract = True


class CustomUser(Base, AbstractUser):
    __slots__ = ('msal_id',)

    msal_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    class Meta:
        ordering = ('created',)
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        abstract = False
    
    def __str__(self):
        return self.username
