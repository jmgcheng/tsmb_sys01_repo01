from django.urls import path

from items.views import ItemListView, ItemCreateView, ItemDetailView, ItemUpdateView, ajx_item_list

app_name = 'items'

urlpatterns = [
    path('create/', ItemCreateView.as_view(), name='item-create'),
    # path('variations/create/', ProductVariationCreateView.as_view(),
    #      name='product-variation-create'),

    path('<int:pk>/', ItemDetailView.as_view(), name='item-detail'),
    # path('variations/<int:pk>/', ProductVariationDetailView.as_view(),
    #      name='product-variation-detail'),

    path('<int:pk>/update/', ItemUpdateView.as_view(), name='item-update'),
    # path('variations/<int:pk>/update/',
    #      ProductVariationUpdateView.as_view(), name='product-variation-update'),

    path('ajx_item_list/', ajx_item_list, name='ajx_item_list'),
    # path('variations/ajx_product_variation_list/',
    #      ajx_product_variation_list, name='ajx_product_variation_list'),

    path('', ItemListView.as_view(), name='item-list'),
    # path('variations/', ProductVariationListView.as_view(),
    #      name='product-variation-list'),
]
