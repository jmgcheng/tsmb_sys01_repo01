from django.contrib import admin
from employees.models import Employee, EmployeeJob, EmployeeJobLevel, EmployeeJobSpecialty, EmployeeStatus


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'regular_date', 'status')
    search_fields = ('user', )


admin.site.register(EmployeeStatus)
admin.site.register(EmployeeJobSpecialty)
admin.site.register(EmployeeJobLevel)
admin.site.register(EmployeeJob)
admin.site.register(Employee, EmployeeAdmin)
