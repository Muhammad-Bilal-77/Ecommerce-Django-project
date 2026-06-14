from django.contrib import admin
from .models import Category, Product, FeaturedCollection

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(FeaturedCollection)
