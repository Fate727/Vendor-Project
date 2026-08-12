import random

from faker import Faker

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.utils import timezone

from UserModule.models import Users   # Change import if needed


class Command(BaseCommand):
    help = "Generate 2000 fake basic users"

    def handle(self, *args, **kwargs):

        fake = Faker()

        users = []

        self.stdout.write("Generating fake users...")

        while len(users) < 2000:

            username = fake.unique.user_name()
            email = fake.unique.email()

            try:
                user = Users(
                    FullName=fake.name(),
                    UserName=username,
                    Email=email,
                    Phone=fake.numerify("98########"),
                    Address=fake.address().replace("\n", ", "),
                    Password="pbkdf2_sha256$1000000$ZQbVKVgtb1Rfcb90vRdMPi$ZWEcYHFUTinFiwDfcMKAwDt3losXyYQnwJ+TcezbtBI=",
                    Role="basic",
                    LoginAt=timezone.now(),
                )

                users.append(user)

                if len(users) % 500 == 0:
                    self.stdout.write(
                        f"Prepared {len(users)} users..."
                    )

            except IntegrityError:
                continue

        Users.objects.bulk_create(
            users,
            batch_size=500
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully created {len(users)} fake users."
            )
        )