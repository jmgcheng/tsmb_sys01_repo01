import pandas as pd
import os
from datetime import datetime
from decimal import Decimal
from django.shortcuts import redirect, render
# from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Prefetch, DecimalField, ExpressionWrapper, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, Concat
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from transacts.models import TransactStatus, TransactHeader, TransactDetail
from items.models import ItemPriceAdjustment
from transacts.forms import TransactHeaderForm, TransactDetailForm, TransactInlineFormSet, TransactInlineFormSetNoExtra
from django.views import View
from xhtml2pdf import pisa


class TransactCreateView(LoginRequiredMixin, CreateView):
    model = TransactHeader
    template_name = 'transacts/transact_form.html'
    form_class = TransactHeaderForm
    success_url = reverse_lazy('transacts:transact-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = TransactInlineFormSet(
                self.request.POST, prefix='transact_detail', instance=self.object)
        else:
            context['formset'] = TransactInlineFormSet(
                prefix='transact_detail', instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        form.instance.creator = self.request.user.employee
        # form.instance.status = TransactStatus.objects.get(name='FILED')

        formset = context['formset']

        if formset.is_valid():
            transact_header = form.save()
            formset.instance = transact_header
            formset.save()

            #
            messages.success(
                self.request, 'Transact created successfully.')

            return super().form_valid(form)
        else:
            #
            messages.warning(self.request, 'Please check errors below')

            return self.form_invalid(form)


class TransactUpdateView(LoginRequiredMixin, UpdateView):
    model = TransactHeader
    template_name = 'transacts/transact_form.html'
    form_class = TransactHeaderForm
    success_url = reverse_lazy('transacts:transact-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            # Load existing TransactDetail objects for the header instance
            context['formset'] = TransactInlineFormSetNoExtra(
                self.request.POST, instance=self.object, prefix='transact_detail', )
        else:
            # Populate the formset with the existing details for the header instance
            context['formset'] = TransactInlineFormSetNoExtra(
                instance=self.object, prefix='transact_detail',)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            # Save the updated header instance
            transact_header = form.save()

            # Save the updated details for the header instance
            formset.instance = transact_header
            formset.save()

            #
            messages.success(
                self.request, 'Transact updated successfully.')

            return super().form_valid(form)
        else:
            #
            messages.warning(self.request, 'Please check errors below')

            return self.form_invalid(form)


class TransactDetailView(LoginRequiredMixin, DetailView):
    model = TransactHeader
    template_name = 'transacts/transact_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Subquery to get the latest price adjustment before or on the transaction date
        latest_price_adjustment = ItemPriceAdjustment.objects.filter(
            item=OuterRef('item'),
            date__lte=self.object.date  # Ensure we filter based on the transaction date
        ).order_by('-date').values('new_price')[:1]

        # Fetch TransactDetails with annotations
        context['details'] = TransactDetail.objects.select_related('item').filter(
            transact_header=self.object
        ).annotate(
            num_per_unit=Coalesce(F('item__num_per_unit'), 0),
            weight=Coalesce(F('item__weight'), Decimal('0.0')),
            convert_to_kilos=ExpressionWrapper(
                F('item__num_per_unit') * F('item__weight'),
                output_field=DecimalField()
            ),
            delivered_in_kilos=ExpressionWrapper(
                F('quantity') * F('item__num_per_unit') * F('item__weight'),
                output_field=DecimalField()
            ),
            price_posted=Coalesce(
                Subquery(latest_price_adjustment, output_field=DecimalField()),
                F('item__price')
            )
        )

        return context


class TransactListView(LoginRequiredMixin, ListView):
    model = TransactHeader
    template_name = 'transacts/transact_list.html'


class TransactDetailListView(LoginRequiredMixin, ListView):
    model = TransactHeader
    template_name = 'transacts/transact_detail_list.html'


@login_required
def ajx_transact_list(request):

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    #
    transacts = TransactHeader.objects.all()

    if search_value:
        transacts = transacts.filter(

            Q(si_no__icontains=search_value) |
            Q(company__name__icontains=search_value) |
            Q(location__name__icontains=search_value)

        ).distinct()

    #
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'id')

    if order_column == 'creator':
        order_column = 'creator__user__first_name'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'customer':
        order_column = 'customer__first_name'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'location':
        order_column = 'location__name'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'company':
        order_column = 'company__name'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'status':
        order_column = 'status__name'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    elif order_column == 'transact_id':
        order_column = 'id'
        if order_direction == 'desc':
            transacts = transacts.order_by(
                F(order_column).desc(nulls_last=True))
        else:
            transacts = transacts.order_by(
                F(order_column).asc(nulls_last=True))
    else:
        if order_direction == 'desc':
            order_column = f'-{order_column}'
        transacts = transacts.order_by(order_column)

    #
    transacts = transacts.select_related(
        'creator', 'customer', 'location', 'company', 'status')

    paginator = Paginator(transacts, length)
    total_records = paginator.count
    transacts_page = paginator.get_page(start // length + 1)

    #
    data = []

    for t in transacts_page:
        fullname_creator = ''
        if t.creator:
            fullname_creator = f'{t.creator.user.first_name} {t.creator.user.last_name}'
            fullname_creator = f'{fullname_creator} {t.creator.user.employee.middle_name}' if t.creator.user.employee.middle_name else fullname_creator

        fullname_customer = ''
        if t.customer:
            fullname_customer = f'{t.customer.first_name} {t.customer.last_name}'
            fullname_customer = f'{fullname_customer} {t.customer.middle_name}' if t.customer.middle_name else fullname_customer

        data.append({

            'transact_id': f"<a href='/transacts/{t.id}/'>{t.id}</a>",
            'si_no': t.si_no,
            'company': t.company.name if t.company else '',
            'date': t.date,
            'creator': fullname_creator,
            'location': t.location.name if t.location else '',
            # 'customer': fullname_customer,
            'status': t.status.name if t.status else '',

        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    }

    return JsonResponse(response)


@login_required
def ajx_transact_detail_list(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Subquery to get the most recent price adjustment before or on the transaction date
    latest_price_adjustment = ItemPriceAdjustment.objects.filter(
        item=OuterRef('item'),
        date__lte=OuterRef('transact_header__date')
    ).order_by('-date').values('new_price')[:1]

    transacts = TransactDetail.objects.select_related(
        'transact_header__creator',
        'transact_header__company',
        'transact_header__location',
        'item'
    ).annotate(
        transact_id=F('transact_header__id'),
        si_no=F('transact_header__si_no'),
        company_name=F('transact_header__company__name'),
        date=F('transact_header__date'),
        creator_name=Concat(F('transact_header__creator__user__first_name'), Value(
            ' '), F('transact_header__creator__user__last_name')),
        location_name=F('transact_header__location__name'),
        num_per_unit=Coalesce(F('item__num_per_unit'), 0),
        weight=Coalesce(F('item__weight'), Decimal('0.0')),
        convert_to_kilos=ExpressionWrapper(
            F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        delivered_in_kilos=ExpressionWrapper(
            F('quantity') * F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        price_posted=Coalesce(Subquery(
            latest_price_adjustment, output_field=DecimalField()), F('item__price'))
    )

    if search_value:
        transacts = transacts.filter(
            Q(transact_header__si_no__icontains=search_value) |
            Q(transact_header__company__name__icontains=search_value) |
            Q(transact_header__location__name__icontains=search_value) |
            Q(item__name__icontains=search_value)
        ).distinct()

    # date range filter
    if request.GET.get('minDate'):
        min_date = request.GET['minDate']
        transacts = transacts.filter(date__gte=min_date)

    if request.GET.get('maxDate'):
        max_date = request.GET['maxDate']
        transacts = transacts.filter(date__lte=max_date)

    # Sorting Fix
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'transact_id')

    column_map = {
        'transact_id': 'transact_id',
        'si_no': 'si_no',
        'company': 'company_name',
        'date': 'date',
        'creator': 'creator_name',
        'location': 'location_name',
        'item': 'item__name',
        'num_per_unit': 'num_per_unit',
        'weight': 'weight',
        'convert_to_kilos': 'convert_to_kilos',
        'quantity': 'quantity',
        'delivered_in_kilos': 'delivered_in_kilos',
        'price_posted': 'price_posted',
    }

    order_column = column_map.get(order_column, 'transact_id')

    if order_direction == 'desc':
        transacts = transacts.order_by(F(order_column).desc(nulls_last=True))
    else:
        transacts = transacts.order_by(F(order_column).asc(nulls_last=True))

    paginator = Paginator(transacts, length)
    total_records = paginator.count
    transacts_page = paginator.get_page(start // length + 1)

    # Fetch price adjustment history for each item
    item_ids = {t.item.id for t in transacts_page}
    price_histories = {item_id: [] for item_id in item_ids}

    adjustments = ItemPriceAdjustment.objects.filter(
        item_id__in=item_ids).order_by('date')
    for adj in adjustments:
        price_histories[adj.item_id].append((adj.date, adj.new_price))

    data = []
    for t in transacts_page:
        # Build remarks column
        remarks = f"Original Price {t.item.price}."
        if price_histories[t.item.id]:
            for date, new_price in price_histories[t.item.id]:
                remarks += f" Updated on {date.strftime('%b %d %Y')} to {new_price}."

        data.append({
            'transact_id': f"<a href='/transacts/{t.transact_id}/'>{t.transact_id}</a>",
            'si_no': t.si_no,
            'company': t.company_name,
            'date': t.date.strftime('%Y-%m-%d'),
            'creator': t.creator_name,
            'location': t.location_name,
            'item': t.item.name,
            'num_per_unit': t.num_per_unit,
            'weight': t.weight,
            'convert_to_kilos': t.convert_to_kilos,
            'quantity': t.quantity,
            'delivered_in_kilos': t.delivered_in_kilos,
            'price_posted': float(t.price_posted),
            'remarks': remarks
        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    }

    return JsonResponse(response)


@login_required
def ajx_export_transact_detail_list(request):

    # Subquery to get the most recent price adjustment before or on the transaction date
    latest_price_adjustment = ItemPriceAdjustment.objects.filter(
        item=OuterRef('item'),
        date__lte=OuterRef('transact_header__date')
    ).order_by('-date').values('new_price')[:1]

    transacts = TransactDetail.objects.select_related(
        'transact_header__creator',
        'transact_header__company',
        'transact_header__location',
        'item'
    ).annotate(
        transact_id=F('transact_header__id'),
        si_no=F('transact_header__si_no'),
        company_name=F('transact_header__company__name'),
        date=F('transact_header__date'),
        creator_name=Concat(F('transact_header__creator__user__first_name'), Value(
            ' '), F('transact_header__creator__user__last_name')),
        location_name=F('transact_header__location__name'),
        num_per_unit=Coalesce(F('item__num_per_unit'), 0),
        weight=Coalesce(F('item__weight'), Decimal('0.0')),
        convert_to_kilos=ExpressionWrapper(
            F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        delivered_in_kilos=ExpressionWrapper(
            F('quantity') * F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        price_posted=Coalesce(Subquery(
            latest_price_adjustment, output_field=DecimalField()), F('item__price'))
    )

    # Sorting Fix
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'transact_id')

    column_map = {
        'transact_id': 'transact_id',
        'si_no': 'si_no',
        'company': 'company_name',
        'date': 'date',
        'creator': 'creator_name',
        'location': 'location_name',
        'item': 'item__name',
        'num_per_unit': 'num_per_unit',
        'weight': 'weight',
        'convert_to_kilos': 'convert_to_kilos',
        'quantity': 'quantity',
        'delivered_in_kilos': 'delivered_in_kilos',
        'price_posted': 'price_posted',
    }

    order_column = column_map.get(order_column, 'transact_id')

    if order_direction == 'desc':
        transacts = transacts.order_by(F(order_column).desc(nulls_last=True))
    else:
        transacts = transacts.order_by(F(order_column).asc(nulls_last=True))

    # Fetch price adjustment history for each item
    item_ids = {t.item.id for t in transacts}
    price_histories = {item_id: [] for item_id in item_ids}

    adjustments = ItemPriceAdjustment.objects.filter(
        item_id__in=item_ids).order_by('date')
    for adj in adjustments:
        price_histories[adj.item_id].append((adj.date, adj.new_price))

    data = []
    for t in transacts:
        # Build remarks column
        remarks = f"Original Price {t.item.price}."
        if price_histories[t.item.id]:
            for date, new_price in price_histories[t.item.id]:
                remarks += f" Updated on {date.strftime('%b %d %Y')} to {new_price}."

        data.append({
            'DATE': t.date.strftime('%Y-%m-%d'),
            'COMPANY': t.company_name,
            'SI NO': t.si_no,
            'LOCATION': t.location_name,
            'CREATED BY': t.creator_name,
            'ITEM': t.item.name,
            'UNIT': t.item.unit.name,
            'PACKS PER UNIT': t.num_per_unit,
            'WEIGHT': t.weight,
            'CONVERT TO KILOS': t.convert_to_kilos,
            'QUANTITY': t.quantity,
            'DELIVERED IN KILOS': t.delivered_in_kilos,
            'PRICE POSTED': float(t.price_posted),
            'REMARKS': remarks
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"transact_detail_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})


@login_required
def ajx_export_filtered_transact_detail_list(request):

    search_value = request.GET.get('search[value]', '')

    # Subquery to get the most recent price adjustment before or on the transaction date
    latest_price_adjustment = ItemPriceAdjustment.objects.filter(
        item=OuterRef('item'),
        date__lte=OuterRef('transact_header__date')
    ).order_by('-date').values('new_price')[:1]

    transacts = TransactDetail.objects.select_related(
        'transact_header__creator',
        'transact_header__company',
        'transact_header__location',
        'item'
    ).annotate(
        transact_id=F('transact_header__id'),
        si_no=F('transact_header__si_no'),
        company_name=F('transact_header__company__name'),
        date=F('transact_header__date'),
        creator_name=Concat(F('transact_header__creator__user__first_name'), Value(
            ' '), F('transact_header__creator__user__last_name')),
        location_name=F('transact_header__location__name'),
        num_per_unit=Coalesce(F('item__num_per_unit'), 0),
        weight=Coalesce(F('item__weight'), Decimal('0.0')),
        convert_to_kilos=ExpressionWrapper(
            F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        delivered_in_kilos=ExpressionWrapper(
            F('quantity') * F('item__num_per_unit') * F('item__weight'),
            output_field=DecimalField()
        ),
        price_posted=Coalesce(Subquery(
            latest_price_adjustment, output_field=DecimalField()), F('item__price'))
    )

    if search_value:
        transacts = transacts.filter(
            Q(transact_header__si_no__icontains=search_value) |
            Q(transact_header__company__name__icontains=search_value) |
            Q(transact_header__location__name__icontains=search_value) |
            Q(item__name__icontains=search_value)
        ).distinct()

    # date range filter
    if request.GET.get('minDate'):
        min_date = request.GET['minDate']
        transacts = transacts.filter(date__gte=min_date)

    if request.GET.get('maxDate'):
        max_date = request.GET['maxDate']
        transacts = transacts.filter(date__lte=max_date)

    # Sorting Fix
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'transact_id')

    column_map = {
        'transact_id': 'transact_id',
        'si_no': 'si_no',
        'company': 'company_name',
        'date': 'date',
        'creator': 'creator_name',
        'location': 'location_name',
        'item': 'item__name',
        'num_per_unit': 'num_per_unit',
        'weight': 'weight',
        'convert_to_kilos': 'convert_to_kilos',
        'quantity': 'quantity',
        'delivered_in_kilos': 'delivered_in_kilos',
        'price_posted': 'price_posted',
    }

    order_column = column_map.get(order_column, 'transact_id')

    if order_direction == 'desc':
        transacts = transacts.order_by(F(order_column).desc(nulls_last=True))
    else:
        transacts = transacts.order_by(F(order_column).asc(nulls_last=True))

    # Fetch price adjustment history for each item
    item_ids = {t.item.id for t in transacts}
    price_histories = {item_id: [] for item_id in item_ids}

    adjustments = ItemPriceAdjustment.objects.filter(
        item_id__in=item_ids).order_by('date')
    for adj in adjustments:
        price_histories[adj.item_id].append((adj.date, adj.new_price))

    data = []
    for t in transacts:
        # Build remarks column
        remarks = f"Original Price {t.item.price}."
        if price_histories[t.item.id]:
            for date, new_price in price_histories[t.item.id]:
                remarks += f" Updated on {date.strftime('%b %d %Y')} to {new_price}."

        data.append({
            'DATE': t.date.strftime('%Y-%m-%d'),
            'COMPANY': t.company_name,
            'SI NO': t.si_no,
            'LOCATION': t.location_name,
            'CREATED BY': t.creator_name,
            'ITEM': t.item.name,
            'UNIT': t.item.unit.name,
            'PACKS PER UNIT': t.num_per_unit,
            'WEIGHT': t.weight,
            'CONVERT TO KILOS': t.convert_to_kilos,
            'QUANTITY': t.quantity,
            'DELIVERED IN KILOS': t.delivered_in_kilos,
            'PRICE POSTED': float(t.price_posted),
            'REMARKS': remarks
        })

    # Create a Pandas DataFrame
    df = pd.DataFrame(data)

    # Generate the Excel file
    filename = f"filtered_transact_detail_records_{
        timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(os.path.join('media', filename), index=False)

    return JsonResponse({'filename': filename, 'status': 'success'})
