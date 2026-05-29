from database import obtener_conexion

def registrar_animal(numero_identificacion, id_especie, fecha_nacimiento):
    """Inserta un nuevo animal en la base de datos MySQL."""
    sql = """
        INSERT INTO animales (numero_identificacion, id_especie, fecha_nacimiento, id_estado)
        VALUES (%s, %s, %s, 1);
    """
    conexion = obtener_conexion()
    if not conexion: 
        return None
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, (numero_identificacion, id_especie, fecha_nacimiento))
        
        id_generado = cursor.lastrowid  
        
        conexion.commit()
        cursor.close()
        return id_generado
    except Exception as error:
        print(f"Error al registrar en MySQL: {error}")
        conexion.rollback()
        return None
    finally:
        conexion.close()

def obtener_datos_biometricos_ia():
    """Recupera el histórico de pesos para el modelo de IA."""
    sql = """
        SELECT a.numero_identificacion, b.peso_kg, b.consumo_alimento_diario, b.fecha_pesaje
        FROM registros_biometricos b
        JOIN animales a ON b.id_animal = a.id_animal
        ORDER BY b.fecha_pesaje DESC;
    """
    conexion = obtener_conexion()
    if not conexion: return []
    try:
        cursor = conexion.cursor()
        cursor.execute(sql)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as error:
        print(f"Error al obtener datos para IA: {error}")
        return []
    finally:
        conexion.close()

        