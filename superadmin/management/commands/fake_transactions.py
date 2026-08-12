import random
from decimal import Decimal

from faker import Faker

from django.core.management.base import BaseCommand
from django.utils import timezone

from UserModule.models import Users, Transaction
from SellerModule.models import Seller, Product


class Command(BaseCommand):
    help = "Generate 20,000 fake transactions"

    def handle(self, *args, **kwargs):

        fake = Faker()

        users = list(
            Users.objects.filter(Role="basic")
        )

        sellers = list(
            Seller.objects.filter(Status="accepted")
        )

        if not users:
            self.stdout.write("No users found.")
            return

        if not sellers:
            self.stdout.write("No sellers found.")
            return

        # Cache products by seller
        seller_products = {}

        for seller in sellers:
            products = list(
                Product.objects.filter(SellerID=seller)
            )

            if products:
                seller_products[seller.SellerID] = products

        payment_methods = [
            "Cash",
            "eSewa",
            "Khalti",
            "FonePay"
        ]

        transactions = []

        self.stdout.write("Generating transactions...")

        for i in range(20000):

            user = random.choice(users)
            seller = random.choice(sellers)

            products = seller_products.get(seller.SellerID)

            if not products:
                continue

            cart = []
            total = Decimal("0.00")

            # Select 1–5 unique products
            selected_products = random.sample(
                products,
                min(random.randint(1, 5), len(products))
            )

            for product in selected_products:

                if not product.Units:
                    continue

                unit = random.choice(product.Units)

                qty = random.randint(1, 5)

                price = Decimal(str(unit["price"]))

                cart.append({
                    "product": product.ProductID,
                    "qty": qty,
                    "unit": unit["unit"],
                    "price": float(price)
                })

                total += price * qty

            # Skip if no valid products were added
            if not cart:
                continue

            transactions.append(

                Transaction(

                    UserID=user,

                    SellerID=seller,

                    Products=cart,

                    TotalAmount=total,

                    Status="completed",

                    PaymentMethod=random.choice(payment_methods),

                    CreatedAt=fake.date_time_between(
                        start_date="-1y",
                        end_date="now",
                        tzinfo=timezone.get_current_timezone()
                    )

                )

            )

            if (i + 1) % 1000 == 0:
                self.stdout.write(
                    f"Prepared {i + 1} transactions..."
                )

        Transaction.objects.bulk_create(
            transactions,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(transactions)} transactions."
            )
        )