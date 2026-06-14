from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Cart, CartItem

class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='Password123')
        
        self.cat = Category.objects.create(name='Electronics', description='Gadgets')
        self.prod1 = Product.objects.create(
            category=self.cat,
            name='Smartphone',
            description='Sleek 5G phone',
            price=699.99,
            stock=5
        )
        self.prod2 = Product.objects.create(
            category=self.cat,
            name='Adapter',
            description='Fast USB-C charger',
            price=29.99,
            stock=10
        )
        
        self.view_cart_url = reverse('view_cart')
        self.add_to_cart_url = lambda pid: reverse('add_to_cart', args=[pid])
        self.remove_from_cart_url = lambda iid: reverse('remove_from_cart', args=[iid])
        self.update_cart_url = lambda iid: reverse('update_cart', args=[iid])

    def test_view_cart_anonymous_redirect(self):
        response = self.client.get(self.view_cart_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_view_empty_cart(self):
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.view_cart_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Cart is Empty')

    def test_add_to_cart_success(self):
        self.client.login(username='buyer', password='Password123')
        # Add product 1
        response = self.client.get(self.add_to_cart_url(self.prod1.id))
        self.assertRedirects(response, self.view_cart_url)
        
        # Verify cart and item exist
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        item = cart.items.first()
        self.assertEqual(item.product, self.prod1)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(float(cart.total_price), 699.99)

    def test_add_multiple_to_cart_quantity_increase(self):
        self.client.login(username='buyer', password='Password123')
        # Add product 1 twice
        self.client.get(self.add_to_cart_url(self.prod1.id))
        self.client.get(self.add_to_cart_url(self.prod1.id))
        
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)
        self.assertEqual(float(cart.total_price), 1399.98)

    def test_add_to_cart_out_of_stock_warning(self):
        self.client.login(username='buyer', password='Password123')
        # Empty stock
        self.prod1.stock = 0
        self.prod1.save()
        
        response = self.client.get(self.add_to_cart_url(self.prod1.id))
        self.assertRedirects(response, reverse('product_detail', args=[self.prod1.id]))
        self.assertFalse(CartItem.objects.filter(product=self.prod1).exists())

    def test_add_to_cart_exceed_stock_warning(self):
        self.client.login(username='buyer', password='Password123')
        # Product 1 only has stock=5. Add 6 times
        for _ in range(5):
            self.client.get(self.add_to_cart_url(self.prod1.id))
        
        # 6th attempt
        response = self.client.get(self.add_to_cart_url(self.prod1.id))
        self.assertRedirects(response, reverse('product_detail', args=[self.prod1.id]))
        item = CartItem.objects.get(product=self.prod1)
        self.assertEqual(item.quantity, 5) # Capped at 5

    def test_remove_from_cart(self):
        self.client.login(username='buyer', password='Password123')
        self.client.get(self.add_to_cart_url(self.prod1.id))
        item = CartItem.objects.get(product=self.prod1)
        
        response = self.client.get(self.remove_from_cart_url(item.id))
        self.assertRedirects(response, self.view_cart_url)
        self.assertFalse(CartItem.objects.filter(product=self.prod1).exists())

    def test_update_quantity_success(self):
        self.client.login(username='buyer', password='Password123')
        self.client.get(self.add_to_cart_url(self.prod1.id))
        item = CartItem.objects.get(product=self.prod1)
        
        # Update quantity to 4
        response = self.client.post(self.update_cart_url(item.id), {'quantity': 4})
        self.assertRedirects(response, self.view_cart_url)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

    def test_update_quantity_exceed_stock_warning(self):
        self.client.login(username='buyer', password='Password123')
        self.client.get(self.add_to_cart_url(self.prod1.id))
        item = CartItem.objects.get(product=self.prod1)
        
        # Update quantity to 6 (exceeds stock=5)
        response = self.client.post(self.update_cart_url(item.id), {'quantity': 6})
        self.assertRedirects(response, self.view_cart_url)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1) # Unchanged

    def test_update_quantity_zero_removes_item(self):
        self.client.login(username='buyer', password='Password123')
        self.client.get(self.add_to_cart_url(self.prod1.id))
        item = CartItem.objects.get(product=self.prod1)
        
        # Update quantity to 0
        response = self.client.post(self.update_cart_url(item.id), {'quantity': 0})
        self.assertRedirects(response, self.view_cart_url)
        self.assertFalse(CartItem.objects.filter(product=self.prod1).exists())
