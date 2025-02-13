from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


def validate_age(value):
    today = timezone.now().date()
    age_limit = today - timedelta(days=18*365.25)
    if value > age_limit:
        raise ValidationError('Employee must be at least 18 years old.')


class EmployeeStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    # PROBATION, REGULAR, RESIGNED, TERMINATED, SEPARATED

    def __str__(self):
        return self.name


class EmployeeJob(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class EmployeeJobLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class EmployeeJobSpecialty(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_id = models.CharField(max_length=50, unique=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=[
                              ('MALE', 'MALE'), ('FEMALE', 'FEMALE')])
    birth_date = models.DateField(
        validators=[validate_age], blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    status = models.ForeignKey(
        EmployeeStatus, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField(blank=True, null=True)
    regular_date = models.DateField(blank=True, null=True)
    separation_date = models.DateField(blank=True, null=True)
    position = models.ForeignKey(
        EmployeeJob, on_delete=models.SET_NULL, null=True)
    position_level = models.ForeignKey(
        EmployeeJobLevel, on_delete=models.SET_NULL, null=True)
    position_specialties = models.ManyToManyField(
        EmployeeJobSpecialty, blank=True)

    def __str__(self):
        return self.company_id
