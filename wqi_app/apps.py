from django.apps import AppConfig


class WqiAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wqi_app'

    def ready(self):
        import wqi_app.templatetags.wqi_filters
