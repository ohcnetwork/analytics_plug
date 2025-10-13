from django.db import models

from care.emr.models.base import EMRBaseModel


class AnalyticsConfig(EMRBaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    handler = models.CharField(max_length=255)
    handler_args = models.JSONField(default=dict)
    context_type = models.CharField(max_length=255)
    context_mapping = models.JSONField(default=dict)
