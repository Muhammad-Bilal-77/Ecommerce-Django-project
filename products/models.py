from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class FeaturedCollection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='collections/', blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        # Cover fallback: check first product with an image in this collection
        first_product = self.products.exclude(image='').first()
        if first_product and first_product.image:
            return first_product.image.url
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    featured_collection = models.ForeignKey(FeaturedCollection, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def full_clean(self, *args, **kwargs):
        if self.price is not None and isinstance(self.price, (float, int)):
            self.price = Decimal(str(self.price))
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        # Premium fallback placeholder photo for clean aesthetics
        return "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop"
