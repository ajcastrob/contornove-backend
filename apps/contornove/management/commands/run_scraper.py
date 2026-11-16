from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from wagtail.models import Page
from apps.contornove.models import (
    MedioSnippet,
    ReporteDiarioPage,
    TitularOrderable,
)


def extraer_titulares(html, medio):
    soup = BeautifulSoup(html, "html.parser")
    titulares = []
    urls_vistas = set()

    for enlace in soup.select(medio.selector_titular):
        titulo = " ".join(enlace.stripped_strings)
        url = urljoin(medio.url_base, enlace.get("href", ""))

        if not titulo or not url.startswith(("https://", "http://")):
            continue

        if url in urls_vistas:
            continue

        urls_vistas.add(url)
        titulares.append(
            {
                "titular": titulo,
                "enlace_original": url,
            }
        )

        if len(titulares) == 8:
            break

    return titulares


def obtener_o_crear_reporte(fecha):
    reporte = ReporteDiarioPage.objects.filter(fecha=fecha).first()

    if reporte:
        return reporte, False

    raiz = Page.get_first_root_node()
    reporte = raiz.add_child(
        instance=ReporteDiarioPage(
            title=f"Reporte diario — {fecha.isoformat()}",
            slug=f"reporte-{fecha.isoformat()}",
            fecha=fecha,
            live=False,
        )
    )

    return reporte, True


class Command(BaseCommand):
    help = "Obtiene titulares y actualiza un borrador sin publicarlo."

    def handle(self, *args, **options):
        medios = MedioSnippet.objects.filter(activo=True)

        if not medios.exists():
            self.stdout.write(self.style.WARNING("No hay medios activos."))
            return

        fecha = timezone.localdate()
        reporte, creado = obtener_o_crear_reporte(fecha)

        if creado:
            self.stdout.write(f"Borrador creado: {reporte.title}")
        else:
            self.stdout.write(f"Borrador reutilizado: {reporte.title}")

        exitosos = 0
        fallidos = 0
        titulares_extraidos = []

        for medio in medios:
            try:
                response = requests.get(
                    medio.url_portada,
                    timeout=15,
                    headers={"User-Agent": "ContornoVE/0.1"},
                )
                response.raise_for_status()
            except requests.RequestException as error:
                self.stderr.write(f"{medio.nombre}: {error}")
                fallidos += 1
                continue

            titulares = extraer_titulares(response.text, medio)

            if not titulares:
                self.stderr.write(f"{medio.nombre}: no devolvió titulares válidos.")
                fallidos += 1
                continue

            exitosos += 1

            self.stdout.write(f"{medio.nombre}: {len(titulares)} titulares válidos")

            for item in titulares:
                item["medio"] = medio
                titulares_extraidos.append(item)

                self.stdout.write(f"- {item['titular']} → {item['enlace_original']}")

        if titulares_extraidos:
            with transaction.atomic():
                reporte.titulares.all().delete()

                TitularOrderable.objects.bulk_create(
                    [
                        TitularOrderable(
                            reporte=reporte,
                            medio=item["medio"],
                            titular=item["titular"],
                            enlace_original=item["enlace_original"],
                            sort_order=posicion,
                        )
                        for posicion, item in enumerate(titulares_extraidos)
                    ]
                )
                reporte = ReporteDiarioPage.objects.get(pk=reporte.pk)
                reporte.save_revision()

            self.stdout.write(
                self.style.SUCCESS(
                    f"{len(titulares_extraidos)} titulares guardados en el borrador."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "No se guardaron titulares; se conserva el borrador existente."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Portadas procesadas: {exitosos}; fallidas: {fallidos}."
            )
        )
