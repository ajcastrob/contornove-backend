from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.snippets.models import register_snippet


@register_snippet
class MedioSnippet(models.Model):
    class TendenciaEditorial(models.TextChoices):
        OFICIALISTA = "oficialista", "Oficialista"
        INDEPENDIENTE = "independiente", "Independiente"
        MIXTO = "mixto", "Mixto"

    nombre = models.CharField(max_length=120, unique=True)
    tendencia_editorial = models.CharField(
        max_length=20, choices=TendenciaEditorial.choices
    )
    url_base = models.URLField()
    url_portada = models.URLField()
    selector_titular = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    panels = [
        FieldPanel("nombre"),
        FieldPanel("tendencia_editorial"),
        FieldPanel("url_base"),
        FieldPanel("url_portada"),
        FieldPanel("selector_titular"),
        FieldPanel("activo"),
    ]

    def __str__(self):
        return self.nombre


class ReporteDiarioPage(Page):
    fecha = models.DateField(unique=True)
    contexto_editorial = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("fecha"),
        FieldPanel("contexto_editorial"),
        InlinePanel("titulares", label="Titulares"),
    ]

    subpage_types = []


class TitularOrderable(Orderable):
    reporte = ParentalKey(
        "contornove.ReporteDiarioPage",
        on_delete=models.CASCADE,
        related_name="titulares",
    )
    medio = models.ForeignKey(
        MedioSnippet,
        on_delete=models.PROTECT,
        related_name="titulares",
    )
    titular = models.CharField(max_length=500)
    enlace_original = models.URLField()

    panels = [
        FieldPanel("medio"),
        FieldPanel("titular"),
        FieldPanel("enlace_original"),
    ]

    def __str__(self):
        return f"{self.medio}: {self.titular}"
