from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class ProfileUserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile_user'

    def ready(self):
        from django.contrib.auth.models import User
        from profile_user.models import UserProfile
        
        @receiver(post_migrate)
        def create_default_admin(sender, **kwargs):
            if sender.name == 'profile_user':
                try:
                    # Cek apakah admin sudah ada
                    admin_user = User.objects.get(username='admin')
                except User.DoesNotExist:
                    # Buat admin baru jika belum ada
                    admin_user = User.objects.create_superuser(
                        username='admin',
                        password='pbpsuksesd09',
                    )
                
                # Cek apakah profile admin sudah ada
                try:
                    UserProfile.objects.get(user=admin_user)
                except UserProfile.DoesNotExist:
                    # Buat profile admin jika belum ada
                    UserProfile.objects.create(
                        user=admin_user,
                        full_name='Admin Sporra',
                        role='admin'
                    )