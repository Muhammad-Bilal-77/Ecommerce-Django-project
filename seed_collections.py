import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from products.models import Product, FeaturedCollection

# Collections to create
collections_data = [
    {
        "name": "Summer Curated",
        "description": "Elevate your high-summer aesthetic with our signature lightweight edits."
    },
    {
        "name": "Modernist Core",
        "description": "Subtle profiles, structured geometries, and advanced functional materials."
    },
    {
        "name": "Vanguard Edition",
        "description": "Our rarest releases and design-house collaborations."
    }
]

print("Starting featured collections seeding...")

# Create or get collections
collection_objects = {}
for col_info in collections_data:
    col, created = FeaturedCollection.objects.get_or_create(
        name=col_info["name"],
        defaults={"description": col_info["description"]}
    )
    collection_objects[col_info["name"]] = col
    if created:
        print(f"Created featured collection: {col.name}")
    else:
        print(f"Featured collection already exists: {col.name}")

# Now assign products to these collections
# Let's map keywords from product names to their target collections
mappings = {
    "Summer Curated": ["Prism", "Cuff", "Backpack"],
    "Modernist Core": ["Ring", "Headphones", "Acoustic", "Wireless Mouse", "Laptop"],
    "Vanguard Edition": ["Parfum", "Chronograph", "Classic", "Evolvoria"]
}

assigned_count = 0
for col_name, keywords in mappings.items():
    col_obj = collection_objects.get(col_name)
    if not col_obj:
        continue
    
    for keyword in keywords:
        products = Product.objects.filter(name__icontains=keyword)
        for product in products:
            product.featured_collection = col_obj
            product.save()
            assigned_count += 1
            print(f"Assigned product '{product.name}' to collection '{col_name}'")

# If no products were assigned (e.g. if the store was empty), let's make sure we alert the user or check product count
product_count = Product.objects.count()
if product_count == 0:
    print("Warning: No products found in the database. Please run 'python seed_store.py' first to populate products, then rerun this script.")
elif assigned_count == 0:
    # Let's assign some products randomly if no keyword matches were found
    print("No keyword matches found. Assigning available products to collections...")
    products = list(Product.objects.all())
    for i, product in enumerate(products):
        col_list = list(collection_objects.values())
        col_obj = col_list[i % len(col_list)]
        product.featured_collection = col_obj
        product.save()
        assigned_count += 1
        print(f"Assigned product '{product.name}' to collection '{col_obj.name}'")

print(f"Featured collections seeding completed successfully! Assigned {assigned_count} products.")
