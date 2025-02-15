from django.urls import path
from transacts.views import TransactCreateView, TransactUpdateView, TransactListView, TransactDetailView, ajx_transact_list

app_name = 'transacts'

urlpatterns = [

    path('create/', TransactCreateView.as_view(), name='transact-create'),
    path('<int:pk>/update/', TransactUpdateView.as_view(), name='transact-update'),
    path('<int:pk>/', TransactDetailView.as_view(), name='transact-detail'),
    path('ajx_transact_list/', ajx_transact_list, name='ajx_transact_list'),
    path('', TransactListView.as_view(), name='transact-list'),
]
