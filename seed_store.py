import os
import django
import urllib.request
from django.core.files import File
from decimal import Decimal
import tempfile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Category, Product

# Categories to create
categories_data = [
    {
        "name": "Watches",
        "description": "Timeless luxury and precision engineering."
    },
    {
        "name": "Accessories",
        "description": "Refined accents to elevate your everyday look."
    },
    {
        "name": "Wearable Tech",
        "description": "Premium devices merging high-fashion with next-gen features."
    },
    {
        "name": "Limited Editions",
        "description": "Exclusive drops and rare curated releases."
    }
]

# Products to create
products_data = [
    {
        "name": "Evolvoria Aero Z1 Chronograph",
        "category_name": "Watches",
        "price": Decimal("240.00"),
        "stock": 15,
        "description": "A luxury, sleek, minimalist chronograph watch designed for precision and modern visual impact.",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Prism V2 Designer Eyewear",
        "category_name": "Accessories",
        "price": Decimal("185.00"),
        "stock": 8,
        "description": "Premium luxury designer sunglasses featuring polarized UV400 lenses and handcrafted acetate frames.",
        "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Titanium Smart Ring",
        "category_name": "Wearable Tech",
        "price": Decimal("350.00"),
        "stock": 20,
        "description": "Luxury health-tracking wearable crafted in lightweight aerospace-grade titanium with an ultra-thin profile.",
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Nova Tech Backpack",
        "category_name": "Accessories",
        "price": Decimal("320.00"),
        "stock": 12,
        "description": "Luxury minimalist waterproof carry-on featuring structured compartments and integrated charge ports.",
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Evolvoria Core Classic",
        "category_name": "Watches",
        "price": Decimal("450.00"),
        "stock": 5,
        "description": "High-end luxury gold-plated timepiece featuring a genuine Italian leather strap and Swiss movement.",
        "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Acoustic Noir Over-Ear",
        "category_name": "Wearable Tech",
        "price": Decimal("499.00"),
        "stock": 10,
        "description": "Luxury active noise-cancelling wireless headphones with custom high-fidelity dynamic drivers.",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Stella 24K Gold Cuff",
        "category_name": "Accessories",
        "price": Decimal("150.00"),
        "stock": 30,
        "description": "Exquisite 24K gold-plated minimalist wrist cuff bracelet designed for a clean, timeless statement.",
        "image_url": "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=800&auto=format&fit=crop"
    },
    {
        "name": "Ethereal Aura Parfum",
        "category_name": "Limited Editions",
        "price": Decimal("210.00"),
        "stock": 4,
        "description": "A rare sensory experience: limited-run premium parfum crafted with organic jasmine, amber, and custom woods.",
        "image_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?q=80&w=800&auto=format&fit=crop"
    }
]

print("Starting store seeding...")

# Create Categories
category_objects = {}
for cat_info in categories_data:
    cat, created = Category.objects.get_or_create(
        name=cat_info["name"],
        defaults={"description": cat_info["description"]}
    )
    category_objects[cat_info["name"]] = cat
    if created:
        print(f"Created category: {cat.name}")
    else:
        print(f"Category already exists: {cat.name}")

# Create Products
for prod_info in products_data:
    cat_obj = category_objects.get(prod_info["category_name"])
    
    # Check if product already exists
    prod_exists = Product.objects.filter(name=prod_info["name"]).exists()
    if prod_exists:
        print(f"Product already exists: {prod_info['name']}")
        continue

    print(f"Downloading image for {prod_info['name']}...")
    try:
        # Download the image using urllib
        # Use headers to prevent HTTP 403 Forbidden errors from unsplash
        req = urllib.request.Request(
            prod_info["image_url"], 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            image_data = response.read()

        # Save to temporary file
        img_temp = tempfile.NamedTemporaryFile(delete=True)
        img_temp.write(image_data)
        img_temp.flush()
        
        # Instantiate Django File object
        filename = f"{prod_info['name'].lower().replace(' ', '_')}.jpg"
        django_file = File(img_temp, name=filename)

        # Create Product
        prod = Product.objects.create(
            category=cat_obj,
            name=prod_info["name"],
            price=prod_info["price"],
            stock=prod_info["stock"],
            description=prod_info["description"]
        )
        
        # Save image to field
        prod.image.save(filename, django_file, save=True)
        print(f"Successfully created product: {prod.name}")
        
    except Exception as e:
        print(f"Failed to create product {prod_info['name']}: {e}")

print("Seeding completed successfully!")
