from django.db import models
from django.utils import timezone

class Users(models.Model):
    ROLE_CHOICES = (
        ('basic', 'Basic User'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )

    UserID = models.AutoField(primary_key=True)
    FullName = models.CharField(max_length=100)
    UserName = models.CharField(max_length=50, unique=True) 
    Email = models.EmailField(max_length=100, unique=True)   
    Phone = models.CharField(max_length=15)
    Address = models.CharField(max_length=255)
    Password = models.CharField(max_length=255) 
    Role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='basic')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    LoginAt = models.DateTimeField(auto_now_add=False)

    def __str__(self):
        return f"{self.UserName} ({self.get_Role_display()})"
  
    
class Cart(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    CartID = models.AutoField(primary_key=True)
    UserID = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )
    ProductID = models.ForeignKey(
        'SellerModule.Product',
        on_delete=models.CASCADE,
        related_name="cart_entries"
    )
    SelectedUnit = models.JSONField()
    UnitType = models.CharField(max_length=50)
    Quantity = models.IntegerField(default=1)
    Status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    AddedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('UserID', 'ProductID', 'UnitType', 'Status')
    
    def save(self, *args, **kwargs):
        if not self.UnitType and self.SelectedUnit:
            unit = self.SelectedUnit.get('unit', '')
            amount = self.SelectedUnit.get('amount', '')
            self.UnitType = f"{unit}-{amount}"
        super().save(*args, **kwargs)

class Transaction(models.Model):

    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    TransactionID = models.AutoField(primary_key=True)

    UserID = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    SellerID = models.ForeignKey(
        'SellerModule.Seller',
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # Example:
    # [{"product": 12, "qty": 2, "unit": "1kg", "price": 1234}]
    Products = models.JSONField(default=list)

    TotalAmount = models.FloatField(default=0)

    Status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS,
        default='pending'
    )

    PaymentMethod = models.CharField(max_length=20, default="Cash")
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)


class Feedback(models.Model):
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    title      = models.CharField(max_length=100)
    email      = models.EmailField(max_length=254)
    phone      = models.CharField(max_length=30, blank=True)
    message    = models.TextField()

    submitted_by = models.ForeignKey(
        Users,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedbacks",
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("new", "New"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )
