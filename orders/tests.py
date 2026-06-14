from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem

class OrdersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='Password123')
        
        self.cat = Category.objects.create(name='Computing', description='Parts')
        self.prod = Product.objects.create(
            category=self.cat,
            name='Intel Processor',
            description='Core i7 CPU',
            price=299.99,
            stock=5
        )
        
        self.checkout_url = reverse('checkout')
        self.my_orders_url = reverse('my_orders')
        self.order_detail_url = lambda oid: reverse('order_detail', args=[oid])

    def test_checkout_anonymous_redirect(self):
        response = self.client.get(self.checkout_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_checkout_empty_cart_redirect(self):
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.checkout_url)
        self.assertRedirects(response, reverse('all_products'))

    def test_place_order_success(self):
        self.client.login(username='buyer', password='Password123')
        
        # Populate cart first
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.prod, quantity=2)
        
        # Post shipping details
        response = self.client.post(self.checkout_url, {
            'shipping_address': '123 Tech Avenue, Silicon Valley',
            'phone_number': '+19876543210'
        })
        
        # Verify redirect to order history
        self.assertRedirects(response, self.my_orders_url)
        
        # Check Order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.shipping_address, '123 Tech Avenue, Silicon Valley')
        self.assertEqual(order.phone_number, '+19876543210')
        self.assertEqual(float(order.total_price), 599.98)
        self.assertEqual(order.status, 'Pending')
        
        # Check OrderItem was created
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.prod)
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(float(order_item.price), 299.99)
        
        # Check product stock level was decremented: 5 - 2 = 3
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 3)
        
        # Check cart is cleared
        self.assertFalse(cart.items.exists())

    def test_place_order_exceed_stock_fails(self):
        self.client.login(username='buyer', password='Password123')
        
        # Populate cart with quantity greater than stock (quantity=6 > stock=5)
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.prod, quantity=6)
        
        response = self.client.post(self.checkout_url, {
            'shipping_address': '123 Tech Avenue',
            'phone_number': '+19876543210'
        })
        
        # Verify it redirects to cart page due to stock warning
        self.assertRedirects(response, reverse('view_cart'))
        self.assertEqual(Order.objects.count(), 0)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 5) # Unchanged

    def test_my_orders_listing(self):
        self.client.login(username='buyer', password='Password123')
        order = Order.objects.create(
            user=self.user,
            shipping_address='Street',
            phone_number='+19876543210',
            total_price=100.00
        )
        response = self.client.get(self.my_orders_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Order #{order.id}")

    def test_order_detail_tracking(self):
        self.client.login(username='buyer', password='Password123')
        order = Order.objects.create(
            user=self.user,
            shipping_address='Street Info',
            phone_number='+19876543210',
            total_price=100.00
        )
        OrderItem.objects.create(order=order, product=self.prod, price=100.00, quantity=1)
        
        # Check tracking timeline details
        response = self.client.get(self.order_detail_url(order.id))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Street Info')

    def test_place_order_invalid_phone_fails_gracefully(self):
        self.client.login(username='buyer', password='Password123')
        
        # Populate cart first
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.prod, quantity=2)
        
        # Post shipping details with invalid phone number
        response = self.client.post(self.checkout_url, {
            'shipping_address': '123 Tech Avenue, Silicon Valley',
            'phone_number': 'invalid-phone-format'
        })
        
        # Verify response is 200 (render checkout page with error) and not 500 or 302
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phone number must be entered in the format')
        
        # Verify no order was created
        self.assertEqual(Order.objects.count(), 0)

    def test_cancel_order_customer_success(self):
        self.client.login(username='buyer', password='Password123')
        # Create a pending order
        order = Order.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            phone_number='+19876543210',
            total_price=299.99,
            status='Pending'
        )
        OrderItem.objects.create(order=order, product=self.prod, price=299.99, quantity=2)
        # Verify stock was 5 (reset to 5 for test setup, or let's check current self.prod.stock)
        self.prod.stock = 5
        self.prod.save()

        # Send post request to cancel
        response = self.client.post(reverse('cancel_order', args=[order.id]))
        self.assertRedirects(response, reverse('order_detail', args=[order.id]))

        order.refresh_from_db()
        self.assertEqual(order.status, 'Cancelled')

        # Stock should be restored: 5 + 2 = 7
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 7)

    def test_cancel_order_customer_non_pending_fails(self):
        self.client.login(username='buyer', password='Password123')
        order = Order.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            phone_number='+19876543210',
            total_price=299.99,
            status='Shipped'
        )
        OrderItem.objects.create(order=order, product=self.prod, price=299.99, quantity=1)
        self.prod.stock = 5
        self.prod.save()

        # Try to cancel
        response = self.client.post(reverse('cancel_order', args=[order.id]))
        self.assertRedirects(response, reverse('order_detail', args=[order.id]))

        # Status should remain Shipped
        order.refresh_from_db()
        self.assertEqual(order.status, 'Shipped')

        # Stock should remain 5 (no restoration)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 5)

    def test_cancel_order_unauthorized(self):
        # Create a second user who owns the order
        other_user = User.objects.create_user(username='other', email='other@example.com', password='Password123')
        order = Order.objects.create(
            user=other_user,
            shipping_address='123 Test St',
            phone_number='+19876543210',
            total_price=299.99,
            status='Pending'
        )

        # Login as buyer (not owner)
        self.client.login(username='buyer', password='Password123')
        response = self.client.post(reverse('cancel_order', args=[order.id]))
        # Should return 404
        self.assertEqual(response.status_code, 404)

    def test_admin_cancel_order_success(self):
        # Create admin user
        admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='Password123', is_staff=True)
        self.client.login(username='admin', password='Password123')

        order = Order.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            phone_number='+19876543210',
            total_price=299.99,
            status='Pending'
        )
        OrderItem.objects.create(order=order, product=self.prod, price=299.99, quantity=2)
        self.prod.stock = 5
        self.prod.save()

        # Update order status to Cancelled via dashboard view
        response = self.client.post(reverse('dashboard_update_order_status', args=[order.id]), {
            'status': 'Cancelled'
        })
        self.assertRedirects(response, reverse('dashboard_orders'))

        order.refresh_from_db()
        self.assertEqual(order.status, 'Cancelled')

        # Stock restored
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.stock, 7)

    def test_admin_update_cancelled_order_fails(self):
        admin_user = User.objects.create_user(username='admin', email='admin@example.com', password='Password123', is_staff=True)
        self.client.login(username='admin', password='Password123')

        order = Order.objects.create(
            user=self.user,
            shipping_address='123 Test St',
            phone_number='+19876543210',
            total_price=299.99,
            status='Cancelled'
        )

        # Try to change status from Cancelled to Shipped
        response = self.client.post(reverse('dashboard_update_order_status', args=[order.id]), {
            'status': 'Shipped'
        })
        self.assertRedirects(response, reverse('dashboard_orders'))

        order.refresh_from_db()
        # Status must remain Cancelled
        self.assertEqual(order.status, 'Cancelled')

