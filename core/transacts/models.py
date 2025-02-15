from datetime import datetime
from django.db import models
from locations.models import Location
from customers.models import Customer
from companies.models import Company
from employees.models import Employee
from items.models import Item


class TransactStatus(models.Model):
    name = models.CharField(max_length=50, unique=True, null=False)
    # FILED, CANCELLED

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TransactHeader(models.Model):
    si_no = models.CharField(max_length=100)
    date = models.DateField(default=datetime.now)
    creator = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="transact_creator")
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.ForeignKey(TransactStatus, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['si_no', 'company'], name='unique_transact')
        ]

    def __str__(self):
        return f"TransactHeader #{self.code}"


class TransactDetail(models.Model):
    transact_header = models.ForeignKey(
        TransactHeader, on_delete=models.CASCADE, blank=False, null=True)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="transact_item")
    quantity = models.PositiveIntegerField(default=0, blank=False, null=False)

    def __str__(self):
        return f"TransactDetail #{self.id}"
