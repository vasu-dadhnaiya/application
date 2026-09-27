from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, verbose_name="User Name")
    contact_number = models.CharField(max_length=20, verbose_name="Contact Number")
    age = models.PositiveIntegerField(verbose_name="Age")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

    @property
    def email(self):
        return self.user.email

