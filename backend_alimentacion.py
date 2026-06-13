# backend_alimentacion.py
from database import obtener_conexion

def registrar_tipo_alimento(id_animal, tipo_alimento):
    """Asigna o modifica el tipo de alimento o dieta asignada a un animal."""
    conexion = obtener_conexion()
    if not conexion: return False
    try:
        cursor = conexion.cursor()
        # Asumiendo que agregamos una columna 'tipo_alimento' a la tabla animales o biometría
        sql = "UPDATE animales SET tipo_alimento = %s WHERE id_animal = %s;"
        cursor.execute(sql, (tipo_alimento, id_animal))
        conexion.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error al asignar alimento: {e}")
        return False
    finally:
        conexion.close()

def calcular_totales_alimentacion_finca(costo_por_kg=0.5):
    """
    Calcula la cantidad total de alimento diario consumido por todo el rebaño 
    activo y proyecta el costo financiero de mantenimiento de la finca.
    """
    conexion = obtener_conexion()
    if not conexion: return {"total_kg": 0, "costo_diario_usd": 0}
    try:
        cursor = conexion.cursor(dictionary=True)
        # Sumamos el último consumo diario registrado para cada animal activo (id_estado = 1)
        query = """
            SELECT SUM(rb.consumo_alimento_diario) AS total_kg
            FROM registros_biometricos rb
            INNER JOIN animales a ON rb.id_animal = a.id_animal
            WHERE a.id_estado = 1 AND rb.fecha_pesaje = (
                SELECT MAX(fecha_pesaje) FROM registros_biometricos WHERE id_animal = a.id_animal
            );
        """
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        
        total_kg = float(resultado["total_kg"]) if resultado["total_kg"] else 0.0
        return {
            "total_kg": round(total_kg, 2),
            "costo_diario_usd": round(total_kg * costo_por_kg, 2),
            "costo_mensual_usd": round((total_kg * costo_por_kg) * 30, 2)
        }
    except Exception as e:
        print(f"Error en cálculos de producción: {e}")
        return {"total_kg": 0, "costo_diario_usd": 0}
    finally:
        conexion.close()

        