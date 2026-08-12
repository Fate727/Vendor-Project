from django.core.management.base import BaseCommand

from UserModule.models import Transaction
from SellerModule.models import Product

import os
import pandas as pd

from django.conf import settings

from datetime import timedelta
from collections import defaultdict


class Command(BaseCommand):

    help = "Generate ML training dataset from transaction history"


    def handle(self, *args, **kwargs):


        # ---------------------------------
        # Cache Product Information
        # ---------------------------------

        product_info = {}


        for product in Product.objects.select_related(
            "Category"
        ).all():


            price = 0


            if product.Units:

                try:
                    price = float(
                        product.Units[0]["price"]
                    )

                except:
                    price = 0



            product_info[
                product.ProductID
            ] = {


                "price":
                    price,


                "category_id":
                    product.Category.category_id
                    if product.Category else 0,


                "category_name":
                    product.Category.name
                    if product.Category else "Unknown",


                "stock":
                    product.Stock,


                "created_at":
                    product.CreatedAt.date()

            }



        # ---------------------------------
        # Read Completed Transactions
        # ---------------------------------

        transactions = Transaction.objects.filter(
            Status="completed"
        ).order_by("CreatedAt")



        product_sales = defaultdict(list)



        for transaction in transactions:


            for item in transaction.Products:


                product_id = item["product"]

                qty = item["qty"]

                price = item["price"]



                product_sales[
                    (
                        product_id,
                        transaction.SellerID_id
                    )
                ].append({


                    "date":
                        transaction.CreatedAt.date(),


                    "qty":
                        qty,


                    "revenue":
                        qty * price

                })




        dataset = []



        # ---------------------------------
        # Generate Weekly Snapshots
        # ---------------------------------

        for (product_id, seller_id), sales in product_sales.items():


            if product_id not in product_info:
                continue



            sales.sort(
                key=lambda x:x["date"]
            )



            info = product_info[product_id]



            first_date = sales[0]["date"]

            last_date = sales[-1]["date"]



            current_date = first_date



            while current_date <= last_date:



                total_sales = 0

                revenue = 0


                sales_last_7 = 0

                sales_previous_7 = 0

                sales_last_30 = 0


                last_sale_date = None



                # ---------------------------------
                # Historical Sales Features
                # ---------------------------------

                for sale in sales:



                    if sale["date"] <= current_date:



                        diff = (
                            current_date -
                            sale["date"]
                        ).days



                        total_sales += sale["qty"]

                        revenue += sale["revenue"]



                        if diff <= 7:

                            sales_last_7 += sale["qty"]



                        elif diff <= 14:

                            sales_previous_7 += sale["qty"]



                        if diff <= 30:

                            sales_last_30 += sale["qty"]



                        if (
                            last_sale_date is None
                            or sale["date"] > last_sale_date
                        ):

                            last_sale_date = sale["date"]




                # ---------------------------------
                # Sales Growth Rate
                # ---------------------------------

                if sales_previous_7 > 0:

                    sales_growth_rate = (

                        sales_last_7 -
                        sales_previous_7

                    ) / sales_previous_7

                else:

                    sales_growth_rate = 0




                # ---------------------------------
                # Target Next 7 Days
                # ---------------------------------

                target_next_7 = 0


                future_date = (
                    current_date +
                    timedelta(days=7)
                )



                for sale in sales:


                    if (
                        current_date <
                        sale["date"]
                        <= future_date
                    ):

                        target_next_7 += sale["qty"]





                # ---------------------------------
                # Last Sale
                # ---------------------------------

                if last_sale_date:


                    days_since_last_sale = (

                        current_date -
                        last_sale_date

                    ).days


                else:

                    days_since_last_sale = 999




                # ---------------------------------
                # Average Sales
                # ---------------------------------

                days_active = (

                    current_date -
                    first_date

                ).days + 1



                avg_daily_sales = (

                    total_sales /
                    days_active

                )




                # ---------------------------------
                # Product Age
                # ---------------------------------

                product_age_days = (

                    current_date -
                    info["created_at"]

                ).days




                dataset.append({


                    # IDs kept for reference

                    "ProductID":
                        product_id,


                    "SellerID":
                        seller_id,



                    "Date":
                        current_date,



                    # Sales Features

                    "TotalSales":
                        total_sales,


                    "SalesLast7Days":
                        sales_last_7,


                    "SalesPrevious7Days":
                        sales_previous_7,


                    "SalesLast30Days":
                        sales_last_30,


                    "SalesGrowthRate":
                        round(
                            sales_growth_rate,
                            3
                        ),



                    "Revenue":
                        round(
                            revenue,
                            2
                        ),



                    "AvgDailySales":
                        round(
                            avg_daily_sales,
                            2
                        ),



                    # Product Features

                    "Price":
                        info["price"],


                    "CategoryID":
                        info["category_id"],


                    "CategoryName":
                        info["category_name"],


                    "CurrentStock":
                        info["stock"],


                    "ProductAgeDays":
                        product_age_days,



                    # Time Features

                    "Month":
                        current_date.month,


                    "Week":
                        current_date.isocalendar().week,


                    "DayOfWeek":
                        current_date.weekday(),




                    "DaysSinceLastSale":
                        days_since_last_sale,



                    # Target

                    "TargetNext7Days":
                        target_next_7

                })



                current_date += timedelta(days=7)




        # ---------------------------------
        # Save Dataset
        # ---------------------------------

        df = pd.DataFrame(dataset)



        data_folder = os.path.join(
            settings.BASE_DIR,
            "data"
        )



        os.makedirs(
            data_folder,
            exist_ok=True
        )



        file_path = os.path.join(
            data_folder,
            "ml_product_sales_dataset.csv"
        )



        df.to_csv(
            file_path,
            index=False
        )



        self.stdout.write(
            self.style.SUCCESS(
                f"Dataset created: {len(df)} rows"
            )
        )