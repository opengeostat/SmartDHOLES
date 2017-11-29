# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User, BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator

# Create your models here.

class AppUserManager(BaseUserManager):
    def create_user(self, username, password=None):
        """
        Creates and saves a User with the given username, full name, email and password.
        """
        if not username:
            raise ValueError('Users must have an username')
        user = self.model(
            username=username
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        """
        Creates and saves a superuser with the given username and password.
        """
        user = self.create_user(
            username = username,
            password = password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class AppUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True)
    fullname = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = AppUserManager()

    USERNAME_FIELD = 'username'

    def get_full_name(self):
        # The user is identified by their username
        return self.fullname

    def get_short_name(self):
        # This is the one to show to the public
        return self.username

    def __unicode__(self): # __unicode__ on Python 2
        return self.username
    def assign_perm(self, perm, obj=None):
        return assign_perm(perm, self, obj)
    def remove_perm(self, perm, obj):
        return remove_perm(perm, self, obj)
