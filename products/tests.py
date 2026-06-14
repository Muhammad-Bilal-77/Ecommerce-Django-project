from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product

class ProductsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', email='admin@example.com', password='Password123', is_staff=True)
        self.regular_user = User.objects.create_user(username='customer', email='customer@example.com', password='Password123')
        
        self.cat1 = Category.objects.create(name='Computers', description='Desktop and laptop computers')
        self.cat2 = Category.objects.create(name='Accessories', description='Computer accessories')
        
        self.prod1 = Product.objects.create(
            category=self.cat1,
            name='Super Gaming Laptop',
            description='High performance laptop with advanced GPU',
            price=1499.99,
            stock=10
        )
        self.prod2 = Product.objects.create(
            category=self.cat2,
            name='Wireless Mouse',
            description='Ergonomic wireless mouse with DPI controls',
            price=49.99,
            stock=50
        )
        
        self.home_url = reverse('home')
        self.all_products_url = reverse('all_products')
        self.upload_product_url = reverse('upload_product')

    def test_storefront_home_page(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Computers')
        self.assertContains(response, 'Super Gaming Laptop')

    def test_catalog_all_products(self):
        response = self.client.get(self.all_products_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Gaming Laptop')
        self.assertContains(response, 'Wireless Mouse')

    def test_catalog_search(self):
        # Search for laptop
        response = self.client.get(self.all_products_url, {'q': 'Laptop'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Gaming Laptop')
        self.assertNotContains(response, 'Wireless Mouse')

    def test_catalog_category_filter(self):
        # Filter by Accessories
        response = self.client.get(self.all_products_url, {'category': self.cat2.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wireless Mouse')
        self.assertNotContains(response, 'Super Gaming Laptop')

    def test_product_detail_page(self):
        url = reverse('product_detail', args=[self.prod1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Gaming Laptop')
        self.assertContains(response, '$1499.99')

    def test_category_products_page(self):
        url = reverse('category_products', args=[self.cat1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Gaming Laptop')
        self.assertNotContains(response, 'Wireless Mouse')

    def test_upload_product_auth_check(self):
        # Try uploading without logging in -> redirects to login page
        response = self.client.post(self.upload_product_url, {
            'name': 'New Tech Item',
            'description': 'Description',
            'price': 100.0,
            'stock': 5,
            'category_id': self.cat1.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_upload_product_success(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.upload_product_url, {
            'name': 'Super Mechanical Keyboard',
            'description': 'RGB backlight mechanical switches',
            'price': 129.99,
            'stock': 20,
            'category_id': self.cat2.id
        })
        self.assertRedirects(response, self.all_products_url)
        self.assertTrue(Product.objects.filter(name='Super Mechanical Keyboard').exists())

    def test_upload_product_create_new_category(self):
        self.client.login(username='admin', password='Password123')
        response = self.client.post(self.upload_product_url, {
            'name': 'Virtual Reality Headset',
            'description': 'Next-gen virtual reality headset',
            'price': 599.99,
            'stock': 8,
            'new_category_name': 'Virtual Reality'
        })
        self.assertRedirects(response, self.all_products_url)
        # Check that Category was created and Product is associated
        category = Category.objects.get(name='Virtual Reality')
        self.assertTrue(Product.objects.filter(name='Virtual Reality Headset', category=category).exists())

    def test_edit_product_success(self):
        self.client.login(username='admin', password='Password123')
        url = reverse('edit_product', args=[self.prod1.id])
        response = self.client.post(url, {
            'name': 'Super Gaming Laptop v2',
            'description': 'Updated description',
            'price': 1599.99,
            'stock': 5,
            'category_id': self.cat1.id
        })
        self.assertRedirects(response, reverse('product_detail', args=[self.prod1.id]))
        
        self.prod1.refresh_from_db()
        self.assertEqual(self.prod1.name, 'Super Gaming Laptop v2')
        self.assertEqual(float(self.prod1.price), 1599.99)
        self.assertEqual(self.prod1.stock, 5)

    def test_delete_product_success(self):
        self.client.login(username='admin', password='Password123')
        url = reverse('delete_product', args=[self.prod1.id])
        response = self.client.post(url)
        self.assertRedirects(response, self.all_products_url)
        self.assertFalse(Product.objects.filter(id=self.prod1.id).exists())

    def test_non_staff_denied_upload_product(self):
        self.client.login(username='customer', password='Password123')
        response = self.client.post(self.upload_product_url, {
            'name': 'New Tech Item',
            'description': 'Description',
            'price': 10.0,
            'stock': 5,
            'category_id': self.cat1.id
        })
        self.assertRedirects(response, reverse('home'))
        # Ensure no product was created
        self.assertFalse(Product.objects.filter(name='New Tech Item').exists())

    def test_non_staff_denied_edit_product(self):
        self.client.login(username='customer', password='Password123')
        url = reverse('edit_product', args=[self.prod1.id])
        response = self.client.post(url, {
            'name': 'Hacked Laptop Name',
            'description': 'Description',
            'price': 1.0,
            'stock': 1,
            'category_id': self.cat1.id
        })
        self.assertRedirects(response, reverse('home'))
        self.prod1.refresh_from_db()
        self.assertNotEqual(self.prod1.name, 'Hacked Laptop Name')

    def test_non_staff_denied_delete_product(self):
        self.client.login(username='customer', password='Password123')
        url = reverse('delete_product', args=[self.prod1.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(Product.objects.filter(id=self.prod1.id).exists())

    def test_featured_collection_creation_and_association(self):
        from .models import FeaturedCollection
        collection = FeaturedCollection.objects.create(name='Limited Edition', description='Premium drop')
        product = Product.objects.create(
            category=self.cat1,
            name='Exclusive Watch',
            description='Rare timepiece',
            price=2999.99,
            stock=2,
            featured_collection=collection
        )
        self.assertEqual(product.featured_collection, collection)
        self.assertIn(product, collection.products.all())

    def test_featured_collection_delete_nullifies_product_association(self):
        from .models import FeaturedCollection
        collection = FeaturedCollection.objects.create(name='Limited Edition', description='Premium drop')
        product = Product.objects.create(
            category=self.cat1,
            name='Exclusive Watch',
            description='Rare timepiece',
            price=2999.99,
            stock=2,
            featured_collection=collection
        )
        collection.delete()
        product.refresh_from_db()
        self.assertIsNone(product.featured_collection)
        # Ensure the product itself was not deleted
        self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_collection_products_page(self):
        from .models import FeaturedCollection
        collection = FeaturedCollection.objects.create(name='Limited Edition', description='Premium drop')
        product_in = Product.objects.create(
            category=self.cat1,
            name='Exclusive Watch',
            description='Rare timepiece',
            price=2999.99,
            stock=2,
            featured_collection=collection
        )
        product_out = Product.objects.create(
            category=self.cat1,
            name='Regular Laptop',
            description='Average laptop',
            price=999.99,
            stock=5
        )
        url = reverse('collection_products', args=[collection.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Exclusive Watch')
        self.assertNotContains(response, 'Regular Laptop')

    def test_featured_collection_fallback_image(self):
        from .models import FeaturedCollection
        collection = FeaturedCollection.objects.create(name='Empty Collection')
        # Without any image and without products, it should return the default Unsplash fallback
        self.assertIn('unsplash.com', collection.image_url)

        product = Product.objects.create(
            category=self.cat1,
            name='Watch',
            description='Rare timepiece',
            price=2999.99,
            stock=2,
            featured_collection=collection
        )
        self.assertIsNotNone(collection.image_url)

