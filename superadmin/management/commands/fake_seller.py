import random

from faker import Faker

from django.core.management.base import BaseCommand

from UserModule.models import Users
from SellerModule.models import Seller


class Command(BaseCommand):
    help = "Generate fake sellers"

    def handle(self, *args, **kwargs):

        fake = Faker()

        # Number of sellers to create
        seller_count = 500

        # Get users that are still basic users
        users = list(
            Users.objects.filter(Role="basic")[:seller_count]
        )

        if len(users) < seller_count:
            self.stdout.write(
                self.style.ERROR(
                    f"Only {len(users)} basic users available."
                )
            )
            return

        sellers = []

        self.stdout.write("Generating sellers...")

        for i, user in enumerate(users):

            # Change user role
            user.Role = "seller"

            sellers.append(
                Seller(
                    UserId=user,
                    StoreName=fake.company(),
                    StoreAddress=fake.address().replace("\n", ", "),
                    ProductionLicenseNumber=f"LIC-{fake.unique.numerify('########')}",
                    PAN=fake.unique.numerify("#########"),
                    Status="accepted",
                )
            )

            if (i + 1) % 50 == 0:
                self.stdout.write(f"Prepared {i + 1} sellers...")

        # Update user roles
        Users.objects.bulk_update(
            users,
            ["Role"],
            batch_size=500
        )

        # Create sellers
        Seller.objects.bulk_create(
            sellers,
            batch_size=500
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created {len(sellers)} sellers."
            )
        )