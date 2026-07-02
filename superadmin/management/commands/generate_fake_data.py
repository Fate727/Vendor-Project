import csv
import os
import json
import random
import uuid
import requests

from django.core.management.base import BaseCommand
from django.conf import settings

from SellerModule.models import Seller, Category, Product, Tag


class Command(BaseCommand):
    help = "Generate ~4000 products + categories + tags"

    def handle(self, *args, **kwargs):

        sellers = list(Seller.objects.all())

        if not sellers:
            self.stdout.write("No sellers found!")
            return

        csv_file = os.path.join(settings.BASE_DIR, "data", "products.csv")

        products_to_create = []

        self.stdout.write("Processing CSV products...")

        with open(csv_file, newline="", encoding="utf-8") as file:

            rows = list(csv.DictReader(file))

            # Loop twice to get about 4000 products
            for loop in range(2):

                self.stdout.write(f"Pass {loop + 1}/2")

                for i, row in enumerate(rows):

                    # -----------------------------
                    # CATEGORY
                    # -----------------------------
                    category_name = (row.get("Category") or "Unknown").strip()

                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        defaults={"status": "active"}
                    )

                    # -----------------------------
                    # CATEGORY IMAGE
                    # -----------------------------
                    if created or not category.image:

                        file_name = f"{uuid.uuid4()}.jpg"

                        folder_path = os.path.join(
                            settings.MEDIA_ROOT,
                            "categories"
                        )
                        os.makedirs(folder_path, exist_ok=True)

                        file_path = os.path.join(folder_path, file_name)

                        img_url = (
                            f"https://picsum.photos/400/400?"
                            f"random={random.randint(1,999999)}"
                        )

                        try:
                            response = requests.get(
                                img_url,
                                stream=True,
                                timeout=10
                            )

                            if response.status_code == 200:

                                with open(file_path, "wb") as f:
                                    for chunk in response.iter_content(1024):
                                        if chunk:
                                            f.write(chunk)

                                # Save relative path to ImageField
                                category.image = f"categories/{file_name}"
                                category.save(update_fields=["image"])

                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Category image failed ({category_name}): {e}"
                                )
                            )

                    # -----------------------------
                    # SELLER
                    # -----------------------------
                    seller = random.choice(sellers)

                    # -----------------------------
                    # IMAGE FILES
                    # -----------------------------
                    try:
                        images_list = json.loads(
                            row.get("ImageFiles", "[]")
                        )
                    except Exception:
                        images_list = []

                    images_list = [
                        f"products/{img}"
                        for img in images_list
                    ]

                    # -----------------------------
                    # SAFE JSON
                    # -----------------------------
                    def safe_json(field, default):
                        try:
                            return json.loads(
                                row.get(field, json.dumps(default))
                            )
                        except Exception:
                            return default

                    subcategories = safe_json(
                        "SubCategories",
                        [category_name]
                    )
                    units = safe_json("Units", [])
                    specs = safe_json("Specifications", [])

                    # -----------------------------
                    # PRODUCT
                    # -----------------------------
                    products_to_create.append(
                        Product(
                            SellerID=seller,
                            CompanyName=row.get(
                                "CompanyName",
                                "Unknown"
                            ),
                            ProductName=row.get(
                                "ProductName",
                                "Unnamed Product"
                            ),
                            Category=category,
                            SubCategories=subcategories,
                            Units=units,
                            Stock=int(
                                row.get("Stock", 0) or 0
                            ),
                            Specifications=specs,
                            Images=images_list,
                            Description=row.get(
                                "Description",
                                ""
                            )
                        )
                    )

                    if len(products_to_create) % 500 == 0:
                        self.stdout.write(
                            f"Prepared {len(products_to_create)} products..."
                        )

        # -----------------------------
        # BULK INSERT
        # -----------------------------
        Product.objects.bulk_create(
            products_to_create,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created {len(products_to_create)} products."
            )
        )

        # -----------------------------
        # CREATE TAGS
        # -----------------------------
        self.stdout.write("Creating tags...")

        created_tags = 0

        for product in Product.objects.select_related("Category"):

            if not product.Category:
                continue

            if not product.SubCategories:
                continue

            for subcat in product.SubCategories:

                subcat = str(subcat).strip()

                if not subcat:
                    continue

                _, created = Tag.objects.get_or_create(
                    CategoryID=product.Category,
                    Name=subcat
                )

                if created:
                    created_tags += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Created {created_tags} unique tags."
            )
        )