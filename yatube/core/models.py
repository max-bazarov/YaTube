from django.db import models


class PubDateModel(models.Model):
    """Абстрактная модель. Добавляет дату создания."""
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
