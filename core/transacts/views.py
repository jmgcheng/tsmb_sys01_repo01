from django.shortcuts import redirect, render
# from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Prefetch
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.template.loader import get_template
from django.urls import reverse_lazy
from transacts.models import TransactStatus, TransactHeader, TransactDetail
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
        form.instance.status = TransactStatus.objects.get(
            name='FILED')

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

        # Fetch TransactDetails for the current header
        context['details'] = TransactDetail.objects.filter(
            transact_header=self.object)

        return context


class TransactListView(LoginRequiredMixin, ListView):
    model = TransactHeader
    template_name = 'transacts/transact_list.html'


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
