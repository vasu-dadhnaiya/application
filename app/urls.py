from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('superuser/dashboard/', views.superuser_dashboard_view, name='superuser_dashboard'),
    path('superuser/edit/<int:user_id>/', views.superuser_edit_user_view, name='superuser_edit_user'),
    path('superuser/delete/<int:user_id>/', views.superuser_delete_user_view, name='superuser_delete_user'),
]
