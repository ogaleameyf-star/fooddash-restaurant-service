"""Runtime configuration, read from environment variables (12-factor style).

In Kubernetes these values come from the ConfigMap and Secret in k8s/.
"""
import os


class Settings:
    service_name: str = "restaurant-service"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://restaurant:restaurant@localhost:5432/restaurant_db",
    )
    # When true, a few sample restaurants and menus are inserted on first start.
    seed_data: bool = os.getenv("SEED_DATA", "true").lower() == "true"


settings = Settings()
