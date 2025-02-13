from django.db import models


class Customer(models.Model):
    customer_id = models.CharField(max_length=50, unique=True, default='')
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return f'{self.name}'
