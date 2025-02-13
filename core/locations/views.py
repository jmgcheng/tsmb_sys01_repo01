from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required, login_required
from django.db.models import Q, Count, F, Case, When, IntegerField, Value, Prefetch, TextField
from django.db.models.functions import Coalesce
from locations.models import Location
from locations.forms import LocationForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'locations/location_list.html'


class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('locations:location-list')


class LocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = 'locations/location_detail.html'


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('locations:location-list')

    def form_valid(self, form):
        #
        messages.success(self.request, 'Location updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        #
        messages.warning(self.request, 'Please check errors below')
        return super().form_invalid(form)


@login_required
def ajx_location_list(request):

    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    #
    locations = Location.objects.all()

    if search_value:
        locations = locations.filter(
            Q(name__icontains=search_value) |
            Q(address__icontains=search_value)
        ).distinct()

    # Handle ordering
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')
    order_column = request.GET.get(
        f'columns[{order_column_index}][data]', 'id')

    # print(f'----------------hermit1------------------')
    # print(order_column)
    # print(f'----------------hermit1------------------')

    if order_direction == 'desc':
        order_column = f'-{order_column}'
    locations = locations.order_by(order_column)

    paginator = Paginator(locations, length)
    total_records = paginator.count
    locations_page = paginator.get_page(start // length + 1)

    #
    data = []

    for l in locations_page:
        data.append({
            'name': f"<a href='/locations/{l.id}/'>{l.name}</a>",
            'address': l.address,
        })

    response = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    }

    return JsonResponse(response)
