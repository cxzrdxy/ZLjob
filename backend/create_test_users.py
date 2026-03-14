import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_user(username, password, is_superuser=False):
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists.")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        print(f"Password for '{username}' has been reset to '{password}'.")
    else:
        if is_superuser:
            User.objects.create_superuser(username=username, password=password, email=f"{username}@example.com")
            print(f"Superuser '{username}' created.")
        else:
            User.objects.create_user(username=username, password=password, email=f"{username}@example.com")
            print(f"User '{username}' created.")

if __name__ == "__main__":
    print("Creating test users...")
    create_user("admin", "admin123456", is_superuser=True)
    create_user("test", "test123456")
    print("Done.")
