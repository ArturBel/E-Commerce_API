from django.contrib.auth.models import AbstractUser
from django.db import models
from argon2 import PasswordHasher


ph = PasswordHasher()


class CustomUser(AbstractUser):
    first_name = models.CharField(unique=False, max_length=64)
    last_name = models.CharField(unique=False, max_length=64)
    username = models.CharField(unique=True, max_length=64)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def hash_password(self, raw_password: str):
        self.password = ph.hash(raw_password)
    
    def check_password(self, raw_password: str):
        return ph.verify(self.password, raw_password)