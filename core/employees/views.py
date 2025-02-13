import pandas as pd
import os
from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import Group, Permission, User
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Count, F, Case, When, IntegerField, Value, Prefetch, TextField
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import StringAgg
from employees.models import Employee, EmployeeJobSpecialty, EmployeeJobLevel, EmployeeJob, EmployeeStatus
from employees.forms import EmployeeCreationForm, EmployeeUpdateForm, EmployeeExcelUploadForm
from employees.utils import insert_excel_employees, update_excel_employees, handle_uploaded_file
from employees.tasks import import_employees_task
from celery.result import AsyncResult
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['positions'] = EmployeeJob.objects.all()
        context['specialties'] = EmployeeJobSpecialty.objects.all()
        context['genders'] = ['MALE', 'FEMALE']
        context['employee_status'] = EmployeeStatus.objects.filter(
            name__in=['REGULAR', 'PROBATION', 'SEPARATED'])

        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeCreationForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee-list')


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'employees/employee_detail.html'


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeUpdateForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee-list')

    def form_valid(self, form):
        #
        messages.success(self.request, 'Employee updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        #
        messages.warning(self.request, 'Please check errors below')
        return super().form_invalid(form)


@login_required
def ajx_employee_list(request):

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    position_filter = request.GET.getlist('position[]', [])
    specialty_filter = request.GET.getlist('specialty[]', [])
    gender_filter = request.GET.getlist('gender[]', [])
    employee_status_filter = request.GET.getlist('employee_status[]', [])

    #
    employees = Employee.objects.all()

    if search_value:
        employees = employees.filter(

            Q(company_id__icontains=search_value) |
            Q(start_date__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__first_name__icontains=search_value) |
            Q(middle_name__icontains=search_value) |
            Q(position__name__icontains=search_value) |
            Q(position_specialties__name__icontains=search_value) |
            Q(position_level__name__icontains=search_value) |
            Q(gender__icontains=search_value) |
            Q(status__name__icontains=search_value)

        ).distinct()

    if position_filter:
        employees = employees.filter(position__name__in=position_filter)

    if specialty_filter:
        employees = employees.filter(
            position_specialties__name__in=specialty_filter)

    if gender_filter:
        employees = employees.filter(gender__in=gender_filter)

    if employee_status_filter:
        employees = employees.filter(status__name__in=employee_status_filter)

    #
    employees = employees.filter(
        user__is_active=True, user__is_superuser=False)

    #
    employees = employees.annotate(
        specialties_agg=Coalesce(
            StringAgg('position_specialties__name', ', ', distinct=True),
            Value(''),
            output_field=TextField()
        )
    )

    # Handle ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'id')

    if order_column == 'last_name':
        order_column = 'user__last_name'
        if order_direction == 'desc':
            employees = employees.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            employees = employees.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'specialties':
        order_column = 'specialties_agg'
        if order_direction == 'desc':
            employees = employees.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            employees = employees.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'first_name':
        order_column = 'user__first_name'
        if order_direction == 'desc':
            employees = employees.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            employees = employees.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'level':
        order_column = 'position_level'
        if order_direction == 'desc':
            employees = employees.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            employees = employees.order_by(
                F(order_column).asc(nulls_last=True))
    else:
        if order_direction == 'desc':
            order_column = f'-{order_column}'
        employees = employees.order_by(order_column)

    #
    employees = employees.select_related(
        'status', 'position', 'position_level', 'user')
    employees = employees.prefetch_related('position_specialties')

    paginator = Paginator(employees, length)
    total_records = paginator.count
    employees_page = paginator.get_page(start // length + 1)

    #
    data = []

    for emp in employees_page:
        specialties = ', '.join([specialty.name for specialty in emp.position_specialties.all(
        )]) if emp.position_specialties else ''

        data.append({

            'company_id': f"<a href='/employees/{emp.id}/'>{emp.company_id}</a>",
            'start_date': emp.start_date,
            'last_name': emp.user.last_name,
            'first_name': emp.user.first_name,
            'middle_name': emp.middle_name,
            'position': emp.position.name if emp.position else '',
            'specialties': specialties,
            'level': emp.position_level.name if emp.position_level else '',
            'gender': emp.gender,
            'status': emp.status.name if emp.status else ''

        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    }

    return JsonResponse(response)


@login_required
def ajx_export_excel_all_employees(request):

    #
    employees = Employee.objects.all()

    #
    employees = employees.filter(
        user__is_active=True, user__is_superuser=False)

    #
    employees = employees.select_related(
        'status', 'position', 'position_level', 'user')
    employees = employees.prefetch_related('position_specialties')

    # Data to be exported
    data = []
    for employee in employees:
        specialties = ', '.join([specialty.name for specialty in employee.position_specialties.all(
        )]) if employee.position_specialties else ''

        data.append({
            'COMPANY ID': employee.company_id,
            'FIRST NAME': employee.user.first_name,
            'LAST NAME': employee.user.last_name,
            'MIDDLE NAME': employee.middle_name,
            'GENDER': employee.gender,
            'EMAIL': employee.user.email,
            'CONTACT': employee.contact,
            'ADDRESS': employee.address,
            'BIRTH DATE': employee.birth_date,
            'START DATE': employee.start_date,
            'STATUS': employee.status.name if employee.status else '',
            'POSITION': employee.position.name if employee.position else '',
            'POSITION LEVEL': employee.position_level.name if employee.position_level else '',
            'POSITION SPECIALTIES': specialties,
            'REGULAR DATE': employee.regular_date,
            'SEPARATION DATE': employee.separation_date if employee.separation_date else '',
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"employee_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})


@login_required
def ajx_export_excel_filtered_employees(request):
    #
    search_value = request.GET.get('search[value]', '')
    #
    position_filter = request.GET.getlist('position[]', [])
    specialty_filter = request.GET.getlist('specialty[]', [])
    gender_filter = request.GET.getlist('gender[]', [])
    employee_status_filter = request.GET.getlist('employee_status[]', [])

    # Initial query with select_related for reducing the number of queries
    employees = Employee.objects.select_related(
        'status', 'position', 'position_level', 'user'
    ).prefetch_related('position_specialties')

    # Apply search filtering
    if search_value:
        employees = employees.filter(

            Q(company_id__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(user__first_name__icontains=search_value) |
            Q(middle_name__icontains=search_value) |
            Q(position__name__icontains=search_value) |
            Q(position_specialties__name__icontains=search_value) |
            Q(position_level__name__icontains=search_value) |
            Q(gender__icontains=search_value) |
            Q(status__name__icontains=search_value)

        ).distinct()

    if position_filter:
        employees = employees.filter(position__name__in=position_filter)

    if specialty_filter:
        employees = employees.filter(
            position_specialties__name__in=specialty_filter)

    if gender_filter:
        employees = employees.filter(gender__in=gender_filter)

    if employee_status_filter:
        employees = employees.filter(status__name__in=employee_status_filter)

    #
    employees = employees.filter(
        user__is_active=True, user__is_superuser=False)

    #
    employees = employees.annotate(
        specialties_agg=Coalesce(
            StringAgg('position_specialties__name', ', ', distinct=True),
            Value(''),
            output_field=TextField()
        )
    )

    # Data to be exported
    data = []
    for employee in employees:
        specialties = ', '.join([specialty.name for specialty in employee.position_specialties.all(
        )]) if employee.position_specialties else ''

        data.append({
            'COMPANY ID': employee.company_id,
            'FIRST NAME': employee.user.first_name,
            'LAST NAME': employee.user.last_name,
            'MIDDLE NAME': employee.middle_name,
            'GENDER': employee.gender,
            'EMAIL': employee.user.email,
            'CONTACT': employee.contact,
            'ADDRESS': employee.address,
            'BIRTH DATE': employee.birth_date,
            'START DATE': employee.start_date,
            'STATUS': employee.status.name if employee.status else '',
            'POSITION': employee.position.name if employee.position else '',
            'POSITION LEVEL': employee.position_level.name if employee.position_level else '',
            'POSITION SPECIALTIES': specialties,
            'REGULAR DATE': employee.regular_date,
            'SEPARATION DATE': employee.separation_date if employee.separation_date else '',
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"filtered_employee_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})


@login_required
def ajx_import_insert_excel_employees_celery(request):
    #
    if request.method == 'POST':
        form = EmployeeExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # upload the file first in our system so we can have a path
                file_path = handle_uploaded_file(file)

                # start import of data using celery
                # this returns a task.id even if import_employees_task def has only pass. This means that we don't need to return anything from this def because .delay still returns a task even if there's none. It also doesn't matter if we return True or False to the function that we're calling
                # return JsonResponse({'status': 'testing', 'message': f"task is {task} and task.id is {task.id}"})
                task = import_employees_task.delay(file_path, mode='INSERT')

                return JsonResponse({'status': 'started', 'task_id': task.id, 'message': f"Import Insert Process TaskID {task.id} started. Please wait..."})
            except FileNotFoundError:
                # mostly it goes here if media/uploads directory doesn't exist or handle_uploaded_file not able to upload the file correctly
                return JsonResponse({'status': 'error', 'message': f"EV31: {str(FileNotFoundError)}. Check file or directory location"})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f"EV30: {type(e)} | {str(e)}"})

    return JsonResponse({'status': 'error', 'message': 'EV03: Invalid request method.'})


@login_required
def ajx_import_update_excel_employees_celery(request):
    #
    if request.method == 'POST':
        form = EmployeeExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                file_path = handle_uploaded_file(file)
                task = import_employees_task.delay(file_path, mode='UPDATE')

                return JsonResponse({'status': 'started', 'task_id': task.id, 'message': f"Import Update Process TaskID {task.id} started. Please wait..."})
            except FileNotFoundError:
                return JsonResponse({'status': 'error', 'message': f"EV33: {str(FileNotFoundError)}. Check file or directory location"})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f"EV32: {type(e)} | {str(e)}"})

    return JsonResponse({'status': 'error', 'message': 'EV06: Invalid request method.'})


@login_required
def ajx_tasks_status(request, task_id):
    # task.state might return PENDING, SUCCESS, or FAILURE
    # FAILURE triggers when function called by .delay raise an error
    task = AsyncResult(task_id)

    return JsonResponse({
        'status': task.state,
        'task_id': task_id,
        # task.result has value only when function called by .delay raise an error
        'message': str(task.result),
    })
