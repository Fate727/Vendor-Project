from decimal import Decimal
from collections import defaultdict
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from UserModule.models import Transaction, ProductAnalytics
from SellerModule.models import Product


class Command(BaseCommand):
    help = "Generate Product Analytics from completed Transaction history"

    def handle(self, *args, **kwargs):
        # Clear Old Analytics
        ProductAnalytics.objects.all().delete()

        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        previous_7_days_start = today - timedelta(days=14)
        last_30_days = today - timedelta(days=30)

        analytics = {}

        self.stdout.write("Reading transactions...")

        transactions = (
            Transaction.objects
            .filter(Status="completed")
            .order_by("CreatedAt")
        )

        # Read Transactions
        for transaction in transactions:
            transaction_date = transaction.CreatedAt.date()
            
            for item in transaction.Products:
                product_id = item["product"]
                qty = int(item["qty"])
                price = Decimal(str(item["price"]))
                
                key = (product_id, transaction.SellerID_id)
                
                if key not in analytics:
                    analytics[key] = {
                        "total_sales": 0,
                        "sales_7": 0,
                        "previous_7": 0,
                        "sales_30": 0,
                        "revenue": Decimal("0.00"),
                        "last_sale": None,
                        "price": price,
                    }
                
                data = analytics[key]
                
                # Update basic metrics
                data["total_sales"] += qty
                data["revenue"] += price * qty
                data["price"] = price
                
                # Last 7 days sales
                if transaction_date >= last_7_days:
                    data["sales_7"] += qty
                
                # Previous 7 days sales
                if previous_7_days_start <= transaction_date < last_7_days:
                    data["previous_7"] += qty
                
                # Last 30 days sales
                if transaction_date >= last_30_days:
                    data["sales_30"] += qty
                
                # Update last sale date
                if data["last_sale"] is None or transaction_date > data["last_sale"]:
                    data["last_sale"] = transaction_date

        self.stdout.write("Saving analytics...")
        objects = []

        # Create Analytics Records
        for (product_id, seller_id), data in analytics.items():
            try:
                product = Product.objects.get(ProductID=product_id)
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Product {product_id} not found, skipping...")
                )
                continue

            # Calculate days since last sale
            last_sale = data["last_sale"]
            days_since = (today - last_sale).days if last_sale else 999

            # Calculate sales growth rate
            if data["previous_7"] > 0:
                growth_rate = (data["sales_7"] - data["previous_7"]) / data["previous_7"]
            else:
                growth_rate = 0

            # Calculate average daily sales (based on 30 days)
            avg_daily_sales = round(data["sales_30"] / 30, 2)

            objects.append(
                ProductAnalytics(
                    ProductID=product,
                    SellerID_id=seller_id,
                    TotalSales=data["total_sales"],
                    SalesLast7Days=data["sales_7"],
                    SalesPrevious7Days=data["previous_7"],
                    SalesLast30Days=data["sales_30"],
                    SalesGrowthRate=round(growth_rate, 3),
                    AvgSalesPerDay=avg_daily_sales,
                    Revenue=data["revenue"],
                    Price=data["price"],
                    LastSaleDate=last_sale,
                    DaysSinceLastSale=days_since,
                )
            )

        # Bulk create analytics records
        if objects:
            ProductAnalytics.objects.bulk_create(objects, batch_size=1000)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(objects)} analytics records."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("No analytics records were created.")
            )