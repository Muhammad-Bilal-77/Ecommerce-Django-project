from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product, Category
from cart.models import Cart, CartItem
from .models import WishlistItem

class WishlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer', email='cust@example.com', password='Password123')
        self.category = Category.objects.create(name='Tech', description='Gadgets')
        self.product1 = Product.objects.create(
            category=self.category,
            name='Smart Watch',
            description='Wearable tech',
            price=199.99,
            stock=10
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='Wireless Buds',
            description='Audio tech',
            price=99.99,
            stock=0
        )
        
        self.wishlist_url = reverse('wishlist_detail')
        self.add_url = lambda pid: reverse('add_to_wishlist', args=[pid])
        self.remove_url = lambda wid: reverse('remove_from_wishlist', args=[wid])
        self.move_to_cart_url = lambda wid: reverse('move_to_cart', args=[wid])

    def test_wishlist_access_anonymous(self):
        # Accessing wishlist requires login
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_add_to_wishlist(self):
        self.client.login(username='customer', password='Password123')
        response = self.client.get(self.add_url(self.product1.id))
        
        # Verify redirect
        self.assertEqual(response.status_code, 302)
        
        # Verify item added
        self.assertTrue(WishlistItem.objects.filter(user=self.user, product=self.product1).exists())

        # Adding same item again does not create duplicate (unique constraint check)
        response = self.client.get(self.add_url(self.product1.id))
        self.assertEqual(WishlistItem.objects.filter(user=self.user, product=self.product1).count(), 1)

    def test_remove_from_wishlist(self):
        self.client.login(username='customer', password='Password123')
        item = WishlistItem.objects.create(user=self.user, product=self.product1)
        
        response = self.client.get(self.remove_url(item.id))
        self.assertRedirects(response, self.wishlist_url)
        self.assertFalse(WishlistItem.objects.filter(id=item.id).exists())

    def test_wishlist_detail_view(self):
        self.client.login(username='customer', password='Password123')
        WishlistItem.objects.create(user=self.user, product=self.product1)
        
        response = self.client.get(self.wishlist_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Smart Watch')
        self.assertContains(response, '$199.99')

    def test_move_to_cart_success(self):
        self.client.login(username='customer', password='Password123')
        item = WishlistItem.objects.create(user=self.user, product=self.product1)
        
        response = self.client.get(self.move_to_cart_url(item.id))
        
        # Should redirect to view_cart
        self.assertRedirects(response, reverse('view_cart'))
        
        # Verify removed from wishlist
        self.assertFalse(WishlistItem.objects.filter(id=item.id).exists())
        
        # Verify added to cart
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(CartItem.objects.filter(cart=cart, product=self.product1).exists())

    def test_move_to_cart_out_of_stock_fails(self):
        self.client.login(username='customer', password='Password123')
        item = WishlistItem.objects.create(user=self.user, product=self.product2) # stock is 0
        
        response = self.client.get(self.move_to_cart_url(item.id))
        
        # Should redirect back to wishlist_detail
        self.assertRedirects(response, self.wishlist_url)
        
        # Verify NOT removed from wishlist
        self.assertTrue(WishlistItem.objects.filter(id=item.id).exists())
        
        # Verify NOT added to cart
        self.assertFalse(CartItem.objects.filter(product=self.product2).exists())
