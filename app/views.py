from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Avg
from django.http import HttpResponseForbidden

from .models import UserProfile
from .forms import UserRegistrationForm, UserLoginForm, UserProfileEditForm


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superuser_dashboard')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user, profile = form.save()
            login(request, user)
            messages.success(request, f"Registration successful! Welcome, {profile.full_name}!")
            return redirect('user_dashboard')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'app/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superuser_dashboard')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Fetch profile for greeting name
                display_name = user.first_name or user.username
                if hasattr(user, 'profile') and user.profile.full_name:
                    display_name = user.profile.full_name

                messages.success(request, f"Welcome back, {display_name}!")

                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_superuser:
                    return redirect('superuser_dashboard')
                return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please fill in all required fields.")
    else:
        form = UserLoginForm()

    return render(request, 'app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def user_dashboard_view(request):
    user = request.user
    # Ensure profile exists
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': user.first_name or user.username,
            'contact_number': 'N/A',
            'age': 25
        }
    )

    context = {
        'user': user,
        'profile': profile,
        'user_name': profile.full_name or user.username,
    }
    return render(request, 'app/dashboard.html', context)


@login_required
def edit_profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'full_name': user.first_name or user.username,
            'contact_number': 'N/A',
            'age': 25
        }
    )

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, user=user)
        if form.is_valid():
            form.save(user=user)
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('user_dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserProfileEditForm(
            initial={
                'full_name': profile.full_name,
                'email': user.email,
                'contact_number': profile.contact_number if profile.contact_number != 'N/A' else '',
                'age': profile.age,
            },
            user=user
        )

    return render(request, 'app/user_edit.html', {'form': form, 'is_self_edit': True})


@login_required
def superuser_dashboard_view(request):
    # Strict superuser check
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            render(request, '403.html', {'message': "Access Denied: Superuser permissions are required to view this dashboard."})
        )

    query = request.GET.get('q', '').strip()
    users_qs = User.objects.all().select_related('profile').order_by('-date_joined')

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(profile__full_name__icontains=query) |
            Q(profile__contact_number__icontains=query)
        ).distinct()

    total_users = User.objects.count()
    superuser_count = User.objects.filter(is_superuser=True).count()

    # Calculate statistics
    avg_age_dict = UserProfile.objects.aggregate(avg_age=Avg('age'))
    avg_age = round(avg_age_dict['avg_age'], 1) if avg_age_dict['avg_age'] else 'N/A'

    context = {
        'users': users_qs,
        'query': query,
        'total_users': total_users,
        'superuser_count': superuser_count,
        'avg_age': avg_age,
    }
    return render(request, 'app/admin_dashboard.html', context)


@login_required
def superuser_edit_user_view(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            render(request, '403.html', {'message': "Access Denied: Superuser permissions are required."})
        )

    target_user = get_object_or_404(User, pk=user_id)
    profile, created = UserProfile.objects.get_or_create(
        user=target_user,
        defaults={
            'full_name': target_user.first_name or target_user.username,
            'contact_number': 'N/A',
            'age': 25
        }
    )

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, user=target_user)
        if form.is_valid():
            form.save(user=target_user)
            messages.success(request, f"User '{target_user.username}' updated successfully!")
            return redirect('superuser_dashboard')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserProfileEditForm(
            initial={
                'full_name': profile.full_name,
                'email': target_user.email,
                'contact_number': profile.contact_number if profile.contact_number != 'N/A' else '',
                'age': profile.age,
            },
            user=target_user
        )

    return render(request, 'app/user_edit.html', {
        'form': form,
        'target_user': target_user,
        'is_self_edit': False
    })


@login_required
def superuser_delete_user_view(request, user_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            render(request, '403.html', {'message': "Access Denied: Superuser permissions are required."})
        )

    if request.method != 'POST':
        messages.error(request, "Invalid request method for user deletion.")
        return redirect('superuser_dashboard')

    target_user = get_object_or_404(User, pk=user_id)

    if target_user.pk == request.user.pk:
        messages.error(request, "You cannot delete your own superuser account while logged in!")
        return redirect('superuser_dashboard')

    username = target_user.username
    target_user.delete()
    messages.success(request, f"User '{username}' has been successfully deleted.")
    return redirect('superuser_dashboard')
