from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product, Category
from orders.models import Order
from decimal import Decimal

class DashboardTests(TestCase):
    def setUp(self):
        # Create regular user
        self.user = User.objects.create_user(username='buyer', email='buyer@example.com', password='Password123')
        # Create staff user
        self.staff_user = User.objects.create_user(username='admin', email='admin@example.com', password='Password123', is_staff=True)
        
        # Setup categories and products
        self.cat = Category.objects.create(name='Tech', description='Gadgets')
        self.prod = Product.objects.create(
            category=self.cat,
            name='Laptop',
            description='Thin and light',
            price=999.99,
            stock=10
        )
        
        # Setup orders
        self.order = Order.objects.create(
            user=self.user,
            shipping_address='123 Main St',
            phone_number='+1234567890',
            total_price=999.99,
            status='Pending'
        )

        self.dashboard_url = reverse('admin_dashboard')
        self.products_url = reverse('dashboard_products')
        self.add_product_url = reverse('dashboard_add_product')
        self.edit_product_url = lambda pid: reverse('dashboard_edit_product', args=[pid])
        self.delete_product_url = lambda pid: reverse('dashboard_delete_product', args=[pid])
        self.add_category_url = reverse('dashboard_add_category')
        self.delete_category_url = lambda cid: reverse('dashboard_delete_category', args=[cid])
        self.orders_url = reverse('dashboard_orders')
        self.update_order_status_url = lambda oid: reverse('dashboard_update_order_status', args=[oid])
        self.users_url = reverse('dashboard_users')

    def test_dashboard_access_restrictions(self):
        # Anonymous redirects to login
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        
        # Non-staff redirects to login
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Staff has access
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_dashboard_statistics(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_users'], 2)
        self.assertEqual(response.context['total_orders'], 1)
        self.assertEqual(float(response.context['total_revenue']), 999.99)
        self.assertEqual(response.context['total_products'], 1)

    def test_dashboard_products_list(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.products_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laptop')
        self.assertContains(response, 'Tech')

    def test_dashboard_add_product_success(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.add_product_url, {
            'name': 'Mouse',
            'description': 'RGB Mouse',
            'price': 19.99,
            'stock': 15,
            'category_id': self.cat.id
        })
        self.assertRedirects(response, self.products_url)
        self.assertTrue(Product.objects.filter(name='Mouse').exists())

    def test_dashboard_edit_product_success(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.edit_product_url(self.prod.id), {
            'name': 'Laptop Pro',
            'description': 'Pro version',
            'price': 1299.99,
            'stock': 5,
            'category_id': self.cat.id
        })
        self.assertRedirects(response, self.products_url)
        self.prod.refresh_from_db()
        self.assertEqual(self.prod.name, 'Laptop Pro')
        self.assertEqual(float(self.prod.price), 1299.99)

    def test_dashboard_delete_product(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.delete_product_url(self.prod.id))
        self.assertRedirects(response, self.products_url)
        self.assertFalse(Product.objects.filter(id=self.prod.id).exists())

    def test_dashboard_add_category(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.add_category_url, {
            'name': 'Home Appliances',
            'description': 'Household items'
        })
        self.assertRedirects(response, self.products_url)
        self.assertTrue(Category.objects.filter(name='Home Appliances').exists())

    def test_dashboard_delete_category_with_products_fails(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.delete_category_url(self.cat.id))
        self.assertRedirects(response, self.products_url)
        # Category should still exist since it has a product
        self.assertTrue(Category.objects.filter(id=self.cat.id).exists())

    def test_dashboard_delete_category_without_products_succeeds(self):
        self.client.login(username='admin', password='Password123')
        new_cat = Category.objects.create(name='Empty', description='Nothing')
        response = self.client.post(self.delete_category_url(new_cat.id))
        self.assertRedirects(response, self.products_url)
        self.assertFalse(Category.objects.filter(id=new_cat.id).exists())

    def test_dashboard_orders_list_and_update(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '#1')
        
        # Update order status to Shipped
        response = self.client.post(self.update_order_status_url(self.order.id), {
            'status': 'Shipped'
        })
        self.assertRedirects(response, self.orders_url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Shipped')

    def test_dashboard_users_list_search_and_actions(self):
        self.client.login(username='admin', password='Password123')
        
        # Verify both users show up
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user, response.context['users'])
        self.assertIn(self.staff_user, response.context['users'])
        
        # Search
        response = self.client.get(self.users_url, {'q': 'buyer'})
        self.assertIn(self.user, response.context['users'])
        self.assertNotIn(self.staff_user, response.context['users'])

        # Toggle staff role of buyer
        response = self.client.post(self.users_url, {
            'user_id': self.user.id,
            'action': 'toggle_staff'
        })
        self.assertRedirects(response, self.users_url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)

        # Delete user
        response = self.client.post(self.users_url, {
            'user_id': self.user.id,
            'action': 'delete_user'
        })
        self.assertRedirects(response, self.users_url)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_dashboard_add_product_with_new_collection(self):
        from products.models import FeaturedCollection
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.add_product_url, {
            'name': 'Watch Pro',
            'description': 'Description',
            'price': 299.99,
            'stock': 10,
            'category_id': self.cat.id,
            'new_collection_name': 'Cyber Monday'
        })
        self.assertRedirects(response, self.products_url)
        # Check that the collection was created
        collection = FeaturedCollection.objects.get(name='Cyber Monday')
        self.assertTrue(Product.objects.filter(name='Watch Pro', featured_collection=collection).exists())

    def test_dashboard_edit_product_change_collection(self):
        from products.models import FeaturedCollection
        col1 = FeaturedCollection.objects.create(name='Col 1')
        col2 = FeaturedCollection.objects.create(name='Col 2')
        product = Product.objects.create(
            category=self.cat,
            name='Gadget A',
            description='Desc',
            price=99.99,
            stock=100,
            featured_collection=col1
        )
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.edit_product_url(product.id), {
            'name': 'Gadget A',
            'description': 'Desc',
            'price': 99.99,
            'stock': 100,
            'category_id': self.cat.id,
            'featured_collection_id': col2.id
        })
        self.assertRedirects(response, self.products_url)
        product.refresh_from_db()
        self.assertEqual(product.featured_collection, col2)

