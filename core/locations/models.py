from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=250)

    def __str__(self):
        return f'{self.name} - {self.address}'
