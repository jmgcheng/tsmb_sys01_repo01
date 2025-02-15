from django.contrib import admin
from transacts.models import TransactStatus, TransactHeader, TransactDetail

admin.site.register(TransactStatus)
admin.site.register(TransactHeader)
admin.site.register(TransactDetail)
