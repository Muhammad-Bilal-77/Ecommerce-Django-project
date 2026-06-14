from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

def register(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    errors = {}
    values = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        values = {
            'username': username,
            'email': email
        }

        # Validations
        if not username:
            errors['username'] = "Username is required."
        elif User.objects.filter(username=username).exists():
            errors['username'] = "Username is already taken."

        if not email:
            errors['email'] = "Email address is required."
        elif User.objects.filter(email=email).exists():
            errors['email'] = "Already registered this user mail"
            messages.warning(request, "Already registered this user mail")

        if not password:
            errors['password'] = "Password is required."
        else:
            try:
                # Create a temporary user instance to run similarity check validators
                temp_user = User(username=username, email=email)
                validate_password(password, temp_user)
            except ValidationError as e:
                errors['password'] = " ".join(e.messages)

        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        if not errors:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')

    return render(request, 'accounts/register.html', {
        'errors': errors,
        'values': values
    })

def login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    errors = {}
    username = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username:
            errors['username'] = "Username is required."
        if not password:
            errors['password'] = "Password is required."

        if not errors:
            # Check if user exists
            if not User.objects.filter(username=username).exists():
                messages.warning(request, "User does not exist. Redirecting to registration page.")
                return redirect('register')

            # Authenticate user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                errors['password'] = "Incorrect password. Please try again."
                messages.error(request, "Invalid credentials.")

    return render(request, 'accounts/login.html', {
        'errors': errors,
        'username': username
    })

def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.success(request, "You have been successfully logged out.")
        return render(request, 'accounts/logout.html')
    else:
        return redirect('login')

def forget_password(request):
    errors = {}
    email = ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            errors['email'] = "Email is required."
        else:
            user = User.objects.filter(email=email).first()
            if user:
                # Store email in session to verify on the next page
                request.session['reset_email'] = email
                messages.info(request, "Account verified. Please reset your password below.")
                return redirect('reset_password')
            else:
                errors['email'] = "No user found with this email address."
                messages.error(request, "Email not found.")

    return render(request, 'accounts/forget_password.html', {
        'errors': errors,
        'email': email
    })

def reset_password(request):
    email = request.session.get('reset_email')
    if not email:
        messages.warning(request, "Please initiate forgot password flow first.")
        return redirect('forget_password')

    errors = {}

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not password:
            errors['password'] = "New password is required."
        else:
            try:
                user = User.objects.filter(email=email).first()
                validate_password(password, user)
            except ValidationError as e:
                errors['password'] = " ".join(e.messages)

        if password != confirm_password:
            errors['confirm_password'] = "Passwords do not match."

        if not errors:
            # Update user's password
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(password)
                user.save()
                # Clear session
                del request.session['reset_email']
                messages.success(request, "Password reset successfully. Please log in.")
                return redirect('login')
            else:
                messages.error(request, "An error occurred. Please try again.")
                return redirect('forget_password')

    return render(request, 'accounts/reset_password.html', {
        'errors': errors,
        'email': email
    })

@login_required(login_url='login')
def change_password(request):
    errors = {}

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, "Your password was successfully updated!")
            if request.user.is_staff:
                return redirect('profile')
            return redirect('dashboard')
        else:
            # Map form errors to display in our custom styled template
            for field, err_list in form.errors.items():
                if field == '__all__':
                    errors['old_password'] = " ".join(err_list)
                else:
                    errors[field] = " ".join(err_list)
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    if request.user.is_staff:
        return render(request, 'dashboard/change_password.html', {
            'errors': errors,
            'active_tab': 'settings',
            'active_sub_tab': 'change_password'
        })
    return render(request, 'accounts/change_password.html', {
        'errors': errors,
        'active_tab': 'settings',
        'active_sub_tab': 'change_password'
    })

@login_required(login_url='login')
def dashboard(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')
    return render(request, 'accounts/dashboard.html', {
        'session_key': request.session.session_key,
        'active_tab': 'overview'
    })


@login_required(login_url='login')
def profile(request):
    user = User.objects.filter(id = request.user.id).first()
    if request.user.is_staff:
        return render(request, 'dashboard/profile.html', {
            'user': user,
            'active_tab': 'settings',
            'active_sub_tab': 'profile'
        })
    return render(request, 'accounts/profile.html', {
        'user': user,
        'active_tab': 'settings',
        'active_sub_tab': 'profile'
    })  