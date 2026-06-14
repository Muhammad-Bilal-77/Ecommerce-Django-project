from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('', views.my_orders, name='my_orders'),
    path('<int:id>/', views.order_detail, name='order_detail'),
    path('<int:id>/cancel/', views.cancel_order, name='cancel_order'),
]
