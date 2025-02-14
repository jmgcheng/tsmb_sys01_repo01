from django.urls import path

from items.views import ItemListView, ItemCreateView, ItemDetailView, ItemUpdateView, ItemPriceAdjustmentListView, ItemPriceAdjustmentCreateView, ItemPriceAdjustmentDetailView, ItemPriceAdjustmentUpdateView, ajx_item_list, ajx_item_price_adjustment_list, ajx_export_excel_all_items, ajx_export_excel_filtered_items, ajx_import_insert_excel_items_celery, ajx_import_update_excel_items_celery, ajx_tasks_status

app_name = 'items'

urlpatterns = [
    path('create/', ItemCreateView.as_view(), name='item-create'),
    path('price_adjustments/create/', ItemPriceAdjustmentCreateView.as_view(),
         name='item-price-adjustment-create'),

    path('<int:pk>/', ItemDetailView.as_view(), name='item-detail'),
    path('price_adjustments/<int:pk>/', ItemPriceAdjustmentDetailView.as_view(),
         name='item-price-adjustment-detail'),

    path('<int:pk>/update/', ItemUpdateView.as_view(), name='item-update'),
    path('price_adjustments/<int:pk>/update/',
         ItemPriceAdjustmentUpdateView.as_view(), name='item-price-adjustment-update'),

    path('ajx_item_list/', ajx_item_list, name='ajx_item_list'),
    path('ajx_item_price_adjustment_list/', ajx_item_price_adjustment_list,
         name='ajx_item_price_adjustment_list'),
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
    path('price_adjustments/', ItemPriceAdjustmentListView.as_view(),
         name='item-price-adjustment-list'),
]
