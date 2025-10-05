from django.contrib.auth.models import AbstractUser
from django.db import models

from users.custom_managers import UserManager


# Create your models here.

class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    HR = "HR", "HR"
    EMPLOYEE = "EMPLOYEE", "Employee"

class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=25, blank=True)
    last_name = models.CharField(max_length=25, blank=True)
    email = models.EmailField(unique=True, blank=True)
    phone_number = models.CharField(max_length=11, blank=True)
    username = models.CharField(max_length=11, unique=True, blank=False, null=False)
    role = models.CharField(choices=Role.choices, max_length=20, default=Role.EMPLOYEE)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def is_admin(self):
        return self.role == Role.ADMIN
    def is_hr(self):
        return self.role == Role.HR
    def is_employee(self):
        return self.role == Role.EMPLOYEE
    def __str__(self):
        return self.username
    def __repr__(self):
        return self.username