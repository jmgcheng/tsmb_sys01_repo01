from django import forms
from transacts.models import TransactStatus, TransactHeader, TransactDetail
from django.forms import modelformset_factory, inlineformset_factory


class TransactHeaderForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(
        attrs={'type': 'date'}), required=True)

    class Meta:
        model = TransactHeader
        fields = ['si_no', 'date', 'location',  'company', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the default value for status to "FILED" if not already set
        # This checks if it's a new form (not editing an existing record)
        if not self.instance.pk:
            try:
                filed_status = TransactStatus.objects.get(name="FILED")
                self.fields['status'].initial = filed_status
            except TransactStatus.DoesNotExist:
                pass  # If "FILED" status does not exist, just leave it empty

    def clean(self):
        cleaned_data = super().clean()
        si_no = cleaned_data.get('si_no', '')

        #
        cleaned_data['si_no'] = si_no.upper().replace(' ', '-')

        return cleaned_data


class TransactDetailForm(forms.ModelForm):
    class Meta:
        model = TransactDetail
        fields = ['item', 'quantity']


# in use for extra 1
TransactInlineFormSet = inlineformset_factory(
    TransactHeader,
    TransactDetail,
    form=TransactDetailForm,
    fields=['item', 'quantity'],
    extra=1,  # Set the number of empty forms to display
    can_delete=True,
)

# in use for extra is 0
TransactInlineFormSetNoExtra = inlineformset_factory(
    TransactHeader,
    TransactDetail,
    form=TransactDetailForm,
    fields=['item', 'quantity'],
    extra=0,  # Set the number of empty forms to display
    can_delete=True,
)
