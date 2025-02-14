import pandas as pd
import os
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required, login_required
from django.db.models import Q, Count, F, Case, When, IntegerField, Value, Prefetch, TextField
from django.db.models.functions import Coalesce
from items.models import ItemUnit, Item, ItemPriceAdjustment
from companies.models import Company
from items.forms import ItemForm, ItemPriceAdjustmentForm, ItemExcelUploadForm
from items.utils import insert_excel_items, update_excel_items, handle_uploaded_file
from items.tasks import import_items_task
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from celery.result import AsyncResult


class ItemListView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'items/item_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = ItemUnit.objects.all()
        context['companies'] = Company.objects.all()

        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:item-list')


class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'items/item_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = get_object_or_404(
            Item, pk=self.kwargs['pk'])

        conv_to_kg = '-'
        if item.num_per_unit and item.weight:
            conv_to_kg = item.num_per_unit * item.weight

        # Add the annotated object to the context
        context['conv_to_kg'] = conv_to_kg
        return context


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:item-list')

    def form_valid(self, form):
        #
        messages.success(
            self.request, 'Item updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        #
        messages.warning(self.request, 'Please check errors below')
        return super().form_invalid(form)


@login_required
def ajx_item_list(request):

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    company_filter = request.GET.getlist('company[]', [])
    unit_filter = request.GET.getlist('unit[]', [])

    #
    items = Item.objects.all()

    if search_value:
        items = items.filter(
            Q(name__icontains=search_value)
        ).distinct()

    if company_filter:
        items = items.filter(
            company__name__in=company_filter)

    if unit_filter:
        items = items.filter(
            unit__name__in=unit_filter)

    # Handle ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'id')

    if order_column == 'company':
        order_column = 'company__name'
        if order_direction == 'desc':
            items = items.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            items = items.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'unit':
        order_column = 'unit__name'
        if order_direction == 'desc':
            items = items.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            items = items.order_by(
                F(order_column).asc(nulls_last=True))
    else:
        if order_direction == 'desc':
            order_column = f'-{order_column}'
        items = items.order_by(order_column)

    #
    items = items.select_related(
        'unit', 'company')

    paginator = Paginator(items, length)
    total_records = paginator.count
    items_page = paginator.get_page(start // length + 1)

    #
    data = []

    for i in items_page:
        data.append({
            'name': f"<a href='/items/{i.id}/'>{i.name}</a>",
            'company': i.company.name if i.company else '',
            'unit': i.unit.name if i.unit else '',
            'num_per_unit': i.num_per_unit if i.num_per_unit else 0,
            'weight': i.weight if i.weight else 0.0,
            'convert_kilo': (i.num_per_unit * i.weight) if i.num_per_unit and i.weight else 0.0,
        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    }

    return JsonResponse(response)


@login_required
def ajx_export_excel_all_items(request):

    #
    items = Item.objects.all()

    #
    items = items.select_related(
        'unit', 'company')

    # Data to be exported
    data = []
    for item in items:

        data.append({
            'NAME': item.name,
            'COMPANY': item.company.name,
            'UNIT': item.unit.name,
            'NUM PER UNIT': item.num_per_unit,
            'WEIGHT': item.weight,
            'ORIGINAL PRICE': item.price,
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"item_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})


@login_required
def ajx_export_excel_filtered_items(request):
    #
    search_value = request.GET.get('search[value]', '')
    #
    company_filter = request.GET.getlist('company[]', [])
    unit_filter = request.GET.getlist('unit[]', [])

    # Initial query with select_related for reducing the number of queries
    items = Item.objects.select_related(
        'unit', 'company'
    )

    # Apply search filtering
    if search_value:
        items = items.filter(

            Q(name__icontains=search_value)

        ).distinct()

    if company_filter:
        items = items.filter(
            company__name__in=company_filter)

    if unit_filter:
        items = items.filter(
            unit__name__in=unit_filter)

    # Data to be exported
    data = []
    for item in items:

        data.append({
            'NAME': item.name,
            'COMPANY': item.company.name,
            'UNIT': item.unit.name,
            'NUM PER UNIT': item.num_per_unit,
            'WEIGHT': item.weight,
            'ORIGINAL PRICE': item.price,
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"filtered_item_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})


@login_required
def ajx_import_insert_excel_items_celery(request):
    #
    if request.method == 'POST':
        form = ItemExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # upload the file first in our system so we can have a path
                file_path = handle_uploaded_file(file)

                # start import of data using celery
                # this returns a task.id even if import_items_task def has only pass. This means that we don't need to return anything from this def because .delay still returns a task even if there's none. It also doesn't matter if we return True or False to the function that we're calling
                # return JsonResponse({'status': 'testing', 'message': f"task is {task} and task.id is {task.id}"})
                task = import_items_task.delay(file_path, mode='INSERT')

                return JsonResponse({'status': 'started', 'task_id': task.id, 'message': f"Import Insert Process TaskID {task.id} started. Please wait..."})
            except FileNotFoundError:
                # mostly it goes here if media/uploads directory doesn't exist or handle_uploaded_file not able to upload the file correctly
                return JsonResponse({'status': 'error', 'message': f"EV31: {str(FileNotFoundError)}. Check file or directory location"})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f"EV30: {type(e)} | {str(e)}"})

    return JsonResponse({'status': 'error', 'message': 'EV03: Invalid request method.'})


@login_required
def ajx_import_update_excel_items_celery(request):
    #
    if request.method == 'POST':
        form = ItemExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                file_path = handle_uploaded_file(file)
                task = import_items_task.delay(file_path, mode='UPDATE')

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
