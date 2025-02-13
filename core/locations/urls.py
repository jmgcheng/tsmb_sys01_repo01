from django.urls import path
from locations.views import LocationListView, LocationCreateView, LocationDetailView, LocationUpdateView, ajx_location_list


app_name = 'locations'

urlpatterns = [
    path('create/', LocationCreateView.as_view(), name='location-create'),
    path('<int:pk>/', LocationDetailView.as_view(), name='location-detail'),
    path('<int:pk>/update/', LocationUpdateView.as_view(), name='location-update'),

    path('ajx_location_list/', ajx_location_list, name='ajx_location_list'),

    path('', LocationListView.as_view(), name='location-list'),

]
