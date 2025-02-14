from django.db import models
from companies.models import Company
from decimal import Decimal
from datetime import datetime
from html_sanitizer.django import get_sanitizer


class ItemUnit(models.Model):
    name = models.CharField(max_length=20, unique=True)
    # CASE, ...

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=300, unique=True,
                            blank=False, null=False)
    excerpt = models.CharField(max_length=250, blank=True)
    weight = models.DecimalField(
        max_digits=10,  # Adjust as needed
        decimal_places=5,  # Allows up to five decimal places
        default=Decimal("0.0"),
    )
    unit = models.ForeignKey(ItemUnit, on_delete=models.SET_NULL,
                             blank=False, null=True, related_name="item_unit")
    num_per_unit = models.PositiveIntegerField(
        default=0, blank=False, null=False)
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, blank=False, null=True, related_name="item_company")
    price = models.DecimalField(
        max_digits=10,  # Adjust based on expected price range
        decimal_places=2,  # Standard for prices (e.g., 100.00, 100.01)
        default=Decimal("0.00")
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        sanitizer = get_sanitizer()
        self.excerpt = sanitizer.sanitize(self.excerpt)

        super().save(*args, **kwargs)


class ItemPriceAdjustment(models.Model):
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="item_price_adjustment_item")
    date = models.DateField(default=datetime.now)
    new_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    def __str__(self):
        return f'price {self.price} on {self.date}'
