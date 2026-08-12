from django.utils import timezone

from SellerModule.models import Product
from UserModule.models import ProductAnalytics


def update_product_analytics(transaction):

    print("Updating analytics...")