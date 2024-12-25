from django.apps import AppConfig


class QpaperanalyzerappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'QPaperAnalyzerApp'

    def ready(self):
        import QPaperAnalyzerApp.signals


