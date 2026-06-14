from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('products/', views.dashboard_products, name='dashboard_products'),
    path('products/add/', views.dashboard_add_product, name='dashboard_add_product'),
    path('products/edit/<int:id>/', views.dashboard_edit_product, name='dashboard_edit_product'),
    path('products/delete/<int:id>/', views.dashboard_delete_product, name='dashboard_delete_product'),
    path('categories/add/', views.dashboard_add_category, name='dashboard_add_category'),
    path('categories/delete/<int:id>/', views.dashboard_delete_category, name='dashboard_delete_category'),
    path('orders/', views.dashboard_orders, name='dashboard_orders'),
    path('orders/update-status/<int:id>/', views.dashboard_update_order_status, name='dashboard_update_order_status'),
    path('users/', views.dashboard_users, name='dashboard_users'),
]
