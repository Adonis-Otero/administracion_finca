# backend_vacunacion.py
import datetime
from database import obtener_conexion

def obtener_vacunas_por_especie(id_especie):
    """Retorna las vacunas del catálogo permitidas para una especie particular (Evita errores INSAI)."""
    conexion = obtener_conexion()
    if not conexion: return []
    try:
        cursor = conexion.cursor(dictionary=True)
        # 1: Bovino, 2: Porcino, 3: Ovino/Caprino (se mapea con catalogo_vacunas)
        query = "SELECT id_vacuna, nombre_enfermedad, dias_retiro FROM catalogo_vacunas WHERE especie_destino = %s;"
        cursor.execute(query, (id_especie,))
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener catálogo: {e}")
        return []
    finally:
        conexion.close()

def registrar_vacunacion_lote(lista_id_animales, id_vacuna, nro_lote, lab, vet, fecha_app):
    """
    Registra una jornada de vacunación para uno o múltiples animales en lote.
    Calcula de forma automática la fecha de la próxima dosis usando las reglas de negocio.
    """
    conexion = obtener_conexion()
    if not conexion: return False, "Error de conexión."
    cursor = conexion.cursor()
    
    try:
        # 1. Insertar el lote biológico comercial para la trazabilidad legal
        query_lote = """
            INSERT INTO lotes_biologicos (id_vacuna, numero_lote_comercial, laboratorio, veterinario_responsable)
            VALUES (%s, %s, %s, %s);
        """
        cursor.execute(query_lote, (id_vacuna, nro_lote, lab, vet))
        id_lote_generado = cursor.lastrowid

        # 2. Obtener la frecuencia en días de la vacuna para automatizar la agenda
        cursor.execute("SELECT frecuencia_dias FROM catalogo_vacunas WHERE id_vacuna = %s;", (id_vacuna,))
        frecuencia = cursor.fetchone()[0]

        fecha_aplicada = datetime.datetime.strptime(fecha_app, "%Y-%m-%d").date()
        fecha_proxima = fecha_aplicada + datetime.timedelta(days=frecuencia) if frecuencia > 0 else None

        # 3. Insertar el historial para cada animal del lote
        query_registro = """
            INSERT INTO registro_vacunacion (id_animal, id_lote_bio, fecha_aplicacion, fecha_proxima_dosis)
            VALUES (%s, %s, %s, %s);
        """
        datos_transaccion = [(id_anim, id_lote_generado, fecha_aplicada, fecha_proxima) for id_anim in lista_id_animales]
        cursor.executemany(query_registro, datos_transaccion)

        conexion.commit()
        cursor.close()
        return True, "¡Jornada de vacunación registrada exitosamente!"
    except Exception as e:
        conexion.rollback()
        print(f"Error en transacción de vacunas: {e}")
        return False, "Ocurrió un error al procesar el lote sanitario."
    finally:
        conexion.close()

        