from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import Category, Product, FeaturedCollection

def home(request):
    categories = Category.objects.all()
    collections = FeaturedCollection.objects.all()
    # Fetch 8 most recent products as featured products
    featured_products = Product.objects.all().order_by('-created_at')[:8]
    return render(request, 'products/home.html', {
        'categories': categories,
        'collections': collections,
        'featured_products': featured_products
    })

def all_products(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
        
    selected_category = None
    if category_id:
        try:
            category_id_int = int(category_id)
            products = products.filter(category_id=category_id_int)
            selected_category = Category.objects.filter(id=category_id_int).first()
        except ValueError:
            pass

    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'selected_category': selected_category
    })

def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('-created_at')
    return render(request, 'products/category_products.html', {
        'category': category,
        'products': products
    })

def collection_products(request, collection_id):
    collection = get_object_or_404(FeaturedCollection, id=collection_id)
    products = Product.objects.filter(featured_collection=collection).order_by('-created_at')
    return render(request, 'products/collection_products.html', {
        'collection': collection,
        'products': products
    })

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).order_by('-created_at')[:6]
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })

@login_required(login_url='login')
def upload_product(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only staff members can perform this action.")
        return redirect('home')
    categories = Category.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price_raw = request.POST.get('price', '').strip()
        stock_raw = request.POST.get('stock', '').strip()
        category_id = request.POST.get('category_id', '').strip()
        new_category_name = request.POST.get('new_category_name', '').strip()
        image = request.FILES.get('image')

        errors = {}

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

        # Handle category selection or creation
        category = None
        if new_category_name:
            # Check if category already exists
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

        if not errors:
            try:
                product = Product.objects.create(
                    name=name,
                    description=description,
                    price=price,
                    stock=stock,
                    category=category,
                    image=image
                )
                messages.success(request, f"Product '{product.name}' uploaded successfully!")
                return redirect('all_products')
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, error_list in e.message_dict.items():
                        errors[field] = " ".join(error_list)
                else:
                    errors['non_field_errors'] = " ".join(e.messages)

        if errors:
            return render(request, 'products/upload_product.html', {
                'errors': errors,
                'categories': categories,
                'values': request.POST
            })

    return render(request, 'products/upload_product.html', {
        'categories': categories
    })

@login_required(login_url='login')
def edit_product(request, id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only staff members can perform this action.")
        return redirect('home')
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price_raw = request.POST.get('price', '').strip()
        stock_raw = request.POST.get('stock', '').strip()
        category_id = request.POST.get('category_id', '').strip()
        new_category_name = request.POST.get('new_category_name', '').strip()
        image = request.FILES.get('image')

        errors = {}

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

        if not errors:
            try:
                product.name = name
                product.description = description
                product.price = price
                product.stock = stock
                product.category = category
                if image:
                    product.image = image
                product.save()
                messages.success(request, f"Product '{product.name}' updated successfully!")
                return redirect('product_detail', id=product.id)
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, error_list in e.message_dict.items():
                        errors[field] = " ".join(error_list)
                else:
                    errors['non_field_errors'] = " ".join(e.messages)

        if errors:
            return render(request, 'products/edit_product.html', {
                'errors': errors,
                'categories': categories,
                'product': product
            })

    return render(request, 'products/edit_product.html', {
        'product': product,
        'categories': categories
    })

@login_required(login_url='login')
def delete_product(request, id):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Only staff members can perform this action.")
        return redirect('home')
    product = get_object_or_404(Product, id=id)
    product_name = product.name
    product.delete()
    messages.success(request, f"Product '{product_name}' deleted successfully.")
    return redirect('all_products')
