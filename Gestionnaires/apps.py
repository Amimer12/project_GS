from django.apps import AppConfig



class GestionnairesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Gestionnaires'
    def ready(self):
        import Gestionnaires.signals
