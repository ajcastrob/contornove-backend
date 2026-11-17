from wagtail.api.v2.views import BaseAPIViewSet, PagesAPIViewSet

from apps.contornove.models import MedioSnippet, ReporteDiarioPage


class MediosAPIViewSet(BaseAPIViewSet):
    name = "medios"
    model = MedioSnippet
    listing_default_fields = [
        "id",
        "nombre",
        "tendencia_editorial",
        "url_base",
    ]

    def get_queryset(self):
        return self.model.objects.filter(activo=True).order_by("nombre")


class ReportesAPIViewSet(PagesAPIViewSet):
    name = "reportes"
    model = ReporteDiarioPage
    listing_default_fields = PagesAPIViewSet.listing_default_fields + [
        "fecha",
    ]
