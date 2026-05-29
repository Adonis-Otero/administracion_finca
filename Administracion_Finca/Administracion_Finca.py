import reflex as rx
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backend_animales

class FormularioAnimalState(rx.State):
    """Maneja los datos del formulario de registro y las respuestas en la interfaz."""
    numero_id: str = ""
    especie_id: str = "1"  
    fecha_nacimiento: str = ""
    mensaje_alerta: str = ""

    def cambiar_numero_id(self, valor: str):
        self.numero_id = valor

    def cambiar_especie_id(self, valor: str):
        self.especie_id = valor

    def cambiar_fecha_nacimiento(self, valor: str):
        self.fecha_nacimiento = valor

    def guardar_registro(self):
         
        if not self.numero_id or not self.fecha_nacimiento:
            self.mensaje_alerta = "Por favor, complete todos los campos obligatorios."
            return

        id_nuevo = backend_animales.registrar_animal(
            self.numero_id, 
            int(self.especie_id), 
            self.fecha_nacimiento
        )

        if id_nuevo:
            self.mensaje_alerta = f"¡Animal {self.numero_id} registrado exitosamente con ID: {id_nuevo}!"
            self.numero_id = ""
            self.fecha_nacimiento = ""
        else:
            self.mensaje_alerta = "Error: El número de identificación ya existe o no hay conexión con la base de datos."

def index() -> rx.Component:
    """Diseño visual de la interfaz de registro de la granja."""
    return rx.center(
        rx.vstack(
            rx.color_mode.button(position="top-right"),
            
            rx.heading("Plataforma de Gestión - Fincas Falcón", size="8", color_scheme="green"),
            rx.text("Registro unificado de animales e inventario base", color="gray"),
            
            rx.card(
                rx.vstack(
                    rx.text("Número de Identificación Único", weight="bold"),
                    rx.input(
                        placeholder="Ej. BOV-4021", 
                        value=FormularioAnimalState.numero_id,
                        on_change=FormularioAnimalState.cambiar_numero_id,
                        width="100%"
                    ),
                    
                    rx.text("Especie", weight="bold"),
                    rx.select(
                        {"1": "Bovino", "2": "Porcino", "3": "Ovino"},
                        value=FormularioAnimalState.especie_id,
                        on_change=FormularioAnimalState.cambiar_especie_id,
                        width="100%"
                    ),
                    
                    rx.text("Fecha de Nacimiento", weight="bold"),
                    rx.input(
                        type="date",
                        value=FormularioAnimalState.fecha_nacimiento,
                        on_change=FormularioAnimalState.cambiar_fecha_nacimiento,
                        width="100%"
                    ),
                    
                    rx.button(
                        "Registrar Animal", 
                        on_click=FormularioAnimalState.guardar_registro,
                        color_scheme="green",
                        width="100%"
                    ),
                    spacing="3",
                    width="400px"
                ),
                padding="24px"
            ),
            
            rx.cond(
                FormularioAnimalState.mensaje_alerta != "",
                rx.callout(
                    FormularioAnimalState.mensaje_alerta,
                    icon="info",
                    color_scheme="blue",
                    width="100%"
                )
            ),
            spacing="5",
            padding_top="5%"
        ),
        width="100vw",
        height="100vh",
        background_color="#f9fafb"
    )

app = rx.App()
app.add_page(index)

