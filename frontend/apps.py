from django.apps import AppConfig


class FrontendConfig(AppConfig):
    name = 'frontend'

    def ready(self):
        from .signals import login_signals

