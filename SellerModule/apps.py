from django.apps import AppConfig


class SellermoduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'SellerModule'

def ready(self):
    import SellerModule.signals