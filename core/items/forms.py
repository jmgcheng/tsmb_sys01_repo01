from django import forms
from items.models import ItemUnit, Item, ItemPriceAdjustment
from decimal import Decimal
from datetime import datetime


class ItemUnitForm(forms.ModelForm):
    class Meta:
        model = ItemUnit
        fields = ['name']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name', '')

        #
        cleaned_data['name'] = name.upper()

        return cleaned_data


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'excerpt', 'weight', 'unit',
                  'num_per_unit', 'company', 'price']
        labels = {
            "num_per_unit": "Packs/Case"
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name', '')
        excerpt = cleaned_data.get('excerpt', '')
        weight = cleaned_data.get('weight', None)
        num_per_unit = cleaned_data.get('num_per_unit', None)
        price = cleaned_data.get('price', None)

        # Convert name to uppercase
        if name:
            cleaned_data['name'] = name.upper()

        # Validate weight
        if weight is not None and weight < Decimal("0"):
            self.add_error("weight", "Weight cannot be negative.")

        # Validate price
        if price is not None and price < Decimal("0"):
            self.add_error("price", "Price cannot be negative.")

        # Validate packs per unit
        if num_per_unit is not None and num_per_unit < Decimal("1"):
            self.add_error(
                "num_per_unit", "Packs per unit needs to be atleast 1.")

        return cleaned_data


class ItemPriceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = ItemPriceAdjustment
        fields = ['item', 'date', 'new_price']

    def clean(self):
        cleaned_data = super().clean()
        new_price = cleaned_data.get('new_price', None)

        # Validate new_price
        if new_price is not None and new_price < Decimal("0"):
            self.add_error("new_price", "New Price cannot be negative.")

        return cleaned_data


class ItemExcelUploadForm(forms.Form):
    file = forms.FileField()
