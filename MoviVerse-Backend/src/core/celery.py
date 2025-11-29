import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("MoviVerse")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Celery Debug Task Executed: {self.request!r}")
