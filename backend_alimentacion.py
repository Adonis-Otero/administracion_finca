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
    if not conexion: return {"total_kg": 0.0, "costo_diario_usd": 0.0, "costo_mensual_usd": 0.0}
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
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
        return {"total_kg": 0.0, "costo_diario_usd": 0.0, "costo_mensual_usd": 0.0}
    finally:
        conexion.close()

def obtener_detalle_alimentacion_animales():
    """Retorna la lista de animales activos con su especie, consumo diario y dieta asignada."""
    conexion = obtener_conexion()
    if not conexion: return []
    try:
        cursor = conexion.cursor()
        query = """
            SELECT a.id_animal, a.numero_identificacion, e.nombre AS especie,
                   COALESCE(rb.peso_kg, 0.0) AS peso_kg,
                   COALESCE(rb.consumo_alimento_diario, 0.0) AS consumo_alimento_diario,
                   a.tipo_alimento
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            LEFT JOIN registros_biometricos rb ON a.id_animal = rb.id_animal 
                AND rb.fecha_pesaje = (
                    SELECT MAX(fecha_pesaje) 
                    FROM registros_biometricos 
                    WHERE id_animal = a.id_animal
                )
            WHERE a.id_estado = 1
            ORDER BY a.id_animal DESC;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        # Convertimos a listas de valores para simplificar el frontend de Reflex
        return [[
            fila[0],
            fila[1],
            fila[2],
            float(fila[3]),
            float(fila[4]),
            fila[5] if fila[5] else "Pasto Natural / Forraje"
        ] for fila in resultados]
    except Exception as e:
        print(f"Error al obtener detalle de alimentacion: {e}")
        return []
    finally:
        conexion.close()

        