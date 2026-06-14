from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from products.models import Product
from cart.models import Cart, CartItem
from .models import WishlistItem

@login_required(login_url='login')
def wishlist_detail(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'wishlist/wishlist.html', {
        'wishlist_items': wishlist_items,
        'active_tab': 'wishlist'
    })

@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, f"Added '{product.name}' to your wishlist.")
    else:
        messages.info(request, f"'{product.name}' is already in your wishlist.")

    next_url = request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('all_products')

@login_required(login_url='login')
def remove_from_wishlist(request, wishlist_id):
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_id, user=request.user)
    product_name = wishlist_item.product.name
    wishlist_item.delete()
    messages.success(request, f"Removed '{product_name}' from your wishlist.")
    return redirect('wishlist_detail')

@login_required(login_url='login')
def move_to_cart(request, wishlist_id):
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_id, user=request.user)
    product = wishlist_item.product

    if product.stock <= 0:
        messages.warning(request, f"Sorry, '{product.name}' is currently out of stock and cannot be moved to cart.")
        return redirect('wishlist_detail')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        if cart_item.quantity + 1 > product.stock:
            messages.warning(request, f"Cannot add more. Only {product.stock} units of '{product.name}' are in stock.")
            return redirect('wishlist_detail')
        else:
            try:
                cart_item.quantity += 1
                cart_item.save()
                wishlist_item.delete()
                messages.success(request, f"Moved '{product.name}' to your cart.")
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
    else:
        try:
            cart_item.quantity = 1
            cart_item.save()
            wishlist_item.delete()
            messages.success(request, f"Moved '{product.name}' to your cart.")
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))

    return redirect('view_cart')
