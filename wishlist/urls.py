from django.urls import path
from . import views

urlpatterns = [
    path('', views.wishlist_detail, name='wishlist_detail'),
    path('add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('move-to-cart/<int:wishlist_id>/', views.move_to_cart, name='move_to_cart'),
]
