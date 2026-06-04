# backend_animales.py
from database import obtener_conexion

def obtener_lista_especies():
    """Devuelve la lista de especies disponibles [(id, nombre), ...] para cargar el combo."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_especie, nombre FROM especies ORDER BY id_especie;")
        resultados = cursor.fetchall()
        cursor.close()
        return resultados  # Devuelve tuplas ej: ((1, 'Bovino'), (2, 'Porcino'))
    except Exception as error:
        print(f"Error al obtener especies: {error}")
        return []
    finally:
        conexion.close()

def registrar_animal_completo(numero_identificacion, nombre_especie, fecha_nacimiento, peso_kg, consumo_alimento):
    """Registra un animal y sus datos biométricos iniciales en un solo paso."""
    conexion = obtener_conexion()
    if not conexion: 
        return False, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor()
        
        # 1. Buscar el id_especie correspondiente al nombre seleccionado (ej. 'Bovino')
        sql_especie = "SELECT id_especie FROM especies WHERE nombre = %s;"
        cursor.execute(sql_especie, (nombre_especie,))
        res_especie = cursor.fetchone()
        
        if not res_especie:
            cursor.close()
            return False, f"La especie '{nombre_especie}' no es válida."
        id_especie = res_especie[0]
        
        # 2. Insertar el Animal base
        sql_animal = """
            INSERT INTO animales (numero_identificacion, id_especie, fecha_nacimiento, id_estado)
            VALUES (%s, %s, %s, 1);
        """
        cursor.execute(sql_animal, (numero_identificacion, id_especie, fecha_nacimiento))
        
        # Recuperamos el ID autoincremental asignado al animal
        id_animal_nuevo = cursor.lastrowid
        
        # 3. Insertar inmediatamente sus datos biométricos de entrada
        sql_biometrico = """
            INSERT INTO registros_biometricos (id_animal, peso_kg, consumo_alimento_diario, fecha_pesaje)
            VALUES (%s, %s, %s, CURDATE());
        """
        cursor.execute(sql_biometrico, (id_animal_nuevo, peso_kg, consumo_alimento))
        
        # Si todo se ejecutó sin errores, guardamos los cambios de forma permanente
        conexion.commit()
        cursor.close()
        return True, f"¡Éxito! Animal {numero_identificacion} registrado con su peso inicial."
        
    except Exception as error:
        conexion.rollback()  # Deshace todo si el código de identificación ya existía
        print(f"Error en registro unificado: {error}")
        return False, "Error: El número de identificación ya existe o los datos son inválidos."
    finally:
        conexion.close()