from django.db.models.signals import pre_save
from django.dispatch import receiver

from UserModule.models import Transaction
from UserModule.services import update_product_analytics


@receiver(pre_save, sender=Transaction)
def transaction_completed(sender, instance, **kwargs):

    # New transaction
    if instance.pk is None:
        return

    previous = Transaction.objects.get(pk=instance.pk)

    if (
        previous.Status != "completed"
        and instance.Status == "completed"
    ):
        update_product_analytics(instance)