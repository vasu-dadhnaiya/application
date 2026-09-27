import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
django.setup()


from django.test import Client
from django.contrib.auth.models import User
from app.models import UserProfile

def run_tests():
    print("=== STARTING DJANGO FEATURE VERIFICATION TESTS ===")
    client = Client()

    # 1. Clean test data if left over
    User.objects.filter(username__in=['john_doe', 'admin_boss', 'dup_user']).delete()

    # 2. Test User Registration via POST
    print("\n[Test 1] Testing User Registration...")
    reg_response = client.post('/register/', {
        'username': 'john_doe',
        'full_name': 'John Doe',
        'email': 'john@example.com',
        'contact_number': '9876543210',
        'age': 28,
        'password': 'TestPassword123!',
        'confirm_password': 'TestPassword123!'
    }, follow=True)

    assert reg_response.status_code == 200, f"Registration failed with code {reg_response.status_code}"
    assert 'Welcome, John Doe!' in reg_response.content.decode('utf-8'), "Welcome greeting missing on dashboard after registration"
    print("[OK] Registration successful & auto-logged in. Welcome greeting verified!")

    # 3. Verify user and profile database entries
    user = User.objects.get(username='john_doe')
    profile = UserProfile.objects.get(user=user)
    assert profile.full_name == 'John Doe'
    assert profile.contact_number == '9876543210'
    assert profile.age == 28
    assert user.email == 'john@example.com'
    print("[OK] User and UserProfile database fields saved accurately!")

    # 4. Test Invalid Form Data (Duplicate email & invalid age)
    print("\n[Test 2] Testing Form Validations (Duplicate Email & Bad Age)...")
    client.logout()
    invalid_reg = client.post('/register/', {
        'username': 'dup_user',
        'full_name': 'Duplicate User',
        'email': 'john@example.com', # Duplicate email!
        'contact_number': '1234567890',
        'age': 150, # Invalid age (> 120)
        'password': 'Pass',
        'confirm_password': 'MismatchPassword'
    })
    assert invalid_reg.status_code == 200
    assert 'A user with this email address already exists' in invalid_reg.content.decode('utf-8')
    assert 'Age must be between 1 and 120' in invalid_reg.content.decode('utf-8')
    assert 'Passwords do not match' in invalid_reg.content.decode('utf-8')
    print("[OK] Validation rules for duplicate email, age range, and password confirmation passed!")

    # 5. Test Edit Profile for logged-in user
    print("\n[Test 3] Testing Edit Profile...")
    client.login(username='john_doe', password='TestPassword123!')
    edit_resp = client.post('/profile/edit/', {
        'full_name': 'John Updated',
        'email': 'john.updated@example.com',
        'contact_number': '9988776655',
        'age': 29
    }, follow=True)
    assert edit_resp.status_code == 200
    profile.refresh_from_db()
    user.refresh_from_db()
    assert profile.full_name == 'John Updated'
    assert profile.contact_number == '9988776655'
    assert profile.age == 29
    assert user.email == 'john.updated@example.com'
    print("[OK] User profile updated successfully!")

    # 6. Test Logout
    print("\n[Test 4] Testing Logout...")
    logout_resp = client.get('/logout/', follow=True)
    assert logout_resp.status_code == 200
    assert 'You have been logged out successfully.' in logout_resp.content.decode('utf-8')
    print("[OK] Logout successful!")

    # 7. Test Login
    print("\n[Test 5] Testing Login...")
    login_resp = client.post('/', {
        'username': 'john_doe',
        'password': 'TestPassword123!'
    }, follow=True)
    assert login_resp.status_code == 200
    assert 'Welcome back, John Updated!' in login_resp.content.decode('utf-8')
    print("[OK] Login successful and greeting dynamically rendered!")

    # 8. Test Superuser Dashboard Access Block for Normal User
    print("\n[Test 6] Testing Superuser Dashboard Access Restrictions...")
    admin_dash_resp = client.get('/superuser/dashboard/')
    assert admin_dash_resp.status_code == 403, f"Expected 403 Forbidden, got {admin_dash_resp.status_code}"
    assert 'Access Denied' in admin_dash_resp.content.decode('utf-8')
    print("[OK] Superuser dashboard correctly BLOCKED normal user with HTTP 403 Forbidden!")

    # 9. Create Superuser and Login as Superuser
    print("\n[Test 7] Testing Superuser Access & Features...")
    admin_user = User.objects.create_superuser('admin_boss', 'admin@boss.com', 'AdminPass123!')
    UserProfile.objects.create(user=admin_user, full_name='Admin Boss', contact_number='0000000000', age=35)

    client.get('/logout/')
    admin_login = client.post('/', {
        'username': 'admin_boss',
        'password': 'AdminPass123!'
    }, follow=True)

    assert admin_login.status_code == 200
    assert 'superuser/dashboard' in admin_login.redirect_chain[0][0]
    print("[OK] Superuser login redirected to superuser dashboard!")

    # 10. Test Search on Superuser Dashboard
    search_resp = client.get('/superuser/dashboard/?q=John')
    assert search_resp.status_code == 200
    assert 'John Updated' in search_resp.content.decode('utf-8')
    print("[OK] Superuser search functionality working!")

    # 11. Test Superuser Edit User
    edit_user_resp = client.post(f'/superuser/edit/{user.id}/', {
        'full_name': 'John EditByAdmin',
        'email': 'john.adminedit@example.com',
        'contact_number': '9988776655',
        'age': 30
    }, follow=True)
    assert edit_user_resp.status_code == 200
    profile.refresh_from_db()
    assert profile.full_name == 'John EditByAdmin'
    print("[OK] Superuser user edit function verified!")

    # 12. Test Superuser Delete User
    del_resp = client.post(f'/superuser/delete/{user.id}/', follow=True)
    assert del_resp.status_code == 200
    assert not User.objects.filter(username='john_doe').exists()
    print("[OK] Superuser delete user function verified!")

    # Cleanup admin
    admin_user.delete()
    print("\n==========================================")
    print("SUCCESS: ALL 12 INTEGRATION & SECURITY TESTS PASSED PERFECTLY!")
    print("==========================================")

if __name__ == '__main__':
    run_tests()
