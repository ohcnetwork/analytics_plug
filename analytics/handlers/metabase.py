import os
import time

import jwt

from analytics.handlers.base import AnalyticsHandlerBase
from analytics.registry import AnalyticsHandlerRegistry

METABASE_SITE_URL = os.getenv("METABASE_SITE_URL")
METABASE_SECRET_KEY = os.getenv("METABASE_SECRET_KEY")


class MetabaseHandler(AnalyticsHandlerBase):
    code = "metabase"

    def perform_validation(self, handler_args):
        if "dashboard_id" not in handler_args:
            raise ValueError("dashboard_id is required")

    def generate_analytics_url(self, instance, mappings):
        payload = {
            "resource": {"dashboard": instance.handler_args["dashboard_id"]},
            "params": mappings,
            "exp": round(time.time()) + (60 * 10),  # 10 minute expiration
        }
        token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

        return (
            METABASE_SITE_URL
            + "/embed/dashboard/"
            + token
            + "#bordered=true&titled=true"
        )


AnalyticsHandlerRegistry.register(MetabaseHandler)
