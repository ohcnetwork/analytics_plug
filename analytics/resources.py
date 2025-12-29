from enum import Enum

from pydantic import UUID4, field_validator, model_validator

from analytics.models import AnalyticsConfig
from analytics.registry import AnalyticsHandlerRegistry
from care.emr.resources.base import EMRResource


class AnalyticsContexts(str, Enum):
    facility = "facility"
    organization = "organization"


class BaseAnalyticsResource(EMRResource):
    __model__ = AnalyticsConfig
    __exclude__ = []

    id: UUID4 | None = None

    name: str
    description: str | None
    metadata: dict | None
    handler: str
    handler_args: dict
    context_type: AnalyticsContexts
    context_mapping: dict | None

    @field_validator("handler")
    @classmethod
    def validate_handler(cls, v):
        AnalyticsHandlerRegistry.get_analytics_handler(v)
        return v

    @model_validator(mode="after")
    def validate_service_resource(self):
        AnalyticsHandlerRegistry.get_analytics_handler(
            self.handler
        )().perform_validation(self.handler_args)
        return self

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
