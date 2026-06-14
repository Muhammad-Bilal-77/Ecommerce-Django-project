from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from decimal import Decimal
from products.models import Product, Category, FeaturedCollection
from orders.models import Order, OrderItem

# Decorator to restrict dashboard views to staff members
def staff_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='login'
    )
    return actual_decorator(view_func)

@staff_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    
    # Calculate total revenue
    revenue_result = Order.objects.aggregate(total=Sum('total_price'))
    total_revenue = revenue_result['total'] if revenue_result['total'] is not None else Decimal('0.00')
    
    total_products = Product.objects.count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Top products (by stock descending as a simple proxy)
    top_products = Product.objects.all().order_by('-created_at')[:4]
    
    return render(request, 'dashboard/dashboard.html', {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'active_tab': 'overview'
    })

@staff_required
def dashboard_products(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all().order_by('name')
    return render(request, 'dashboard/products.html', {
        'products': products,
        'categories': categories,
        'active_tab': 'products'
    })

@staff_required
def dashboard_add_product(request):
    categories = Category.objects.all().order_by('name')
    collections = FeaturedCollection.objects.all().order_by('name')
    errors = {}
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price_raw = request.POST.get('price', '').strip()
        stock_raw = request.POST.get('stock', '').strip()
        category_id = request.POST.get('category_id', '').strip()
        new_category_name = request.POST.get('new_category_name', '').strip()
        featured_collection_id = request.POST.get('featured_collection_id', '').strip()
        new_collection_name = request.POST.get('new_collection_name', '').strip()
        image = request.FILES.get('image')

        if not name:
            errors['name'] = "Product name is required."
        if not price_raw:
            errors['price'] = "Price is required."
        else:
            try:
                price = float(price_raw)
                if price < 0:
                    errors['price'] = "Price cannot be negative."
            except ValueError:
                errors['price'] = "Enter a valid price."

        if not stock_raw:
            errors['stock'] = "Stock is required."
        else:
            try:
                stock = int(stock_raw)
                if stock < 0:
                    errors['stock'] = "Stock cannot be negative."
            except ValueError:
                errors['stock'] = "Enter a valid integer stock."

        # Category logic
        category = None
        if new_category_name:
            category, created = Category.objects.get_or_create(
                name=new_category_name,
                defaults={'description': f"Category for {new_category_name}"}
            )
        elif category_id:
            try:
                category = Category.objects.get(id=int(category_id))
            except (ValueError, Category.DoesNotExist):
                errors['category'] = "Select a valid category."
        else:
            errors['category'] = "Please select or create a category."

        # Featured Collection logic
        featured_collection = None
        if new_collection_name:
            featured_collection, created = FeaturedCollection.objects.get_or_create(
                name=new_collection_name,
                defaults={'description': f"Featured Collection for {new_collection_name}"}
            )
        elif featured_collection_id:
            try:
                featured_collection = FeaturedCollection.objects.get(id=int(featured_collection_id))
            except (ValueError, FeaturedCollection.DoesNotExist):
                errors['featured_collection'] = "Select a valid featured collection."

        if not errors:
            try:
                product = Product.objects.create(
                    name=name,
                    description=description,
                    price=price,
                    stock=stock,
                    category=category,
                    featured_collection=featured_collection,
                    image=image
                )
                messages.success(request, f"Product '{product.name}' created successfully!")
                return redirect('dashboard_products')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, error_list in e.message_dict.items():
                        errors[field] = " ".join(error_list)
                else:
                    errors['non_field_errors'] = " ".join(e.messages)

        return render(request, 'dashboard/add_product.html', {
            'errors': errors,
            'categories': categories,
            'collections': collections,
            'values': request.POST,
            'active_tab': 'products'
        })

    return render(request, 'dashboard/add_product.html', {
        'categories': categories,
        'collections': collections,
        'active_tab': 'products'
    })

@staff_required
def dashboard_edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all().order_by('name')
    collections = FeaturedCollection.objects.all().order_by('name')
    errors = {}
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price_raw = request.POST.get('price', '').strip()
        stock_raw = request.POST.get('stock', '').strip()
        category_id = request.POST.get('category_id', '').strip()
        new_category_name = request.POST.get('new_category_name', '').strip()
        featured_collection_id = request.POST.get('featured_collection_id', '').strip()
        new_collection_name = request.POST.get('new_collection_name', '').strip()
        image = request.FILES.get('image')

        if not name:
            errors['name'] = "Product name is required."
        if not price_raw:
            errors['price'] = "Price is required."
        else:
            try:
                price = float(price_raw)
                if price < 0:
                    errors['price'] = "Price cannot be negative."
            except ValueError:
                errors['price'] = "Enter a valid price."

        if not stock_raw:
            errors['stock'] = "Stock is required."
        else:
            try:
                stock = int(stock_raw)
                if stock < 0:
                    errors['stock'] = "Stock cannot be negative."
            except ValueError:
                errors['stock'] = "Enter a valid integer stock."

        # Category logic
        category = None
        if new_category_name:
            category, created = Category.objects.get_or_create(
                name=new_category_name,
                defaults={'description': f"Category for {new_category_name}"}
            )
        elif category_id:
            try:
                category = Category.objects.get(id=int(category_id))
            except (ValueError, Category.DoesNotExist):
                errors['category'] = "Select a valid category."
        else:
            errors['category'] = "Please select or create a category."

        # Featured Collection logic
        featured_collection = None
        if new_collection_name:
            featured_collection, created = FeaturedCollection.objects.get_or_create(
                name=new_collection_name,
                defaults={'description': f"Featured Collection for {new_collection_name}"}
            )
        elif featured_collection_id:
            try:
                featured_collection = FeaturedCollection.objects.get(id=int(featured_collection_id))
            except (ValueError, FeaturedCollection.DoesNotExist):
                errors['featured_collection'] = "Select a valid featured collection."

        if not errors:
            try:
                product.name = name
                product.description = description
                product.price = price
                product.stock = stock
                product.category = category
                product.featured_collection = featured_collection
                if image:
                    product.image = image
                product.save()
                messages.success(request, f"Product '{product.name}' updated successfully!")
                return redirect('dashboard_products')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, error_list in e.message_dict.items():
                        errors[field] = " ".join(error_list)
                else:
                    errors['non_field_errors'] = " ".join(e.messages)

        return render(request, 'dashboard/edit_product.html', {
            'product': product,
            'errors': errors,
            'categories': categories,
            'collections': collections,
            'active_tab': 'products'
        })

    return render(request, 'dashboard/edit_product.html', {
        'product': product,
        'categories': categories,
        'collections': collections,
        'active_tab': 'products'
    })

@staff_required
def dashboard_delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted successfully.")
    return redirect('dashboard_products')

@staff_required
def dashboard_add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, "Category name is required.")
        else:
            try:
                category = Category(name=name, description=description)
                category.full_clean()
                category.save()
                messages.success(request, f"Category '{name}' created successfully.")
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
    return redirect('dashboard_products')

@staff_required
def dashboard_delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    if category.products.exists():
        messages.error(request, f"Cannot delete category '{category.name}' because it contains products.")
    else:
        name = category.name
        category.delete()
        messages.success(request, f"Category '{name}' deleted successfully.")
    return redirect('dashboard_products')

@staff_required
def dashboard_orders(request):
    status_filter = request.GET.get('status', '').strip()
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter in ['Pending', 'Shipped', 'Delivered', 'Cancelled']:
        orders = orders.filter(status=status_filter)
        
    return render(request, 'dashboard/orders.html', {
        'orders': orders,
        'status_filter': status_filter,
        'active_tab': 'orders'
    })

@staff_required
def dashboard_update_order_status(request, id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=id)
        if order.status == 'Cancelled':
            messages.error(request, "Cannot update the status of a cancelled order.")
            return redirect('dashboard_orders')

        status = request.POST.get('status', '').strip()
        if status in ['Pending', 'Shipped', 'Delivered', 'Cancelled']:
            try:
                if status == 'Cancelled':
                    order.cancel()
                    messages.success(request, f"Order #{order.id} has been cancelled and stock restored.")
                else:
                    order.status = status
                    order.save()
                    messages.success(request, f"Order #{order.id} status updated to '{status}'.")
            except ValidationError as e:
                messages.error(request, " ".join(e.messages))
        else:
            messages.error(request, "Invalid order status value.")
    return redirect('dashboard_orders')

@staff_required
def dashboard_users(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('username')
    
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
        
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id:
            target_user = get_object_or_404(User, id=int(user_id))
            
            if action == 'toggle_staff':
                if target_user == request.user:
                    messages.error(request, "You cannot revoke your own staff privileges.")
                else:
                    target_user.is_staff = not target_user.is_staff
                    target_user.save()
                    messages.success(request, f"Toggled staff role for {target_user.username}.")
            elif action == 'delete_user':
                if target_user == request.user:
                    messages.error(request, "You cannot delete your own account from the dashboard.")
                else:
                    username = target_user.username
                    target_user.delete()
                    messages.success(request, f"User '{username}' deleted successfully.")
            return redirect('dashboard_users')

    return render(request, 'dashboard/users.html', {
        'users': users,
        'q': q,
        'active_tab': 'users'
    })
