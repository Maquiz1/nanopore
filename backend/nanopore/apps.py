from django.apps import AppConfig


class NanoporeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nanopore'

    def ready(self):
        from nanopore import history
        history.connect()
