# Administracion_Finca/Administracion_Finca.py
import reflex as rx
import sys
import os
import re  # Importamos la librería de expresiones regulares de Python

# Asegurar rutas para módulos del backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend_animales

# Cargamos la lista de especies desde la Base de Datos al iniciar
ESPECIES_DISPONIBLES = [esp[1] for esp in backend_animales.obtener_lista_especies()]
if not ESPECIES_DISPONIBLES:
    ESPECIES_DISPONIBLES = ["Bovino", "Porcino", "Ovino"]

class FormularioUnificadoState(rx.State):
    """Maneja el estado del formulario con validación y sanitización en tiempo real."""
    numero_id: str = ""
    especie_nombre: str = ESPECIES_DISPONIBLES[0]
    fecha_nacimiento: str = ""
    peso_inicial: str = ""
    alimento_inicial: str = ""
    mensaje_alerta: str = ""

    def cambiar_numero_id(self, valor: str): 
        self.numero_id = valor
        
    def cambiar_especie(self, valor: str): 
        self.especie_nombre = valor
        
    def cambiar_fecha_nacimiento(self, valor: str): 
        self.fecha_nacimiento = valor

    def cambiar_peso(self, valor: str):
        """Permite solo números y hasta dos decimales usando expresiones regulares."""
        # Si el campo está vacío, permitimos limpiar el input
        if valor == "":
            self.peso_inicial = ""
            return
            
        # Expresión regular: permite solo dígitos, opcionalmente un punto, y máximo 2 decimales
        patron = r"^\d*\.?\d{0,2}$"
        if re.match(patron, valor):
            self.peso_inicial = valor

    def cambiar_alimento(self, valor: str):
        """Permite solo números y hasta dos decimales en el consumo de comida."""
        if valor == "":
            self.alimento_inicial = ""
            return
            
        patron = r"^\d*\.?\d{0,2}$"
        if re.match(patron, valor):
            self.alimento_inicial = valor

    def procesar_registro(self):
        # Validación de campos vacíos
        if not self.numero_id or not self.fecha_nacimiento or not self.peso_inicial or not self.alimento_inicial:
            self.mensaje_alerta = "Todos los campos son obligatorios para el alta del animal."
            return

        # Validar que el peso o alimento no terminen en un punto colgado (ej. '450.')
        if self.peso_inicial.endswith('.') or self.alimento_inicial.endswith('.'):
            self.mensaje_alerta = "Por favor, complete el valor decimal o elimine el punto."
            return

        try:
            exito, respuesta = backend_animales.registrar_animal_completo(
                self.numero_id.strip(),
                self.especie_nombre,
                self.fecha_nacimiento,
                float(self.peso_inicial),
                float(self.alimento_inicial)
            )
            
            self.mensaje_alerta = respuesta
            if exito:
                # Limpieza total tras el éxito
                self.numero_id = ""
                self.fecha_nacimiento = ""
                self.peso_inicial = ""
                self.alimento_inicial = ""
                
        except ValueError:
            self.mensaje_alerta = "Error crítico: Los datos numéricos no tienen el formato correcto."

def index() -> rx.Component:
    """Diseño del formulario unificado blindado contra datos inválidos."""
    return rx.center(
        rx.vstack(
            rx.color_mode.button(position="top-right"),
            
            rx.heading("Plataforma de Gestión - Fincas Falcón", size="8", color_scheme="green"),
            rx.text("Alta única de semovientes con inicialización biométrica directa", color="gray"),
            
            rx.card(
                rx.vstack(
                    rx.heading("Registro Único de Entrada", size="4", color_scheme="green"),
                    
                    rx.text("Número de Identificación Único", weight="bold"),
                    rx.input(
                        placeholder="Ej. BOV-1223", 
                        value=FormularioUnificadoState.numero_id,
                        on_change=FormularioUnificadoState.cambiar_numero_id,
                        width="100%"
                    ),
                    
                    rx.text("Especie", weight="bold"),
                    rx.select(
                        ESPECIES_DISPONIBLES,
                        value=FormularioUnificadoState.especie_nombre,
                        on_change=FormularioUnificadoState.cambiar_especie,
                        width="100%"
                    ),
                    
                    rx.text("Fecha de Nacimiento", weight="bold"),
                    rx.input(
                        type="date", 
                        value=FormularioUnificadoState.fecha_nacimiento, 
                        on_change=FormularioUnificadoState.cambiar_fecha_nacimiento, 
                        width="100%"
                    ),
                    
                    rx.text("Peso de Entrada (Kg)", weight="bold"),
                    rx.input(
                        placeholder="Ej. 380.50", 
                        value=FormularioUnificadoState.peso_inicial, 
                        on_change=FormularioUnificadoState.cambiar_peso, 
                        width="100%"
                    ),
                    
                    rx.text("Consumo de Alimento Diario (Kg)", weight="bold"),
                    rx.input(
                        placeholder="Ej. 10.50", 
                        value=FormularioUnificadoState.alimento_inicial, 
                        on_change=FormularioUnificadoState.cambiar_alimento, 
                        width="100%"
                    ),
                    
                    rx.button(
                        "Registrar e Inicializar Animal", 
                        on_click=FormularioUnificadoState.procesar_registro, 
                        color_scheme="green", 
                        width="100%"
                    ),
                    spacing="3",
                    width="420px"
                ),
                padding="24px"
            ),
            
            rx.cond(
                FormularioUnificadoState.mensaje_alerta != "",
                rx.callout(
                    FormularioUnificadoState.mensaje_alerta, 
                    icon="info", 
                    color_scheme="blue", 
                    width="100%"
                )
            ),
            spacing="5",
            padding_top="2%",
            padding_bottom="5%"
        ),
        width="100vw",
        min_height="100vh",
        background_color="#f9fafb"
    )

app = rx.App()
app.add_page(index)