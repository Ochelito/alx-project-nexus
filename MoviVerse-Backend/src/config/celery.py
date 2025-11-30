import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialize Celery with your Django project name
app = Celery("config")

# Load Celery settings using prefix CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Celery Debug Task: {self.request!r}")
    
