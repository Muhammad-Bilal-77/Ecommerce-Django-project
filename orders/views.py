from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import ValidationError
from cart.models import Cart
from .models import Order, OrderItem

@login_required(login_url='login')
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('all_products')

    errors = {}
    values = {}

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()

        values = {
            'shipping_address': shipping_address,
            'phone_number': phone_number
        }

        if not shipping_address:
            errors['shipping_address'] = "Shipping address is required."
        if not phone_number:
            errors['phone_number'] = "Phone number is required."

        # Double check stock availability
        for item in cart.items.all():
            if item.quantity > item.product.stock:
                errors['stock'] = f"Sorry, only {item.product.stock} units of '{item.product.name}' are available. Please update your cart."
                messages.error(request, errors['stock'])
                return redirect('view_cart')

        if not errors:
            # Enforce atomic transaction to prevent database inconsistency
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        shipping_address=shipping_address,
                        phone_number=phone_number,
                        total_price=cart.total_price
                    )

                    for item in cart.items.all():
                        # Create OrderItem
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            price=item.product.price,
                            quantity=item.quantity
                        )
                        # Deduct stock
                        item.product.stock -= item.quantity
                        item.product.save()

                    # Clear cart items
                    cart.items.all().delete()

                messages.success(request, f"Order #{order.id} placed successfully!")
                return redirect('my_orders')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, error_list in e.message_dict.items():
                        errors[field] = " ".join(error_list)
                else:
                    errors['non_field_errors'] = " ".join(e.messages)

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'errors': errors,
        'values': values
    })

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'active_tab': 'orders'
    })

@login_required(login_url='login')
def order_detail(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'active_tab': 'orders'
    })

@login_required(login_url='login')
def cancel_order(request, id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=id, user=request.user)
        if order.status == 'Pending':
            order.cancel()
            messages.success(request, f"Order #{order.id} has been successfully cancelled.")
        else:
            messages.error(request, "Only pending orders can be cancelled.")
    return redirect('order_detail', id=id)
