from django import forms
from locations.models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'address']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name', '')
        address = cleaned_data.get('address', '')

        #
        cleaned_data['name'] = name.upper()

        return cleaned_data
