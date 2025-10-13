from rest_framework.routers import DefaultRouter

from analytics.analytics_view import AnalyticsViewSet

router = DefaultRouter()
router.register("config", AnalyticsViewSet, basename="config")


urlpatterns = router.urls
