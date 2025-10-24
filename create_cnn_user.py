from django.contrib.auth.models import User
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sporra.settings') 
django.setup()

username_to_create = 'CNN Indonesia'

if not User.objects.filter(username=username_to_create).exists():
    cnn_user = User.objects.create_user(
        username=username_to_create,
        email='noreply@cnnindonesia.com', # Dummy email
        first_name='CNN',
        last_name='Indonesia'
    )
    cnn_user.set_unusable_password() # Kunci password
    cnn_user.save()
    print(f"User '{username_to_create}' created successfully and password locked.")
else:
    print(f"User '{username_to_create}' already exists.")

print("Script finished.")