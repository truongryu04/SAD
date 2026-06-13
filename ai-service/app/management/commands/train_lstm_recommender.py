from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from app.recommender import ProductRecommenderService


class Command(BaseCommand):
    help = "Train next-item LSTM recommender model from customer activity history."

    def add_arguments(self, parser):
        parser.add_argument("--epochs", type=int, default=8)
        parser.add_argument("--batch-size", type=int, default=64)
        parser.add_argument("--learning-rate", type=float, default=1e-3)
        parser.add_argument("--min-user-events", type=int, default=3)

    def handle(self, *args, **options):
        recommender = ProductRecommenderService(
            customer_service_url=settings.CUSTOMER_SERVICE_URL,
            product_service_url=settings.PRODUCT_SERVICE_URL,
        )

        self.stdout.write("Starting LSTM training...")
        try:
            result = recommender.train_lstm_model(
                epochs=options["epochs"],
                batch_size=options["batch_size"],
                learning_rate=options["learning_rate"],
                min_user_events=options["min_user_events"],
            )
        except Exception as ex:
            raise CommandError(f"LSTM training failed: {ex}") from ex

        self.stdout.write(self.style.SUCCESS("LSTM training completed."))
        self.stdout.write(str(result))
