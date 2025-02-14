from django.contrib import admin
from items.models import ItemUnit, ItemPriceAdjustment, Item

admin.site.register(ItemUnit)
admin.site.register(ItemPriceAdjustment)
admin.site.register(Item)
