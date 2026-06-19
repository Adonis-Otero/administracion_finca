import reflex as rx
import sys
import os
from functools import partial

# Forzar la ruta absoluta del directorio raíz del proyecto
ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_raiz = os.path.abspath(os.path.join(ruta_actual, '..'))

if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)

from Administracion_Finca.views.animales import animales_view, AnimalesState
from Administracion_Finca.views.vacunacion import vacunacion_view, VacunacionState
from Administracion_Finca.views.alimentacion import alimentacion_view, AlimentacionState
from Administracion_Finca.views.ia import ia_view, IAState


@rx.page(route="/", on_load=[IAState.cargar_datos, AnimalesState.cargar_datos, VacunacionState.cargar_datos, AlimentacionState.cargar_datos])
def index() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.heading("Sentinel Agropecuario — Panel Gerencial", size="6", color="#60a5fa"),
            rx.spacer(),
            rx.color_mode.button(),
            background_color=rx.color_mode_cond(light="#f8fafc", dark="#1f2937"),
            padding="16px",
            box_shadow="md",
            width="100%",
            border_bottom=rx.color_mode_cond(
                light="1px solid #e2e8f0",
                dark="1px solid #374151"
            ),
            align="center"
        ),
        rx.center(
            rx.vstack(
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Gestión de Animales", value="tab_animales"),
                        rx.tabs.trigger("Sanidad y Vacunación", value="tab_vacunas"),
                        rx.tabs.trigger("Alimentación y Producción", value="tab_alimentacion"),
                        rx.tabs.trigger("Predicciones e IA", value="tab_ia"),
                        width="100%",
                    ),
                    rx.tabs.content(
                        rx.box(animales_view(), padding_y="15px"),
                        value="tab_animales",
                    ),
                    rx.tabs.content(
                        rx.box(vacunacion_view(), padding_y="15px"),
                        value="tab_vacunas",
                    ),
                    rx.tabs.content(
                        rx.box(alimentacion_view(), padding_y="15px"),
                        value="tab_alimentacion",
                    ),
                    rx.tabs.content(
                        rx.box(ia_view(), padding_y="15px"),
                        value="tab_ia",
                    ),
                    width="100%",
                    default_value="tab_animales"
                ),
                spacing="4", width="1050px", padding_y="3%"
            ),
        ),
        width="100vw",
        min_height="100vh",
        background_color=rx.color_mode_cond(light="#f1f5f9", dark="#111827"),
    )

app = rx.App()
app.add_page(index)