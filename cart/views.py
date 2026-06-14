from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from products.models import Product
from .models import Cart, CartItem

@login_required(login_url='login')
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/cart.html', {
        'cart': cart,
        'active_tab': 'cart'
    })

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.warning(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect('product_detail', id=product.id)

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        if cart_item.quantity + 1 > product.stock:
            messages.warning(request, f"Cannot add more. Only {product.stock} units of '{product.name}' are in stock.")
            return redirect('product_detail', id=product.id)
        else:
            try:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Increased quantity of '{product.name}' in your cart.")
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
    else:
        try:
            cart_item.quantity = 1
            cart_item.save()
            messages.success(request, f"Added '{product.name}' to your cart.")
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))

    return redirect('view_cart')

@login_required(login_url='login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f"Removed '{product_name}' from your cart.")
    return redirect('view_cart')

@login_required(login_url='login')
def update_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                # If quantity is set to 0 or negative, remove the item
                product_name = cart_item.product.name
                cart_item.delete()
                messages.success(request, f"Removed '{product_name}' from your cart.")
            elif quantity > cart_item.product.stock:
                messages.warning(request, f"Could not update quantity. Only {cart_item.product.stock} units are in stock.")
            else:
                try:
                    cart_item.quantity = quantity
                    cart_item.save()
                    messages.success(request, f"Updated quantity of '{cart_item.product.name}'.")
                except ValidationError as e:
                    messages.error(request, " ".join(e.messages))
        except ValueError:
            messages.error(request, "Invalid quantity value.")

    return redirect('view_cart')
