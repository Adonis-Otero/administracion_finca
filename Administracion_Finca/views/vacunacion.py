# Administracion_Finca/views/vacunacion.py
import reflex as rx
import backend_vacunacion
import backend_animales

class VacunacionState(rx.State):
    """Gestor de Estado modular para la sanidad y vacunación de la finca."""
    
    # --- Datos de la Jornada de Vacunación ---
    especie_seleccionada: str = "Bovino"
    nombre_vacuna_seleccionada: str = ""
    id_vacuna_seleccionada: int = 0
    catalogo_vacunas_nombres: list[str] = []
    map_vacuna_nombre_a_id: dict[str, int] = {}
    map_vacuna_nombre_a_retiro: dict[str, int] = {}
    
    nro_lote: str = ""
    laboratorio: str = ""
    veterinario: str = ""
    fecha_aplicacion: str = ""
    
    mensaje_alerta: str = ""
    alerta_color: str = "blue"
    dias_retiro_seleccionado: int = 0
    
    # --- Selección de Animales ---
    lista_completa_animales: list[list] = []
    animales_seleccionados: list[int] = []

    # --- Historial y KPIs ---
    historial_vacunacion: list[list] = []
    alertas_sanitarias_count: int = 0
    total_aplicaciones: int = 0

    async def cargar_datos(self):
        """Pobla los datos sanitarios y de animales desde el backend."""
        todos_animales = await rx.run_in_thread(backend_animales.obtener_lista_animales)
        self.lista_completa_animales = todos_animales
        
        historial = await rx.run_in_thread(backend_vacunacion.obtener_historial_vacunacion)
        self.historial_vacunacion = historial
        self.total_aplicaciones = len(historial)
        
        sanitarias = await rx.run_in_thread(backend_animales.obtener_alertas_sanitarias)
        self.alertas_sanitarias_count = sanitarias
        
        await self.cargar_vacunas_por_especie()

    async def cargar_vacunas_por_especie(self):
        """Carga del catálogo las vacunas permitidas para la especie actual."""
        id_esp = 1
        if self.especie_seleccionada == "Bovino": id_esp = 1
        elif self.especie_seleccionada == "Porcino": id_esp = 2
        elif self.especie_seleccionada == "Ovino": id_esp = 3
        
        def operacion_vacunas():
            return backend_vacunacion.obtener_vacunas_por_especie(id_esp)
            
        vacunas = await rx.run_in_thread(operacion_vacunas)
        
        self.map_vacuna_nombre_a_id = {v['nombre_enfermedad']: v['id_vacuna'] for v in vacunas}
        self.map_vacuna_nombre_a_retiro = {v['nombre_enfermedad']: v['dias_retiro'] for v in vacunas}
        self.catalogo_vacunas_nombres = list(self.map_vacuna_nombre_a_id.keys())
        
        if self.catalogo_vacunas_nombres:
            self.nombre_vacuna_seleccionada = self.catalogo_vacunas_nombres[0]
            self.id_vacuna_seleccionada = self.map_vacuna_nombre_a_id[self.nombre_vacuna_seleccionada]
            self.dias_retiro_seleccionado = self.map_vacuna_nombre_a_retiro.get(self.nombre_vacuna_seleccionada, 0)
        else:
            self.nombre_vacuna_seleccionada = ""
            self.id_vacuna_seleccionada = 0
            self.dias_retiro_seleccionado = 0

    async def cambiar_especie(self, valor: str):
        self.especie_seleccionada = valor
        self.animales_seleccionados = []
        await self.cargar_vacunas_por_especie()

    def cambiar_vacuna(self, valor: str):
        self.nombre_vacuna_seleccionada = valor
        self.id_vacuna_seleccionada = self.map_vacuna_nombre_a_id.get(valor, 0)
        self.dias_retiro_seleccionado = self.map_vacuna_nombre_a_retiro.get(valor, 0)

    def cambiar_nro_lote(self, valor: str): self.nro_lote = valor.upper()
    def cambiar_laboratorio(self, valor: str): self.laboratorio = valor
    def cambiar_veterinario(self, valor: str): self.veterinario = valor
    def cambiar_fecha_aplicacion(self, valor: str): self.fecha_aplicacion = valor

    def toggle_seleccion(self, id_animal: int):
        if id_animal in self.animales_seleccionados:
            self.animales_seleccionados.remove(id_animal)
        else:
            self.animales_seleccionados.append(id_animal)

    def seleccionar_todos(self):
        for a in self.lista_animales_especie:
            if len(a) > 0:
                anim_id = int(a[0])
                if anim_id not in self.animales_seleccionados:
                    self.animales_seleccionados.append(anim_id)

    def deseleccionar_todos(self):
        for a in self.lista_animales_especie:
            if len(a) > 0:
                anim_id = int(a[0])
                if anim_id in self.animales_seleccionados:
                    self.animales_seleccionados.remove(anim_id)

    @rx.var
    def lista_animales_especie(self) -> list[list]:
        return [a for a in self.lista_completa_animales if len(a) > 2 and a[2] == self.especie_seleccionada]

    @rx.var
    def animales_con_seleccion(self) -> list[dict]:
        res = []
        for a in self.lista_animales_especie:
            anim_id = int(a[0])
            is_sel = anim_id in self.animales_seleccionados
            res.append({
                "id": anim_id,
                "codigo": a[1],
                "categoria": a[5],
                "sexo": a[4],
                "seleccionado": is_sel
            })
        return res

    @rx.var
    def semaforo_sanitario(self) -> str:
        if self.alertas_sanitarias_count > 5: return "rojo"
        elif self.alertas_sanitarias_count > 0: return "amarillo"
        return "verde"

    async def registrar_jornada(self):
        if not self.id_vacuna_seleccionada:
            self.mensaje_alerta = "Error: Por favor, elija una vacuna válida del catálogo."
            self.alerta_color = "red"
            return
        if not self.nro_lote or not self.laboratorio or not self.veterinario or not self.fecha_aplicacion:
            self.mensaje_alerta = "Por favor, complete todos los campos informativos de la vacuna."
            self.alerta_color = "red"
            return
        if not self.animales_seleccionados:
            self.mensaje_alerta = "Error: Debe seleccionar al menos un animal de la tabla para aplicar la vacuna."
            self.alerta_color = "red"
            return

        def operacion_bd():
            return backend_vacunacion.registrar_vacunacion_lote(
                list(self.animales_seleccionados),
                self.id_vacuna_seleccionada,
                self.nro_lote.strip(),
                self.laboratorio.strip(),
                self.veterinario.strip(),
                self.fecha_aplicacion
            )

        try:
            exito, msg = await rx.run_in_thread(operacion_bd)
            self.mensaje_alerta = msg
            if exito:
                self.alerta_color = "green"
                self.nro_lote = ""
                self.laboratorio = ""
                self.veterinario = ""
                self.fecha_aplicacion = ""
                self.animales_seleccionados = []
                await self.cargar_datos()
            else:
                self.alerta_color = "red"
        except Exception as error:
            print(f"Error al registrar vacuna: {error}")
            self.mensaje_alerta = f"Frontend Exception (registrar_jornada): {str(error)}"
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


# --- Componentes Visuales ---

def kpi_card_sanidad(titulo: str, valor: str, estado: str, subtitulo: str) -> rx.Component:
    """Tarjeta de KPI para control sanitario."""
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

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.cond(estado == "verde", rx.icon("circle-check", color="#4ade80", size=20)),
                rx.cond(estado == "amarillo", rx.icon("triangle-alert", color="#fbbf24", size=20)),
                rx.cond(estado == "rojo", rx.icon("circle-alert", color="#f87171", size=20)),
                rx.text(titulo, font_size="0.95em", weight="bold", color=_text_muted),
                spacing="2", align="center",
            ),
            rx.heading(valor, size="6", margin_y="4px", color=color_heading),
            rx.text(subtitulo, font_size="0.75em", color=_text_sub),
            align="start", spacing="1"
        ),
        border_left=f"5px solid {color_border}",
        background_color=color_bg,
        border_radius="lg",
        box_shadow="lg",
        padding="16px",
        width="100%",
    )


def elemento_tabla_seleccion(animal: rx.Var[dict]) -> rx.Component:
    """Fila de selección de animal para vacunación."""
    return rx.table.row(
        rx.table.cell(animal["id"].to_string(), color=_text_muted),
        rx.table.cell(animal["codigo"], font_weight="bold", color=_text_main),
        rx.table.cell(
            rx.badge(
                animal["sexo"],
                color_scheme=rx.cond(animal["sexo"] == "M", "blue", "pink"),
                variant="soft"
            )
        ),
        rx.table.cell(rx.badge(animal["categoria"], color_scheme="teal")),
        rx.table.cell(
            rx.cond(
                animal["seleccionado"],
                rx.button(
                    "Seleccionado",
                    on_click=lambda: VacunacionState.toggle_seleccion(animal["id"]),
                    color_scheme="green",
                    size="1"
                ),
                rx.button(
                    "Seleccionar",
                    on_click=lambda: VacunacionState.toggle_seleccion(animal["id"]),
                    color_scheme="gray",
                    size="1",
                    variant="outline"
                )
            )
        )
    )


def elemento_tabla_historial(vacuna: rx.Var[list]) -> rx.Component:
    """Fila para la tabla de historial de vacunaciones aplicadas."""
    return rx.table.row(
        rx.table.cell(vacuna[0].to_string(), color=_text_muted),
        rx.table.cell(vacuna[1], font_weight="bold", color=_text_main),
        rx.table.cell(vacuna[2], color=rx.color_mode_cond(light="#1d4ed8", dark="#60a5fa")),
        rx.table.cell(vacuna[3], color=_text_sub),
        rx.table.cell(
            rx.cond(
                vacuna[4] != "",
                rx.badge(vacuna[4], color_scheme="purple", variant="solid"),
                rx.badge("Dosis Única", color_scheme="gray")
            )
        ),
        rx.table.cell(vacuna[5], color=_text_sub),
        rx.table.cell(vacuna[6], color=_text_sub),
        rx.table.cell(vacuna[7], color=_text_muted)
    )


def vacunacion_view() -> rx.Component:
    """Vista principal para el control de Sanidad y Campañas de Vacunación."""
    return rx.vstack(
        # --- Cabecera y KPIs Sanitarios ---
        rx.heading("Estatus Sanitario y Campañas Colectivas", size="4", color=_text_main, margin_top="10px"),
        rx.grid(
            kpi_card_sanidad("Controles Aplicados", VacunacionState.total_aplicaciones.to_string(), "verde", "Historial total dosis aplicadas"),
            kpi_card_sanidad("Alertas Sanitarias", VacunacionState.alertas_sanitarias_count.to_string(), VacunacionState.semaforo_sanitario, "Cabezas con dosis vencida"),
            columns="2",
            spacing="4",
            width="100%",
            margin_bottom="10px"
        ),

        # --- Alertas ---
        rx.cond(
            VacunacionState.mensaje_alerta != "",
            rx.hstack(
                rx.callout(
                    VacunacionState.mensaje_alerta,
                    icon=rx.cond(VacunacionState.alerta_color == "green", "check", "info"),
                    color_scheme=VacunacionState.alerta_color,
                    flex="1",
                    variant="surface"
                ),
                rx.button(
                    rx.icon("x"),
                    on_click=VacunacionState.limpiar_alerta,
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

        # --- Área de Trabajo ---
        rx.hstack(
            # Columna Izquierda: Formulario
            rx.card(
                rx.vstack(
                    rx.heading("Registrar Jornada de Vacunación", size="3", color=_text_main),
                    rx.text("Registra la aplicación de vacunas en lote para la trazabilidad oficial del INSAI", font_size="0.8em", color=_text_muted),

                    rx.text("Especie Destino", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.select(
                        ["Bovino", "Porcino", "Ovino"],
                        value=VacunacionState.especie_seleccionada,
                        on_change=VacunacionState.cambiar_especie,
                        width="100%",
                    ),

                    rx.text("Vacuna (Catálogo INSAI)", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.select(
                        VacunacionState.catalogo_vacunas_nombres,
                        value=VacunacionState.nombre_vacuna_seleccionada,
                        on_change=VacunacionState.cambiar_vacuna,
                        width="100%",
                    ),
                    # Alerta de Período de Retiro
                    rx.cond(
                        VacunacionState.dias_retiro_seleccionado > 0,
                        rx.hstack(
                            rx.icon("info", color="#fbbf24", size=16),
                            rx.text(
                                f"Período de retiro: {VacunacionState.dias_retiro_seleccionado} días. No destinar leche/carne a consumo humano.",
                                font_size="0.75em",
                                color="#fb923c",
                                weight="bold"
                            ),
                            spacing="1",
                            align="center",
                            margin_top="-2px"
                        )
                    ),

                    rx.text("Número de Lote Comercial", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.input(
                        placeholder="Ej. LOT-AFF-40",
                        value=VacunacionState.nro_lote,
                        on_change=VacunacionState.cambiar_nro_lote,
                        width="100%",
                        background_color=_input_bg,
                    ),

                    rx.hstack(
                        rx.vstack(
                            rx.text("Laboratorio", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.input(placeholder="Ej. Bayer", value=VacunacionState.laboratorio, on_change=VacunacionState.cambiar_laboratorio, width="100%", background_color=_input_bg),
                            align_items="start", width="50%"
                        ),
                        rx.vstack(
                            rx.text("Veterinario", weight="bold", font_size="0.85em", color=_text_sub),
                            rx.input(placeholder="Ej. Dr. Pérez", value=VacunacionState.veterinario, on_change=VacunacionState.cambiar_veterinario, width="100%", background_color=_input_bg),
                            align_items="start", width="50%"
                        ),
                        width="100%"
                    ),

                    rx.text("Fecha de Aplicación", weight="bold", font_size="0.85em", color=_text_sub),
                    rx.input(
                        type="date",
                        value=VacunacionState.fecha_aplicacion,
                        on_change=VacunacionState.cambiar_fecha_aplicacion,
                        width="100%",
                        background_color=_input_bg,
                    ),

                    rx.button(
                        "Registrar Jornada Veterinaria",
                        on_click=VacunacionState.registrar_jornada,
                        color_scheme="green",
                        width="100%",
                        margin_top="10px",
                        cursor="pointer"
                    ),
                    spacing="3",
                    align_items="start",
                ),
                background_color=_card_bg,
                border=_card_border,
                width="380px",
                padding="20px",
            ),

            # Columna Derecha: Selector de Animales
            rx.card(
                rx.vstack(
                    rx.heading("Seleccionar Semovientes del Lote", size="3", color=_text_main),
                    rx.text(
                        f"Muestra los animales activos de tipo '{VacunacionState.especie_seleccionada}'. Selecciona los ejemplares vacunados.",
                        font_size="0.8em",
                        color=_text_muted,
                        margin_bottom="10px"
                    ),
                    rx.hstack(
                        rx.button("Seleccionar Todos", on_click=VacunacionState.seleccionar_todos, color_scheme="blue", variant="soft", size="1", cursor="pointer"),
                        rx.button("Deseleccionar Todos", on_click=VacunacionState.deseleccionar_todos, color_scheme="gray", variant="soft", size="1", cursor="pointer"),
                        spacing="2",
                        margin_bottom="10px"
                    ),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ID", color=_text_muted),
                                rx.table.column_header_cell("Código", color=_text_muted),
                                rx.table.column_header_cell("Sexo", color=_text_muted),
                                rx.table.column_header_cell("Categoría", color=_text_muted),
                                rx.table.column_header_cell("Acción", color=_text_muted),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                VacunacionState.animales_con_seleccion,
                                elemento_tabla_seleccion
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

        # --- Historial de Vacunación ---
        rx.card(
            rx.vstack(
                rx.heading("Histórico de Aplicaciones Veterinarias", size="3", color=_text_main, margin_bottom="10px"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Reg", color=_text_muted),
                            rx.table.column_header_cell("Semoviente", color=_text_muted),
                            rx.table.column_header_cell("Vacuna / Enfermedad", color=_text_muted),
                            rx.table.column_header_cell("Aplicación", color=_text_muted),
                            rx.table.column_header_cell("Próxima Agenda", color=_text_muted),
                            rx.table.column_header_cell("Lote Comercial", color=_text_muted),
                            rx.table.column_header_cell("Laboratorio", color=_text_muted),
                            rx.table.column_header_cell("Veterinario", color=_text_muted),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            VacunacionState.historial_vacunacion,
                            elemento_tabla_historial
                        )
                    ),
                    width="100%",
                    variant="surface",
                ),
                width="100%",
            ),
            background_color=_card_bg,
            border=_card_border,
            width="100%",
            padding="20px",
            margin_top="10px",
        ),
        spacing="4",
        width="100%"
    )
