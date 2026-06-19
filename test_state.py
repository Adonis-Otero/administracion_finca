import asyncio
import sys
import os

# Forzar la ruta absoluta del directorio raíz del proyecto
ruta_actual = os.path.dirname(os.path.abspath(__file__))
if ruta_actual not in sys.path:
    sys.path.insert(0, ruta_actual)

from Administracion_Finca.views.vacunacion import VacunacionState

async def test():
    try:
        state = VacunacionState()
        print("--- CARGANDO DATOS ---")
        await state.cargar_datos()
        print("Especie seleccionada:", state.especie_seleccionada)
        print("Catálogo de vacunas:", state.catalogo_vacunas_nombres)
        print("Vacuna seleccionada:", state.nombre_vacuna_seleccionada)
        print("ID vacuna seleccionada:", state.id_vacuna_seleccionada)
        print("Días retiro seleccionado:", state.dias_retiro_seleccionado)
        print("Lista completa animales:", state.lista_completa_animales)
        print("Lista animales de la especie:", state.lista_animales_especie)
        print("Animales con selección:", state.animales_con_seleccion)
        
        print("\n--- CAMBIANDO ESPECIE A OVINO ---")
        await state.cambiar_especie("Ovino")
        print("Especie seleccionada:", state.especie_seleccionada)
        print("Catálogo de vacunas:", state.catalogo_vacunas_nombres)
        print("Vacuna seleccionada:", state.nombre_vacuna_seleccionada)
        print("ID vacuna seleccionada:", state.id_vacuna_seleccionada)
        print("Días retiro seleccionado:", state.dias_retiro_seleccionado)
        print("Lista animales de la especie (Ovino):", state.lista_animales_especie)
    except Exception as e:
        print("ERROR EN EJECUCIÓN:", e)

if __name__ == "__main__":
    asyncio.run(test())
