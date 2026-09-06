# signals.py

from datetime import timedelta

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Product
from UserModule.models import Transaction, ProductAnalytics


# ============================================================
# 1. Detect Pending -> Completed
# ============================================================

@receiver(pre_save, sender=Transaction)
def transaction_status_check(sender, instance, **kwargs):

    # New transaction
    if not instance.pk:
        instance._was_completed = False
        return

    try:
        # Get the transaction currently stored in the database
        old_transaction = Transaction.objects.get(pk=instance.pk)

        instance._was_completed = (
            old_transaction.Status == "pending"
            and instance.Status == "completed"
        )

    except Transaction.DoesNotExist:
        instance._was_completed = False


# ============================================================
# 2. Run Analytics Update After Transaction Is Saved
# ============================================================

@receiver(post_save, sender=Transaction)
def transaction_completed_handler(sender, instance, created, **kwargs):

    if not getattr(instance, "_was_completed", False):
        return

    for item in instance.Products:

        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)

        if not product_id or quantity <= 0:
            continue

        try:
            product = Product.objects.get(
                ProductID=product_id
            )

        except Product.DoesNotExist:
            continue

        update_product_analytics(
            product=product,
            seller=instance.Seller
        )


# ============================================================
# 3. Calculate Product Analytics
# ============================================================

def update_product_analytics(product, seller):

    today = timezone.localdate()

    # --------------------------------------------------------
    # Get all completed transactions for this seller
    # --------------------------------------------------------

    transactions = Transaction.objects.filter(
        Seller=seller,
        Status="completed"
    )

    # --------------------------------------------------------
    # Initialize values
    # --------------------------------------------------------

    total_sales = 0
    sales_last_30_days = 0
    sales_last_7_days = 0
    sales_previous_7_days = 0
    revenue = 0
    last_sale_date = None

    # --------------------------------------------------------
    # Date ranges
    # --------------------------------------------------------

    # Last 30 days including today
    last_30_days_start = today - timedelta(days=29)

    # Last 7 days including today
    last_7_days_start = today - timedelta(days=6)

    # Previous 7 days
    previous_7_days_start = today - timedelta(days=13)
    previous_7_days_end = today - timedelta(days=7)

    # --------------------------------------------------------
    # Process completed transactions
    # --------------------------------------------------------

    for transaction in transactions:

        # CreatedAt is a DateTimeField
        transaction_date = transaction.CreatedAt.date()

        # Products is JSONField
        for item in transaction.Products:

            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)

            # Check whether this transaction contains
            # the product we are calculating
            if str(product_id) != str(product.ProductID):
                continue

            # Ignore invalid quantities
            if not quantity or quantity <= 0:
                continue

            # ------------------------------------------------
            # Total Sales
            # ------------------------------------------------

            total_sales += quantity

            # ------------------------------------------------
            # Revenue
            # ------------------------------------------------

            revenue += product.Price * quantity

            # ------------------------------------------------
            # Last Sale Date
            # ------------------------------------------------

            if (
                last_sale_date is None
                or transaction_date > last_sale_date
            ):
                last_sale_date = transaction_date

            # ------------------------------------------------
            # Sales Last 30 Days
            # ------------------------------------------------

            if transaction_date >= last_30_days_start:
                sales_last_30_days += quantity

            # ------------------------------------------------
            # Sales Last 7 Days
            # ------------------------------------------------

            if transaction_date >= last_7_days_start:
                sales_last_7_days += quantity

            # ------------------------------------------------
            # Sales Previous 7 Days
            # ------------------------------------------------

            if (
                previous_7_days_start
                <= transaction_date
                <= previous_7_days_end
            ):
                sales_previous_7_days += quantity

    # ========================================================
    # 4. Calculate Average Sales Per Day
    # ========================================================

    avg_sales_per_day = sales_last_30_days / 30


    # ========================================================
    # 5. Calculate Sales Growth Rate
    # ========================================================

    if sales_previous_7_days > 0:

        sales_growth_rate = (
            (sales_last_7_days - sales_previous_7_days)
            / sales_previous_7_days
        ) * 100

    else:
        if sales_last_7_days > 0:
            sales_growth_rate = 100
        else:
            sales_growth_rate = 0

    # ========================================================
    # 6. Calculate Days Since Last Sale
    # ========================================================

    if last_sale_date:

        days_since_last_sale = (
            today - last_sale_date
        ).days

    else:

        days_since_last_sale = 0

    # ========================================================
    # 7. Create or Update ProductAnalytics
    # ========================================================

    analytics, created = ProductAnalytics.objects.get_or_create(

        ProductID=product,

        SellerID=seller,

        defaults={
            "Price": product.Price
        }
    )

    # ========================================================
    # 8. Save Analytics Values
    # ========================================================

    analytics.TotalSales = total_sales

    analytics.SalesLast30Days = sales_last_30_days

    analytics.AvgSalesPerDay = avg_sales_per_day

    analytics.Revenue = revenue

    analytics.Price = product.Price

    analytics.LastSaleDate = last_sale_date

    analytics.SalesLast7Days = sales_last_7_days

    analytics.SalesPrevious7Days = sales_previous_7_days

    analytics.SalesGrowthRate = sales_growth_rate

    analytics.DaysSinceLastSale = days_since_last_sale

    analytics.save()