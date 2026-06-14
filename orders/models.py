from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from decimal import Decimal
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.TextField()
    phone_number = models.CharField(validators=[phone_regex], max_length=20)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"

    def cancel(self):
        if self.status != 'Cancelled':
            from django.db import transaction
            with transaction.atomic():
                self.status = 'Cancelled'
                self.save()
                for item in self.items.all():
                    if item.product:
                        item.product.stock += item.quantity
                        item.product.save()


    def full_clean(self, *args, **kwargs):
        if self.total_price is not None and isinstance(self.total_price, (float, int, Decimal)):
            # Convert float to str first to preserve precision, if float
            if isinstance(self.total_price, (float, int)):
                self.total_price = Decimal(str(self.total_price))
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])  # Purchase price
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Order #{self.order.id})"

    def full_clean(self, *args, **kwargs):
        if self.price is not None and isinstance(self.price, (float, int)):
            self.price = Decimal(str(self.price))
        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.quantity * self.price
