from wagtail.api.v2.router import WagtailAPIRouter

from apps.contornove.api import MediosAPIViewSet, ReportesAPIViewSet


api_router = WagtailAPIRouter("contornoveapi")
api_router.register_endpoint("medios", MediosAPIViewSet)
api_router.register_endpoint("reportes", ReportesAPIViewSet)
