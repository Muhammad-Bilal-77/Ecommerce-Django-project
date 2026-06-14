from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.all_products, name='all_products'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('collections/<int:collection_id>/', views.collection_products, name='collection_products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),     
    path('upload_product/', views.upload_product, name='upload_product'),
    path('edit_product/<int:id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:id>/', views.delete_product, name='delete_product'),
]