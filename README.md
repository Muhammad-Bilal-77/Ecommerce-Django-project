# Evolvoria Premium E-Commerce Storefront

Welcome to **Evolvoria**, a state-of-the-art, premium e-commerce platform built with Django 5.2. Evolvoria delivers a visual storefront experience combining glassmorphic design aesthetics, high-performance interactions, and a comprehensive set of storefront and order management features.

---

## 🚀 Key Features

### 🛒 Customer Storefront & Catalog
* **Dynamic Home Page:** Meticulously designed section grids displaying Shop by Category, Featured Collections, and Trending Products.
* **Expandable Catalog Search:** Workable search form in the header that expands dynamically on click.
* **Product Details Page:** Refined single-image layout showing specifications, reviews, and interactive action buttons.
* **Dynamic Profile Avatars:** High-performance seed-based profiles powered by Dicebear's Fun Emoji SVGs (`fun-emoji`) matching user seeds.

### 💖 Wishlist & Cart System
* **Fully Workable Wishlist:** Add products to a personal wishlist from product lists/details pages. Wishlisted items can be easily removed or moved directly to the shopping cart.
* **Live Shopping Cart:** Add items, dynamically adjust quantities, calculate real-time subtotals, and automatically validate product inventory stock levels.

### 📦 Order Tracking & Management
* **Secure Checkout Flow:** Atomic transaction checks to prevent stock overselling during placement.
* **Fulfillment States:** Orders track through `Pending`, `Shipped`, and `Delivered` states.
* **Interactive Timeline:** Shows visual step-by-step progress tracking for customers.
* **Stock Restoration on Cancel:** Cancelling an order automatically returns the ordered item quantities back to the product inventory.
* **Visual Cancel Alert Banner:** If an order is cancelled, the visual timeline on the details page is replaced with a premium, red-accented cancellation information banner.

### 🔒 Security, Locking & Admin Roles
* **Locked Cancelled Status:** Once an order is cancelled (either by customer or admin), its status is locked; staff members cannot change the status of a locked order.
* **Automated Admin Redirects:** Logged-in admin and staff members (`is_staff=True`) are automatically redirected to the Admin Dashboard upon login, registration, or visiting root customer dashboard paths.
* **Dependency-Free Env Secrets:** Custom manual `.env` file parser loaded dynamically on start to secure `SECRET_KEY` and `DEBUG` variables.
* **Robust Git Exclusions:** Local `.env` parameters, virtual environments (`venv/`), database files (`db.sqlite3`), caches (`__pycache__/`), and local media directories are correctly excluded via `.gitignore`.

---

## 🛠️ Technology Stack
* **Framework:** Django 5.2.7
* **Database:** SQLite 3 (Development)
* **Frontend styling:** Vanilla CSS (Storefront pages) & Tailwind CSS (Mock-up landing pages)
* **Design Systems:** Glassmorphic cards, HSL tailored palettes, Plus Jakarta Sans, Inter, and Outfit typography systems.
* **Icons:** Google Material Symbols

---

## 📂 Project Architecture

```text
├── accounts/          # Customer authentication, profile management, and dashboard views
├── cart/              # Shopping cart storage and quantity actions
├── dashboard/         # Staff order fulfillment, user permissions, and admin dashboard views
├── ecommerce/         # Central project settings, manually loaded environment parser, and routing
├── media/             # Local database file uploads and product images
├── orders/            # Checkout flows, timeline tracking, and cancellation logics
├── products/          # Catalog structure, categories, collections, and storefront pages
├── wishlist/          # Favorite products tracking, models, and cart mapping
├── manage.py          # Django executive CLI file
├── .env               # Local secret environment settings file (ignored by Git)
└── .gitignore         # File exclusions mapping for Git repository commits
```

---

## ⚙️ Installation & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/Muhammad-Bilal-77/Ecommerce-Django-project.git
cd Ecommerce-Django-project
```

### 2. Configure Environment Variables
Create a file named `.env` in the root folder of the project. Fill in the following variables:
```ini
# Security Warning: keep the secret key used in production secret!
SECRET_KEY=your-custom-django-secret-key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG=True
```

### 3. Create & Activate Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install django
```

### 5. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed the Database
Run the two seeding scripts in the root directory to populate categories, collections, and premium dummy products:
```bash
python seed_collections.py
python seed_store.py
```

### 7. Run the Local Development Server
```bash
python manage.py runserver
```
Visit the local page at `http://127.0.0.1:8000/`.

---

## 🧪 Running Automated Tests
To run the full test suite comprising 67 unit tests covering accounts redirections, order cancellations, cart mechanisms, and wishlist validation:
```bash
python manage.py test
```
