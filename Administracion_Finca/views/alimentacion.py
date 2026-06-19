# Administracion_Finca/views/alimentacion.py
import reflex as rx
import re
import backend_alimentacion

class AlimentacionState(rx.State):
    """Gestor de Estado modular para la alimentación y finanzas de la finca."""
    
    # --- Configuración Financiera ---
    costo_por_kg: str = "0.50"
    
    # --- KPIs Proyectados ---
    total_kg: float = 0.0
    costo_diario_usd: float = 0.0
    costo_mensual_usd: float = 0.0
    
    # --- Datos de los Animales ---
    lista_detalle_alimentacion: list[list] = []
    
    # --- Alertas ---
    mensaje_alerta: str = ""
    alerta_color: str = "blue"
    
    # --- Modal de Edición ---
    dialogo_abierto: bool = False
    id_animal_seleccionado: int = 0
    codigo_animal_seleccionado: str = ""
    nuevo_tipo_alimento: str = ""

    async def cargar_datos(self):
        """Pobla los datos financieros y de alimentación desde el backend."""
        try:
            costo_val = float(self.costo_por_kg) if self.costo_por_kg else 0.0
        except ValueError:
            costo_val = 0.50
            
        def operacion_totales():
            return backend_alimentacion.calcular_totales_alimentacion_finca(costo_val)
            
        def operacion_detalles():
            return backend_alimentacion.obtener_detalle_alimentacion_animales()
            
        totales = await rx.run_in_thread(operacion_totales)
        self.total_kg = totales.get("total_kg", 0.0)
        self.costo_diario_usd = totales.get("costo_diario_usd", 0.0)
        self.costo_mensual_usd = totales.get("costo_mensual_usd", 0.0)
        
        detalles = await rx.run_in_thread(operacion_detalles)
        self.lista_detalle_alimentacion = detalles

    async def cambiar_costo(self, valor: str):
        if valor == "":
            self.costo_por_kg = ""
            return
        patron = r"^\d*\.?\d{0,2}$"
        if re.match(patron, valor):
            self.costo_por_kg = valor
            if not valor.endswith('.'):
                await self.cargar_datos()

    def abrir_editor_dieta(self, id_animal: int, codigo: str, dieta_actual: str):
        self.id_animal_seleccionado = id_animal
        self.codigo_animal_seleccionado = codigo
        self.nuevo_tipo_alimento = dieta_actual
        self.dialogo_abierto = True

    def cerrar_editor_dieta(self):
        self.dialogo_abierto = False

    def cambiar_nuevo_tipo_alimento(self, valor: str):
        self.nuevo_tipo_alimento = valor

    async def guardar_dieta(self):
        if not self.nuevo_tipo_alimento.strip():
            self.mensaje_alerta = "El tipo de alimento o dieta no puede estar vacío."
            self.alerta_color = "red"
            return
            
        def operacion_bd():
            return backend_alimentacion.registrar_tipo_alimento(
                self.id_animal_seleccionado, 
                self.nuevo_tipo_alimento.strip()
            )
            
        exito = await rx.run_in_thread(operacion_bd)
        
        if exito:
            self.mensaje_alerta = f"¡Dieta del semoviente {self.codigo_animal_seleccionado} actualizada exitosamente!"
            self.alerta_color = "green"
            self.dialogo_abierto = False
            await self.cargar_datos()
        else:
            self.mensaje_alerta = "Error al actualizar la dieta del animal en la base de datos."
            self.alerta_color = "red"

    def limpiar_alerta(self):
        self.mensaje_alerta = ""


# --- Tokens de color semánticos ---
_card_bg    = rx.color_mode_cond(light="#ffffff",  dark="#1f2937")
_card_border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151")
_input_bg   = rx.color_mode_cond(light="#f8fafc",  dark="#374151")
_text_main  = rx.color_mode_cond(light="#0f172a",  dark="#ffffff")
_text_muted = rx.color_mode_cond(light="#64748b",  dark="#9ca3af")
_text_sub   = rx.color_mode_cond(light="#475569",  dark="#e5e7eb")
_info_bg    = rx.color_mode_cond(light="#eff6ff",  dark="#1e3a8a")
_info_border = rx.color_mode_cond(light="1px solid #bfdbfe", dark="1px solid #1d4ed8")
_info_text  = rx.color_mode_cond(light="#1e40af",  dark="#60a5fa")
_info_body  = rx.color_mode_cond(light="#374151",  dark="#d1d5db")


# --- Componentes Visuales ---

def kpi_card_alimentacion(titulo: str, valor: str, icono: str, color_badge: str, subtitulo: str) -> rx.Component:
    """Tarjeta de KPI premium con colores temáticos para la gestión financiera."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icono, color=color_badge, size=22),
                rx.text(titulo, font_size="0.95em", weight="bold", color=_text_muted),
                spacing="2", align="center",
            ),
            rx.heading(valor, size="6", margin_y="4px", color=_text_main),
            rx.text(subtitulo, font_size="0.75em", color=_text_sub),
            align="start", spacing="1"
        ),
        border_left=f"5px solid {color_badge}",
        background_color=_card_bg,
        border_radius="lg",
        box_shadow="lg",
        padding="16px",
        width="100%",
    )


def elemento_tabla_alimentacion(registro: rx.Var[list]) -> rx.Component:
    """Fila para cada animal en la tabla de dieta y alimentación."""
    return rx.table.row(
        rx.table.cell(registro[0].to_string(), color=_text_muted),
        rx.table.cell(registro[1], font_weight="bold", color=_text_main),
        rx.table.cell(registro[2], color=_text_sub),
        rx.table.cell(registro[3].to_string() + " kg", color=rx.color_mode_cond(light="#1d4ed8", dark="#60a5fa")),
        rx.table.cell(registro[4].to_string() + " kg/día", color=rx.color_mode_cond(light="#059669", dark="#10b981")),
        rx.table.cell(
            rx.badge(registro[5], color_scheme="orange", variant="soft")
        ),
        rx.table.cell(
            rx.button(
                "Asignar Dieta",
                on_click=lambda: AlimentacionState.abrir_editor_dieta(
                    registro[0].to(int),
                    registro[1].to(str),
                    registro[5].to(str)
                ),
                color_scheme="orange",
                size="1",
                variant="solid",
                cursor="pointer"
            )
        )
    )


def alimentacion_view() -> rx.Component:
    """Vista principal para la administración de Alimentación y Proyecciones Financieras."""
    return rx.vstack(
        # --- Cabecera e Indicadores de Costos ---
        rx.heading("Consumo de Alimento y Proyecciones Financieras del Rebaño", size="4", color=_text_main, margin_top="10px"),
        rx.grid(
            kpi_card_alimentacion("Consumo Total", AlimentacionState.total_kg.to_string() + " kg", "wheat", "#f59e0b", "Requerimiento diario global"),
            kpi_card_alimentacion("Costo Diario", "$" + AlimentacionState.costo_diario_usd.to_string() + " USD", "dollar-sign", "#10b981", "Gasto diario de mantenimiento"),
            kpi_card_alimentacion("Costo Mensual", "$" + AlimentacionState.costo_mensual_usd.to_string() + " USD", "calendar", "#6366f1", "Proyección financiera a 30 días"),
            columns="3",
            spacing="4",
            width="100%",
            margin_bottom="10px"
        ),

        # --- Notificaciones y Alertas ---
        rx.cond(
            AlimentacionState.mensaje_alerta != "",
            rx.hstack(
                rx.callout(
                    AlimentacionState.mensaje_alerta,
                    icon=rx.cond(AlimentacionState.alerta_color == "green", "check", "info"),
                    color_scheme=AlimentacionState.alerta_color,
                    flex="1",
                    variant="surface"
                ),
                rx.button(
                    rx.icon("x"),
                    on_click=AlimentacionState.limpiar_alerta,
                    color_scheme="gray",
                    variant="soft",
                    cursor="pointer"
                ),
                width="100%",
                align_items="center",
                spacing="2",
                margin_bottom="10px"
            )
        ),

        # --- Área de Trabajo Principal ---
        rx.hstack(
            # Columna Izquierda: Configuración Financiera
            rx.card(
                rx.vstack(
                    rx.heading("Parámetros Financieros", size="3", color=_text_main),
                    rx.text("Ajusta los costos unitarios del alimento para actualizar las proyecciones en tiempo real.", font_size="0.8em", color=_text_muted),

                    rx.text("Costo por Kilogramo ($ USD)", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.input(
                        placeholder="Ej. 0.50",
                        value=AlimentacionState.costo_por_kg,
                        on_change=AlimentacionState.cambiar_costo,
                        width="100%",
                        background_color=_input_bg,
                    ),

                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("info", color=rx.color_mode_cond(light="#2563eb", dark="#3b82f6"), size=16),
                                rx.text("Precisión Financiera", weight="bold", font_size="0.8em", color=_info_text),
                                spacing="1"
                            ),
                            rx.text("Este costo se multiplica directamente por el consumo diario acumulado de cada animal activo en sus registros biométricos.", font_size="0.75em", color=_info_body),
                            spacing="1",
                            align_items="start"
                        ),
                        background_color=_info_bg,
                        border=_info_border,
                        margin_top="10px"
                    ),
                    spacing="3",
                    align_items="start",
                ),
                background_color=_card_bg,
                border=_card_border,
                width="380px",
                padding="20px",
            ),

            # Columna Derecha: Tabla de Dieta de Animales Activos
            rx.card(
                rx.vstack(
                    rx.heading("Dietas y Consumos Individuales", size="3", color=_text_main),
                    rx.text("Lista de semovientes activos y sus correspondientes raciones diarias de alimento.", font_size="0.8em", color=_text_muted, margin_bottom="10px"),

                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ID", color=_text_muted),
                                rx.table.column_header_cell("Código", color=_text_muted),
                                rx.table.column_header_cell("Especie", color=_text_muted),
                                rx.table.column_header_cell("Peso", color=_text_muted),
                                rx.table.column_header_cell("Consumo Diario", color=_text_muted),
                                rx.table.column_header_cell("Dieta Asignada", color=_text_muted),
                                rx.table.column_header_cell("Acción", color=_text_muted),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                AlimentacionState.lista_detalle_alimentacion,
                                elemento_tabla_alimentacion
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                ),
                background_color=_card_bg,
                border=_card_border,
                flex="1",
                padding="20px",
            ),
            width="100%",
            align_items="start",
            spacing="4",
        ),

        # --- Modal para Asignar / Editar Dieta ---
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    rx.dialog.title(f"Asignar Dieta a {AlimentacionState.codigo_animal_seleccionado}", color=_text_main),
                    rx.dialog.description(
                        "Especifique el tipo de alimento o régimen alimenticio (dieta) del animal.",
                        color=_text_muted,
                        font_size="0.85em"
                    ),
                    rx.text("Régimen de Alimentación / Dieta", weight="bold", font_size="0.85em", color=_text_sub, margin_top="10px"),
                    rx.input(
                        placeholder="Ej. Concentrado Proteico / Forraje Verde",
                        value=AlimentacionState.nuevo_tipo_alimento,
                        on_change=AlimentacionState.cambiar_nuevo_tipo_alimento,
                        width="100%",
                        background_color=_input_bg,
                    ),
                    rx.hstack(
                        rx.dialog.close(
                            rx.button("Cancelar", variant="soft", color_scheme="gray", on_click=AlimentacionState.cerrar_editor_dieta, cursor="pointer")
                        ),
                        rx.button("Guardar Dieta", color_scheme="orange", on_click=AlimentacionState.guardar_dieta, cursor="pointer"),
                        spacing="3",
                        margin_top="15px",
                        width="100%",
                        justify="end"
                    ),
                    spacing="3",
                    align_items="start"
                ),
                max_width="450px",
                padding="20px"
            ),
            open=AlimentacionState.dialogo_abierto
        ),
        spacing="4",
        width="100%"
    )
