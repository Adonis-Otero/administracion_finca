# Administracion_Finca/views/animales.py
import reflex as rx
import re
import backend_animales

class AnimalesState(rx.State):
    """Gestor de Estado modular para la vista de Animales."""
    
    # --- Campos del Formulario de Registro ---
    numero_id: str = ""
    especie_nombre: str = "Bovino"
    sexo: str = "F"
    fecha_nacimiento: str = ""
    peso_inicial: str = ""
    alimento_inicial: str = ""
    mensaje_alerta: str = ""

    # --- KPIs y Contadores ---
    total_animales: int = 0
    bovinos_count: int = 0
    porcinos_count: int = 0
    ovinos_count: int = 0
    alertas_sanitarias_count: int = 0
    alertas_produccion_count: int = 0

    # --- Inventario ---
    lista_completa_animales: list[list] = []
    especie_filtro: str = "Todas"

    async def cargar_datos(self):
        """Consulta los datos del backend en hilos secundarios para poblar la UI."""
        total = await rx.run_in_thread(backend_animales.obtener_total_animales)
        conteo_especie = await rx.run_in_thread(backend_animales.obtener_conteo_por_especie)
        sanitarias = await rx.run_in_thread(backend_animales.obtener_alertas_sanitarias)
        produccion = await rx.run_in_thread(backend_animales.obtener_alertas_produccion)
        dataset = await rx.run_in_thread(backend_animales.obtener_lista_animales)

        self.total_animales = total
        self.bovinos_count = conteo_especie.get("Bovino", 0)
        self.porcinos_count = conteo_especie.get("Porcino", 0)
        self.ovinos_count = conteo_especie.get("Ovino", 0)
        self.alertas_sanitarias_count = sanitarias
        self.alertas_produccion_count = produccion
        self.lista_completa_animales = dataset

    def cambiar_numero_id(self, valor: str):
        self.numero_id = valor.upper()

    def cambiar_especie(self, valor: str):
        self.especie_nombre = valor

    def cambiar_sexo(self, valor: str):
        self.sexo = valor

    def cambiar_fecha_nacimiento(self, valor: str):
        self.fecha_nacimiento = valor

    def cambiar_peso(self, valor: str):
        """Valida que el peso inicial sea un decimal válido (ej. 350.50)."""
        if valor == "":
            self.peso_inicial = ""
            return
        patron = r"^\d*\.?\d{0,2}$"
        if re.match(patron, valor):
            self.peso_inicial = valor

    def cambiar_alimento(self, valor: str):
        """Valida que el consumo de alimento diario sea un decimal válido."""
        if valor == "":
            self.alimento_inicial = ""
            return
        patron = r"^\d*\.?\d{0,2}$"
        if re.match(patron, valor):
            self.alimento_inicial = valor

    def cambiar_filtro(self, valor: str):
        self.especie_filtro = valor

    @rx.var
    def animales_filtrados(self) -> list[list]:
        if self.especie_filtro == "Todas":
            return self.lista_completa_animales
        return [a for a in self.lista_completa_animales if len(a) > 2 and a[2] == self.especie_filtro]

    # --- Semáforos de KPIs ---
    @rx.var
    def semaforo_inventario(self) -> str:
        if self.total_animales < 5: return "rojo"
        elif self.total_animales < 15: return "amarillo"
        return "verde"

    @rx.var
    def semaforo_sanitario(self) -> str:
        if self.alertas_sanitarias_count > 5: return "rojo"
        elif self.alertas_sanitarias_count > 0: return "amarillo"
        return "verde"

    @rx.var
    def semaforo_produccion(self) -> str:
        if self.alertas_produccion_count > 3: return "rojo"
        elif self.alertas_produccion_count > 0: return "amarillo"
        return "verde"

    async def registrar_nuevo_animal(self):
        """Registra un animal con su peso e ingesta de alimento inicial utilizando transacciones en el backend."""
        # Validación de campos
        if not self.numero_id or not self.fecha_nacimiento or not self.peso_inicial or not self.alimento_inicial:
            self.mensaje_alerta = "Todos los campos son obligatorios para el registro inicial."
            return

        # Evitar puntos flotantes inválidos
        if self.peso_inicial.endswith('.') or self.alimento_inicial.endswith('.'):
            self.mensaje_alerta = "Por favor, complete los valores decimales."
            return

        try:
            peso_val = float(self.peso_inicial)
            alimento_val = float(self.alimento_inicial)
        except ValueError as val_err:
            self.mensaje_alerta = f"Form Error (ValueError): Los valores de Peso o Alimento no son números válidos. Detalle: {str(val_err)}"
            return

        def operacion_bd():
            return backend_animales.registrar_animal_completo(
                self.numero_id.strip(),
                self.especie_nombre,
                self.sexo,
                self.fecha_nacimiento,
                peso_val,
                alimento_val
            )

        try:
            exito, msg = await rx.run_in_thread(operacion_bd)
            self.mensaje_alerta = msg
            if exito:
                self.numero_id = ""
                self.fecha_nacimiento = ""
                self.peso_inicial = ""
                self.alimento_inicial = ""
                await self.cargar_datos()
        except Exception as error:
            print(f"Error en registro: {error}")
            self.mensaje_alerta = f"Frontend Exception (registrar_nuevo_animal): {str(error)}"

    async def dar_de_baja_animal(self, id_animal: int, estado: int):
        """Actualiza el estado de un animal en la BD (Muerte o Venta) y actualiza la lista."""
        def operacion_bd():
            # 2: Muerto, 3: Vendido
            exito, msg = backend_animales.actualizar_estado_animal(id_animal, estado)
            return exito, msg

        exito, msg = await rx.run_in_thread(operacion_bd)
        if exito:
            self.mensaje_alerta = f"¡Animal ID {id_animal} dado de baja exitosamente! (Respuesta: {msg})"
            await self.cargar_datos()
        else:
            self.mensaje_alerta = f"Fallo al dar de baja: {msg}"

    def limpiar_alerta(self):
        self.mensaje_alerta = ""


# --- Tokens de color semánticos (se adaptan a modo claro/oscuro) ---
_card_bg   = rx.color_mode_cond(light="#ffffff",  dark="#1f2937")
_card_border = rx.color_mode_cond(light="#e2e8f0", dark="#374151")
_input_bg  = rx.color_mode_cond(light="#f8fafc",  dark="#374151")
_text_main = rx.color_mode_cond(light="#0f172a",  dark="#ffffff")
_text_muted = rx.color_mode_cond(light="#64748b", dark="#9ca3af")
_text_sub  = rx.color_mode_cond(light="#475569",  dark="#e5e7eb")
_text_accent = rx.color_mode_cond(light="#1d4ed8", dark="#60a5fa")


# --- Componentes Visuales ---

def kpi_card(titulo: str, valor: str, estado: str, subtitulo: str) -> rx.Component:
    """Tarjeta de KPI con diseño premium y semáforos integrados."""
    color_border = rx.cond(estado == "verde", "#22c55e", rx.cond(estado == "amarillo", "#fbbf24", "#ef4444"))
    color_bg = rx.cond(
        estado == "verde",
        rx.color_mode_cond(light="#dcfce7", dark="#064e3b"),
        rx.cond(
            estado == "amarillo",
            rx.color_mode_cond(light="#fef9c3", dark="#78350f"),
            rx.color_mode_cond(light="#fee2e2", dark="#7f1d1d")
        )
    )
    color_heading = rx.cond(
        estado == "verde",
        rx.color_mode_cond(light="#15803d", dark="#ffffff"),
        rx.cond(
            estado == "amarillo",
            rx.color_mode_cond(light="#92400e", dark="#ffffff"),
            rx.color_mode_cond(light="#991b1b", dark="#ffffff")
        )
    )
    color_sub = rx.cond(
        estado == "verde",
        rx.color_mode_cond(light="#166534", dark="#d1d5db"),
        rx.cond(
            estado == "amarillo",
            rx.color_mode_cond(light="#78350f", dark="#d1d5db"),
            rx.color_mode_cond(light="#7f1d1d", dark="#d1d5db")
        )
    )
    color_title = rx.cond(
        estado == "verde",
        rx.color_mode_cond(light="#15803d", dark="#9ca3af"),
        rx.cond(
            estado == "amarillo",
            rx.color_mode_cond(light="#92400e", dark="#9ca3af"),
            rx.color_mode_cond(light="#991b1b", dark="#9ca3af")
        )
    )

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.cond(estado == "verde", rx.icon("circle-check", color="#4ade80", size=20)),
                rx.cond(estado == "amarillo", rx.icon("triangle-alert", color="#fbbf24", size=20)),
                rx.cond(estado == "rojo", rx.icon("circle-alert", color="#f87171", size=20)),
                rx.text(titulo, font_size="0.95em", weight="bold", color=color_title),
                spacing="2", align="center",
            ),
            rx.heading(valor, size="6", margin_y="4px", color=color_heading),
            rx.text(subtitulo, font_size="0.75em", color=color_sub),
            align="start", spacing="1"
        ),
        border_left=f"5px solid {color_border}",
        background_color=color_bg,
        border_radius="lg",
        box_shadow="lg",
        padding="16px",
        width="100%",
    )


def elemento_tabla_animal(animal: rx.Var[list]) -> rx.Component:
    """Fila para cada animal en la tabla de inventario general."""
    return rx.table.row(
        rx.table.cell(animal[0].to_string(), color=_text_muted),
        rx.table.cell(animal[1], font_weight="bold", color=_text_main),
        rx.table.cell(animal[2], color=_text_sub),
        rx.table.cell(
            rx.badge(
                animal[4],
                color_scheme=rx.cond(animal[4] == "M", "blue", "pink"),
                variant="soft"
            )
        ),
        rx.table.cell(
            rx.badge(animal[5], color_scheme="teal", variant="solid")
        ),
        rx.table.cell(animal[3], color=_text_muted),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Muerte",
                    on_click=lambda: AnimalesState.dar_de_baja_animal(animal[0].to(int), 2),
                    color_scheme="red",
                    size="1",
                    variant="solid"
                ),
                rx.button(
                    "Venta",
                    on_click=lambda: AnimalesState.dar_de_baja_animal(animal[0].to(int), 3),
                    color_scheme="orange",
                    size="1",
                    variant="solid"
                ),
                spacing="2"
            )
        )
    )


def animales_view() -> rx.Component:
    """Vista principal para la administración de Animales de la finca."""
    return rx.vstack(
        # --- Cabecera de KPIs ---
        rx.heading("Control de Inventario y KPIs Sanitarios", size="4", color=_text_main, margin_top="10px"),
        rx.grid(
            kpi_card("Inventario Activo", AnimalesState.total_animales.to_string(), AnimalesState.semaforo_inventario, "Total cabezas activas"),
            kpi_card("Alertas Sanitarias", AnimalesState.alertas_sanitarias_count.to_string(), AnimalesState.semaforo_sanitario, "Control vacunas vencido"),
            kpi_card("Alertas Producción", AnimalesState.alertas_produccion_count.to_string(), AnimalesState.semaforo_produccion, "Por debajo del umbral"),
            columns="3",
            spacing="4",
            width="100%",
            margin_bottom="10px"
        ),

        # --- Distribución de Especies ---
        rx.card(
            rx.vstack(
                rx.text("Distribución de Rebaño Activo", weight="bold", font_size="0.9em", color=_text_sub),
                rx.hstack(
                    rx.badge(f"Bovinos: {AnimalesState.bovinos_count}", color_scheme="blue", variant="solid", size="2"),
                    rx.badge(f"Porcinos: {AnimalesState.porcinos_count}", color_scheme="orange", variant="solid", size="2"),
                    rx.badge(f"Ovinos: {AnimalesState.ovinos_count}", color_scheme="green", variant="solid", size="2"),
                    spacing="3",
                ),
                align="start", spacing="2"
            ),
            width="100%",
            background_color=_card_bg,
            border=rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151"),
            margin_bottom="15px"
        ),

        # --- Sección Principal de Trabajo (Registro y Tabla) ---
        rx.hstack(
            # Columna izquierda: Registro de ejemplar
            rx.card(
                rx.vstack(
                    rx.heading("Alta Única de Semovientes", size="3", color=_text_main),
                    rx.text("Inicialización completa con métricas biométricas", font_size="0.8em", color=_text_muted),

                    rx.text("Código Identificación Único", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.input(
                        placeholder="Ej. BOV-4021",
                        value=AnimalesState.numero_id,
                        on_change=AnimalesState.cambiar_numero_id,
                        width="100%",
                        background_color=_input_bg,
                    ),

                    rx.hstack(
                        rx.vstack(
                            rx.text("Especie", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.select(["Bovino", "Porcino", "Ovino"], value=AnimalesState.especie_nombre, on_change=AnimalesState.cambiar_especie, width="100%"),
                            align_items="start", width="50%"
                        ),
                        rx.vstack(
                            rx.text("Sexo", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.select(["F", "M"], value=AnimalesState.sexo, on_change=AnimalesState.cambiar_sexo, width="100%"),
                            align_items="start", width="50%"
                        ),
                        width="100%"
                    ),

                    rx.text("Fecha de Nacimiento", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.input(
                        type="date",
                        value=AnimalesState.fecha_nacimiento,
                        on_change=AnimalesState.cambiar_fecha_nacimiento,
                        width="100%",
                        background_color=_input_bg,
                    ),

                    rx.hstack(
                        rx.vstack(
                            rx.text("Peso Entrada (Kg)", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.input(placeholder="Ej. 350.50", value=AnimalesState.peso_inicial, on_change=AnimalesState.cambiar_peso, width="100%", background_color=_input_bg),
                            align_items="start", width="50%"
                        ),
                        rx.vstack(
                            rx.text("Alimento Inicial (Kg/día)", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.input(placeholder="Ej. 6.20", value=AnimalesState.alimento_inicial, on_change=AnimalesState.cambiar_alimento, width="100%", background_color=_input_bg),
                            align_items="start", width="50%"
                        ),
                        width="100%"
                    ),

                    rx.button(
                        "Registrar e Inicializar Animal",
                        on_click=AnimalesState.registrar_nuevo_animal,
                        color_scheme="green",
                        width="100%",
                        margin_top="10px"
                    ),
                    spacing="3",
                    align_items="start",
                ),
                background_color=_card_bg,
                border=rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151"),
                width="380px",
                padding="20px",
            ),

            # Columna derecha: Inventario general de animales activos
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.heading("Inventario Activo", size="3", color=_text_main),
                        rx.spacer(),
                        rx.select(
                            ["Todas", "Bovino", "Porcino", "Ovino"],
                            value=AnimalesState.especie_filtro,
                            on_change=AnimalesState.cambiar_filtro,
                            size="1"
                        ),
                        width="100%",
                        align_items="center"
                    ),
                    rx.text("Manejo zootécnico y control de bajas en tiempo real", font_size="0.8em", color=_text_muted, margin_bottom="10px"),

                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ID", color=_text_muted),
                                rx.table.column_header_cell("Código", color=_text_muted),
                                rx.table.column_header_cell("Especie", color=_text_muted),
                                rx.table.column_header_cell("Sexo", color=_text_muted),
                                rx.table.column_header_cell("Categoría", color=_text_muted),
                                rx.table.column_header_cell("Nacimiento", color=_text_muted),
                                rx.table.column_header_cell("Dar de Baja", color=_text_muted),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                AnimalesState.animales_filtrados,
                                elemento_tabla_animal
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                ),
                background_color=_card_bg,
                border=rx.color_mode_cond(light="1px solid #e2e8f0", dark="1px solid #374151"),
                flex="1",
                padding="20px",
            ),
            width="100%",
            align_items="start",
            spacing="4",
        ),

        # --- Alertas y Callouts ---
        rx.cond(
            AnimalesState.mensaje_alerta != "",
            rx.hstack(
                rx.callout(
                    AnimalesState.mensaje_alerta,
                    icon="info",
                    color_scheme="blue",
                    flex="1"
                ),
                rx.button(
                    rx.icon("x"),
                    on_click=AnimalesState.limpiar_alerta,
                    color_scheme="gray",
                    variant="soft"
                ),
                width="100%",
                align_items="center",
                spacing="2"
            )
        ),
        spacing="4",
        width="100%"
    )
