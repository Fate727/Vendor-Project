from django.db import models
from UserModule.models import Users  


"""
======================
Seller Module
======================
"""

class Seller(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    SellerID = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="seller_requests" 
    )
    StoreName = models.CharField(max_length=255, default="My Store")
    StoreAddress = models.CharField(max_length=255)
    ProductionLicenseNumber = models.CharField(max_length=100)
    PAN = models.CharField(max_length=50, unique=True)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')


"""
======================
Category Module
======================

"""

class Category(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('disabled', 'Disabled'),
    )

    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    

"""
======================
Prodcut Module
======================
"""

class Product(models.Model):
    ProductID = models.AutoField(primary_key=True)
    SellerID = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name="products")

    CompanyName = models.CharField(max_length=150, blank=True, null=True)
    ProductName = models.CharField(max_length=200)
    Category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)  # Category header

    SubCategories = models.JSONField(default=list, blank=True)           # e.g. ["Electronics", "Laptops", "Gaming"]
    Units = models.JSONField(default=list, blank=True)                   # e.g. [{"unit":"kg","amount":1,"price":10}]
    Stock = models.IntegerField(default=0)                               # total stock available
    Specifications = models.JSONField(default=list, blank=True)          # e.g. [{"spec":"Weight","value":"12kg"}]
    Images = models.JSONField(default=list, blank=True)                  # e.g. ["img1.jpg","img2.jpg"]
    Description = models.TextField(blank=True, null=True)                # Product description

    CreatedAt = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
    
            if self.Category and self.SubCategories:
                from SellerModule.models import Tag
    
                for subcat in self.SubCategories:
                    Tag.objects.get_or_create(
                        Name=subcat,
                        CategoryID=self.Category
                    )

class Tag(models.Model):
    TagID = models.AutoField(primary_key=True)
    CategoryID = models.ForeignKey(
        'SellerModule.Category',
        on_delete=models.CASCADE,
        related_name='tags'
    )
    Name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('CategoryID', 'Name')

    def __str__(self):
        return f"{self.Name} ({self.CategoryID.name})"
