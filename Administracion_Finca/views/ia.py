# Administracion_Finca/views/ia.py
import reflex as rx
import backend_animales
import backend_ia

class IAState(rx.State):
    """Gestor de Estado modular para la Inteligencia Artificial y predicciones."""
    
    # --- Datos de la Tabla ---
    datos_biometricos_ia: list[list] = []
    
    # --- Auditoría Clínico-Zootécnica Individual ---
    cargando_auditoria: bool = False
    dialogo_auditoria_abierto: bool = False
    codigo_auditado: str = ""
    resultado_salud: str = ""
    resultado_diagnostico: str = ""
    resultado_requerimiento: str = ""
    
    # --- Reporte Gerencial de la Finca ---
    cargando_gerencial: bool = False
    reporte_generado: bool = False
    reporte_advertencia: str = ""
    reporte_estrategia: str = ""

    async def cargar_datos(self):
        """Consulta los datos biométricos para alimentar la tabla de IA."""
        def operacion_db():
            return backend_animales.obtener_datos_biometricos_ia()
        raw_ia = await rx.run_in_thread(operacion_db)
        self.datos_biometricos_ia = raw_ia

    async def auditar_animal(self, id_animal: int, codigo: str):
        """Dispara el análisis individual del animal conectando con el proveedor de IA."""
        self.codigo_auditado = codigo
        self.dialogo_auditoria_abierto = True
        self.cargando_auditoria = True
        self.resultado_salud = ""
        self.resultado_diagnostico = ""
        self.resultado_requerimiento = ""
        yield
        
        def operacion_ia():
            return backend_ia.generar_diagnostico_ia(id_animal)
            
        exito, resultado = await rx.run_in_thread(operacion_ia)
        
        self.resultado_salud = resultado.get("estado_salud", "alerta").lower()
        self.resultado_diagnostico = resultado.get("diagnostico", "No se pudo compilar el diagnóstico.")
        self.resultado_requerimiento = resultado.get("requerimiento", "Revise la configuración del proveedor de IA en el archivo .env.")
        self.cargando_auditoria = False

    def cerrar_auditoria(self):
        self.dialogo_auditoria_abierto = False

    async def generar_reporte_gerencial(self):
        """Genera el reporte macro de riesgos y producción de la finca."""
        self.reporte_generado = False
        self.cargando_gerencial = True
        self.reporte_advertencia = ""
        self.reporte_estrategia = ""
        yield
        
        def operacion_gerencial():
            return backend_ia.generar_reporte_gerencial_ia()
            
        exito, resultado = await rx.run_in_thread(operacion_gerencial)
        
        self.reporte_advertencia = resultado.get("advertencia_riesgo", "No se pudo generar la advertencia.")
        self.reporte_estrategia = resultado.get("estrategia_produccion", "No se pudo generar la estrategia.")
        self.reporte_generado = True
        self.cargando_gerencial = False


# --- Tokens de color semánticos ---
_card_bg     = rx.color_mode_cond(light="#ffffff",  dark="#1f2937")
_card_border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151")
_text_main   = rx.color_mode_cond(light="#0f172a",  dark="#ffffff")
_text_muted  = rx.color_mode_cond(light="#64748b",  dark="#9ca3af")
_text_sub    = rx.color_mode_cond(light="#475569",  dark="#e5e7eb")

# Tarjeta de riesgo (roja)
_risk_bg     = rx.color_mode_cond(light="#fff1f2",  dark="#7f1d1d")
_risk_border = rx.color_mode_cond(light="1px solid #fca5a5", dark="1px solid #ef4444")
_risk_title  = rx.color_mode_cond(light="#b91c1c",  dark="#f87171")
_risk_text   = rx.color_mode_cond(light="#374151",  dark="#e5e7eb")

# Tarjeta de estrategia (verde)
_strategy_bg     = rx.color_mode_cond(light="#f0fdf4",  dark="#064e3b")
_strategy_border = rx.color_mode_cond(light="1px solid #86efac", dark="1px solid #10b981")
_strategy_title  = rx.color_mode_cond(light="#15803d",  dark="#34d399")
_strategy_text   = rx.color_mode_cond(light="#374151",  dark="#e5e7eb")

# Modal de diagnóstico
_diag_box_bg     = rx.color_mode_cond(light="#f8fafc",  dark="#111827")
_diag_box_border = rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151")
_req_box_bg      = rx.color_mode_cond(light="#f5f3ff",  dark="#2e1065")
_req_box_border  = rx.color_mode_cond(light="1px solid #c4b5fd", dark="1px solid #7c3aed")
_req_text        = rx.color_mode_cond(light="#4c1d95",  dark="#ffffff")


# --- Componentes Visuales ---

def elemento_tabla_ia(registro: rx.Var[list]) -> rx.Component:
    """Fila para cada animal en la tabla de predicciones e IA."""
    id_animal = registro[0].to(int)
    codigo = registro[1].to(str)
    peso_actual = registro[2].to(float)
    consumo = registro[3].to(float)
    fecha_pesaje = registro[4]

    peso_proyectado_30d = (peso_actual + (consumo * 1.8)).to_string()

    return rx.table.row(
        rx.table.cell(codigo, font_weight="bold", color=_text_main),
        rx.table.cell(peso_actual.to_string() + " kg", color=rx.color_mode_cond(light="#1d4ed8", dark="#60a5fa")),
        rx.table.cell(consumo.to_string() + " kg/día", color=_text_sub),
        rx.table.cell(fecha_pesaje, color=_text_muted),
        rx.table.cell(
            rx.badge(peso_proyectado_30d + " kg", color_scheme="purple", variant="solid")
        ),
        rx.table.cell(
            rx.button(
                rx.hstack(
                    rx.icon("brain", size=14),
                    rx.text("Auditar con IA"),
                    spacing="1",
                    align="center"
                ),
                on_click=lambda: IAState.auditar_animal(id_animal, codigo),
                color_scheme="purple",
                size="1",
                variant="solid",
                cursor="pointer"
            )
        )
    )


def ia_view() -> rx.Component:
    """Vista principal para la pestaña de Predicciones y Consultas IA."""
    return rx.vstack(
        # --- BLOQUE 1: Reporte Gerencial de la Finca (Macro) ---
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("chart-bar", color="#a855f7", size=22),
                    rx.heading("Auditoría de Riesgos Colectivos y Estrategia de la Finca", size="3", color=_text_main),
                    spacing="2",
                    align="center"
                ),
                rx.text(
                    "Analiza los costos acumulados y detecta la omisión de vacunas de cumplimiento nacional obligatorio (Fiebre Aftosa) usando modelos de IA.",
                    font_size="0.85em",
                    color=_text_muted
                ),

                rx.cond(
                    ~IAState.reporte_generado,
                    # Estado Inicial
                    rx.center(
                        rx.button(
                            rx.hstack(
                                rx.icon("sparkles", size=18),
                                rx.text("Generar Reporte Gerencial con IA"),
                                spacing="2"
                            ),
                            on_click=IAState.generar_reporte_gerencial,
                            loading=IAState.cargando_gerencial,
                            color_scheme="purple",
                            size="3",
                            margin_y="20px",
                            cursor="pointer"
                        ),
                        width="100%"
                    ),
                    # Reporte Generado
                    rx.vstack(
                        rx.grid(
                            # Tarjeta de Riesgos Sanitarios
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("triangle-alert", color=_risk_title, size=18),
                                        rx.text("Advertencia de Riesgos Sanitarios", weight="bold", font_size="0.9em", color=_risk_title),
                                        spacing="1"
                                    ),
                                    rx.text(IAState.reporte_advertencia, font_size="0.85em", color=_risk_text),
                                    spacing="2",
                                    align_items="start"
                                ),
                                background_color=_risk_bg,
                                border=_risk_border,
                                padding="16px"
                            ),
                            # Tarjeta de Estrategia
                            rx.card(
                                rx.vstack(
                                    rx.hstack(
                                        rx.icon("trending-up", color=_strategy_title, size=18),
                                        rx.text("Estrategia Zootécnica y de Producción", weight="bold", font_size="0.9em", color=_strategy_title),
                                        spacing="1"
                                    ),
                                    rx.text(IAState.reporte_estrategia, font_size="0.85em", color=_strategy_text),
                                    spacing="2",
                                    align_items="start"
                                ),
                                background_color=_strategy_bg,
                                border=_strategy_border,
                                padding="16px"
                            ),
                            columns="2",
                            spacing="4",
                            width="100%",
                            margin_top="15px"
                        ),
                        rx.hstack(
                            rx.spacer(),
                            rx.button(
                                "Volver a Analizar Finca",
                                on_click=IAState.generar_reporte_gerencial,
                                loading=IAState.cargando_gerencial,
                                variant="soft",
                                color_scheme="purple",
                                size="1",
                                cursor="pointer"
                            ),
                            width="100%"
                        ),
                        spacing="2",
                        width="100%"
                    )
                ),
                width="100%",
                spacing="3"
            ),
            background_color=_card_bg,
            border=_card_border,
            padding="20px",
            width="100%",
            margin_bottom="15px"
        ),

        # --- BLOQUE 2: Tabla de Proyecciones e IA Individual ---
        rx.card(
            rx.vstack(
                rx.heading("Predicciones de Peso e Informes Clínicos Individuales", size="3", color=_text_main),
                rx.text(
                    "Monitorea el desarrollo zootécnico y ejecuta auditorías clínicas por Inteligencia Artificial para cada semoviente activo.",
                    font_size="0.85em",
                    color=_text_muted,
                    margin_bottom="10px"
                ),

                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Código Animal", color=_text_muted),
                            rx.table.column_header_cell("Último Peso", color=_text_muted),
                            rx.table.column_header_cell("Consumo Alimento", color=_text_muted),
                            rx.table.column_header_cell("Fecha Pesaje", color=_text_muted),
                            rx.table.column_header_cell("Proyección Peso (30 días)", color="#a855f7"),
                            rx.table.column_header_cell("Auditoría Veterinaria", color=_text_muted),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            IAState.datos_biometricos_ia,
                            elemento_tabla_ia
                        )
                    ),
                    width="100%",
                    variant="surface"
                ),
                width="100%"
            ),
            background_color=_card_bg,
            border=_card_border,
            padding="20px",
            width="100%"
        ),

        # --- Modal para Auditoría Clínica Individual ---
        rx.dialog.root(
            rx.dialog.content(
                rx.cond(
                    IAState.cargando_auditoria,
                    # Cargando
                    rx.center(
                        rx.vstack(
                            rx.spinner(size="3", color="#a855f7"),
                            rx.text("Consultando historial clínico, biometría y reglas INSAI...", color=_text_sub, font_size="0.9em"),
                            rx.text("Esto puede tardar unos segundos dependiendo del proveedor de IA.", color=_text_muted, font_size="0.75em"),
                            spacing="3",
                            align="center",
                            padding_y="30px"
                        ),
                        width="100%"
                    ),
                    # Auditoría Cargada
                    rx.vstack(
                        rx.dialog.title(f"Informe Clínico IA - Animal {IAState.codigo_auditado}", color=_text_main),

                        rx.hstack(
                            rx.text("Estado de Salud:", weight="bold", font_size="0.85em", color=_text_muted),
                            rx.cond(IAState.resultado_salud == "optimo", rx.badge("Óptimo", color_scheme="green", variant="solid")),
                            rx.cond(IAState.resultado_salud == "alerta", rx.badge("Alerta Sanitaria", color_scheme="yellow", variant="solid")),
                            rx.cond(IAState.resultado_salud == "critico", rx.badge("Crítico", color_scheme="red", variant="solid")),
                            spacing="2",
                            align="center"
                        ),

                        # Cuadro de Diagnóstico
                        rx.text("Diagnóstico Detallado:", weight="bold", font_size="0.85em", color=_text_sub, margin_top="10px"),
                        rx.card(
                            rx.text(IAState.resultado_diagnostico, font_size="0.85em", color=_text_sub),
                            background_color=_diag_box_bg,
                            border=_diag_box_border,
                            padding="12px",
                            width="100%"
                        ),

                        # Cuadro de Requerimiento/Acción
                        rx.text("Acción Inmediata Recomendada:", weight="bold", font_size="0.85em", color=_text_sub, margin_top="10px"),
                        rx.card(
                            rx.hstack(
                                rx.icon("zap", color="#a855f7", size=16),
                                rx.text(IAState.resultado_requerimiento, font_size="0.85em", color=_req_text, weight="bold"),
                                spacing="2",
                                align="center"
                            ),
                            background_color=_req_box_bg,
                            border=_req_box_border,
                            padding="12px",
                            width="100%"
                        ),

                        # Botón Cerrar
                        rx.hstack(
                            rx.spacer(),
                            rx.button("Entendido / Cerrar", color_scheme="purple", on_click=IAState.cerrar_auditoria, cursor="pointer"),
                            width="100%",
                            margin_top="15px"
                        ),
                        spacing="3",
                        align_items="start",
                        width="100%"
                    )
                ),
                max_width="550px",
                padding="20px"
            ),
            open=IAState.dialogo_auditoria_abierto
        ),
        spacing="4",
        width="100%"
    )
