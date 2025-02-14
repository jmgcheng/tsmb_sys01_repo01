from django.urls import path

from items.views import ItemListView, ItemCreateView, ItemDetailView, ItemUpdateView, ajx_item_list, ajx_export_excel_all_items, ajx_export_excel_filtered_items, ajx_import_insert_excel_items_celery, ajx_import_update_excel_items_celery, ajx_tasks_status

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
    path('ajx_export_excel_all_items/', ajx_export_excel_all_items,
         name='ajx_export_excel_all_items'),
    path('ajx_export_excel_filtered_items/', ajx_export_excel_filtered_items,
         name='ajx_export_excel_filtered_items'),
    path('ajx_import_insert_excel_items_celery', ajx_import_insert_excel_items_celery,
         name='ajx_import_insert_excel_items_celery'),
    path('ajx_import_update_excel_items_celery', ajx_import_update_excel_items_celery,
         name='ajx_import_update_excel_items_celery'),
    path('ajx_tasks_status/<str:task_id>',
         ajx_tasks_status, name='ajx_tasks_status'),

    path('', ItemListView.as_view(), name='item-list'),
    # path('variations/', ProductVariationListView.as_view(),
    #      name='product-variation-list'),
]
