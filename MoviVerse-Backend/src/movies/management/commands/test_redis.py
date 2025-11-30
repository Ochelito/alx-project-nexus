from django.core.management.base import BaseCommand
from django.core.cache import caches

class Command(BaseCommand):
    help = "Test Redis cache connectivity"

    def handle(self, *args, **options):
        cache = caches["default"]
        try:
            cache.set("healthcheck", "ok", timeout=5)
            v = cache.get("healthcheck")
            if v == "ok":
                self.stdout.write(self.style.SUCCESS("Redis cache OK"))
            else:
                self.stderr.write(self.style.ERROR("Redis cache failed to return expected value"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Redis test failed: {e}"))
