class AnalyticsHandlerRegistry:
    _analytics_handlers = {}

    @classmethod
    def register(cls, analytics_handler_class) -> None:
        from analytics.handlers.base import AnalyticsHandlerBase

        if not issubclass(analytics_handler_class, AnalyticsHandlerBase):
            raise ValueError(
                "The provided class is not a subclass of AnalyticsHandlerBase"
            )
        cls._analytics_handlers[analytics_handler_class.code] = analytics_handler_class

    @classmethod
    def get_analytics_handler(cls, code):
        if code not in cls._analytics_handlers:
            raise ValueError("Invalid Analytics Handler")
        return cls._analytics_handlers[code]
