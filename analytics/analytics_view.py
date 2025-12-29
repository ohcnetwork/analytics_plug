from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from analytics.models import AnalyticsConfig
from analytics.registry import AnalyticsHandlerRegistry
from analytics.resources import AnalyticsContexts, BaseAnalyticsResource
from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRDestroyMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.organization import FacilityOrganizationUser, Organization, OrganizationUser
from care.facility.models.facility import Facility
from care.utils.shortcuts import get_object_or_404


def get_context_object(user, instance, external_id):
    if instance.context_type == AnalyticsContexts.facility.value:
        return get_object_or_404(Facility, external_id=external_id)
    elif instance.context_type == AnalyticsContexts.organization.value:
        return get_object_or_404(Organization, external_id=external_id)
    return None


def authorize_analytics_config(user, instance, obj):
    if user.is_superuser:
        return
    if (
        instance.context_type == AnalyticsContexts.facility.value
        and not FacilityOrganizationUser.objects.filter(
            user=user, organization__facility=obj
        ).exists()
    ):
        raise PermissionDenied("You are not authorized to access this analytics config")
    elif (
        instance.context_type == AnalyticsContexts.organization.value
        and not OrganizationUser.objects.filter(
            user=user, organization=obj
        ).exists()
    ):
        raise PermissionDenied("You are not authorized to access this analytics config")


def get_context(user, instance, obj):
    context = {"user_external_id": str(user.external_id), "user_id": str(user.id)}
    if instance.context_type == AnalyticsContexts.facility.value:
        context["facility_external_id"] = str(obj.external_id)
        context["facility_id"] = str(obj.id)
    elif instance.context_type == AnalyticsContexts.organization.value:
        context["organization_external_id"] = str(obj.external_id)
        context["organization_id"] = str(obj.id)
    return context


def get_context_mapping(user, instance, mappings, obj):
    context = get_context(user, instance, obj)
    new_context = {}
    for key, value in mappings.items():
        if value.startswith("{{{") and value.endswith("}}}"):
            param = value[3:-3]
            if param not in context:
                raise ValidationError(f"Parameter {param} not found in context")
            new_context[key] = context.get(param)
        else:
            new_context[key] = value
    return new_context


class GenerateAnalyticsUrlRequest(BaseModel):
    context_id: str


class AnalyticsFilters(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")


class AnalyticsViewSet(
    EMRCreateMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
    EMRListMixin,
    EMRDestroyMixin,
    EMRBaseViewSet,
):
    database_model = AnalyticsConfig
    pydantic_model = BaseAnalyticsResource
    filterset_class = AnalyticsFilters
    filter_backends = [
        filters.DjangoFilterBackend,
        OrderingFilter,
    ]
    ordering_fields = ["created_date", "modified_date"]

    def authorize_create(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionDenied(
                "You are not authorized to create analytics configs"
            )
        return super().authorize_create(instance)

    def authorize_update(self, request_obj, model_instance):
        self.authorize_create(request_obj)

    def authorize_destroy(self, instance):
        self.authorize_create(instance)

    @extend_schema(
        request=GenerateAnalyticsUrlRequest,
    )
    @action(detail=True, methods=["POST"])
    def generate_analytics_url(self, request, *args, **kwargs):
        data = GenerateAnalyticsUrlRequest(**request.data)
        instance = self.get_object()
        obj = get_context_object(request.user, instance, data.context_id)
        authorize_analytics_config(request.user, instance, obj)
        mappings = instance.context_mapping
        converted_mappings = get_context_mapping(request.user, instance, mappings, obj)
        handler = AnalyticsHandlerRegistry.get_analytics_handler(instance.handler)()
        return Response(
            {
                "redirect_url": handler.generate_analytics_url(
                    instance, converted_mappings
                )
            }
        )
