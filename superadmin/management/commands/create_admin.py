from django.core.management.base import BaseCommand
from UserModule.models import Users
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime

class Command(BaseCommand):
    help = 'Creates an admin user with a simple password'

    def handle(self, *args, **kwargs):
        # Check if the admin already exists
        if not Users.objects.filter(Role='admin').exists():
            username = 'admin'
            email = 'admin@gmail.com'
            password = 'admin1234'
            full_name = 'Admin'
            phone = '9876123455'
            address = 'adminplace'

            hashed_password = make_password(password)

            Users.objects.create(
                UserName=username,
                Email=email,
                Password=hashed_password,
                FullName=full_name,
                Phone=phone,
                Address=address,
                Role='admin',
                CreatedAt=datetime.now(),
                LoginAt=datetime.now()
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user with username {username}'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists.'))
