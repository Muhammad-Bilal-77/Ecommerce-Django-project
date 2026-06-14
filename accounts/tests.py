from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class AccountsRedirectTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username='buyer', email='buyer@example.com', password='Password123')
        self.admin = User.objects.create_user(username='admin', email='admin@example.com', password='Password123', is_staff=True)
        self.login_url = reverse('login')
        self.register_url = reverse('register')
        self.dashboard_url = reverse('dashboard')
        self.admin_dashboard_url = reverse('admin_dashboard')

    def test_buyer_login_redirects_to_customer_dashboard(self):
        response = self.client.post(self.login_url, {
            'username': 'buyer',
            'password': 'Password123'
        })
        self.assertRedirects(response, self.dashboard_url)

    def test_admin_login_redirects_to_admin_dashboard(self):
        response = self.client.post(self.login_url, {
            'username': 'admin',
            'password': 'Password123'
        })
        self.assertRedirects(response, self.admin_dashboard_url)

    def test_logged_in_buyer_access_login_redirects_to_customer_dashboard(self):
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_logged_in_admin_access_login_redirects_to_admin_dashboard(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.admin_dashboard_url)

    def test_logged_in_buyer_access_register_redirects_to_customer_dashboard(self):
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_logged_in_admin_access_register_redirects_to_admin_dashboard(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.admin_dashboard_url)

    def test_logged_in_admin_access_customer_dashboard_redirects_to_admin_dashboard(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(response, self.admin_dashboard_url)

    def test_logged_in_buyer_access_customer_dashboard_status_200(self):
        self.client.login(username='buyer', password='Password123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
