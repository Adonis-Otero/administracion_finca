# backend_animales.py
import datetime
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

def calcular_categoria_insai(id_especie, sexo, fecha_nacimiento_str):
    """Determina automáticamente la categoría zootécnica oficial exigida por el INSAI."""
    try:
        nacimiento = datetime.datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d").date()
        edad_meses = (datetime.date.today() - nacimiento).days // 30
    except:
        return "Maute"

    if id_especie == 1:  # Bovinos
        if edad_meses < 12: return "Becerro" if sexo == "M" else "Becerra"
        elif edad_meses <= 24: return "Maute"
        else: return "Toro" if sexo == "M" else "Vaca"
    elif id_especie == 3:  # Caprinos u Ovinos
        return "Cordero/Cabrito" if edad_meses < 6 else "Reproductor"
    return "Lechón" if edad_meses < 3 else "Engorde"


def registrar_animal_completo(numero_identificacion, nombre_especie, sexo, fecha_nacimiento, peso_kg, consumo_alimento):
    """
    Registra un animal con todos sus datos obligatorios (incluyendo sexo, categoría INSAI)
    y sus métricas biométricas iniciales en una única transacción.
    """
    conexion = obtener_conexion()
    if not conexion: 
        return False, "Error de conexión con la base de datos."
    
    try:
        cursor = conexion.cursor()
        
        # 1. Buscar el id_especie correspondiente al nombre seleccionado (Mantiene tu lógica funcional)
        sql_especie = "SELECT id_especie FROM especies WHERE nombre = %s;"
        cursor.execute(sql_especie, (nombre_especie,))
        res_especie = cursor.fetchone()
        
        if not res_especie:
            cursor.close()
            return False, f"La especie '{nombre_especie}' no es válida."
        id_especie = res_especie[0]
        
        # 2. Calcular automáticamente la categoría INSAI con la nueva regla de negocio
        categoria = calcular_categoria_insai(id_especie, sexo, fecha_nacimiento)
        
        # 3. Insertar el Animal base con los nuevos campos de control sanitario
        sql_animal = """
            INSERT INTO animales (numero_identificacion, id_especie, sexo, fecha_nacimiento, categoria_insai, id_estado)
            VALUES (%s, %s, %s, %s, %s, 1);
        """
        cursor.execute(sql_animal, (numero_identificacion, id_especie, sexo, fecha_nacimiento, categoria))
        
        # Recuperamos el ID autoincremental asignado al animal
        id_animal_nuevo = cursor.lastrowid
        
        # 4. Insertar inmediatamente sus datos biométricos de entrada
        sql_biometrico = """
            INSERT INTO registros_biometricos (id_animal, peso_kg, consumo_alimento_diario, fecha_pesaje)
            VALUES (%s, %s, %s, CURDATE());
        """
        cursor.execute(sql_biometrico, (id_animal_nuevo, peso_kg, consumo_alimento))
        
        # Si todo se ejecutó sin errores, guardamos los cambios de forma permanente
        conexion.commit()
        cursor.close()
        return True, f"¡Éxito! Animal {numero_identificacion} registrado como '{categoria}' con su peso inicial."
        
    except Exception as error:
        conexion.rollback()  # Deshace todo ante fallas para mantener limpia la BD
        print(f"Error en registro unificado completo: {error}")
        return False, f"DB Error (registrar_animal_completo): {str(error)}"
    finally:
        conexion.close()


def eliminar_animal(id_animal):
    """
    Da de baja un animal en el sistema. Cambia el estado a inactivo (id_estado = 2)
    por motivos de muerte o venta, protegiendo los históricos en la base de datos.
    """
    conexion = obtener_conexion()
    if not conexion: 
        return False
    try:
        cursor = conexion.cursor()
        sql = "UPDATE animales SET id_estado = 2 WHERE id_animal = %s;"
        cursor.execute(sql, (id_animal,))
        conexion.commit()
        cursor.close()
        return True
    except Exception as error:
        print(f"Error al dar de baja el animal: {error}")
        return False
    finally:
        conexion.close()


def obtener_total_animales():
    """Retorna la cantidad total de animales activos."""
    conexion = obtener_conexion()
    if not conexion:
        return 0
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM animales WHERE id_estado = 1;")
        resultado = cursor.fetchone()
        cursor.close()
        return resultado[0] if resultado else 0
    except Exception as error:
        print(f"Error al obtener total de animales: {error}")
        return 0
    finally:
        conexion.close()


def obtener_alertas_sanitarias():
    """Retorna la cantidad de animales activos con vacunas vencidas (alerta sanitaria)."""
    conexion = obtener_conexion()
    if not conexion:
        return 0
    try:
        cursor = conexion.cursor()
        query = """
            SELECT COUNT(DISTINCT rv.id_animal)
            FROM registro_vacunacion rv
            INNER JOIN animales a ON rv.id_animal = a.id_animal
            WHERE a.id_estado = 1 
              AND rv.fecha_proxima_dosis IS NOT NULL 
              AND rv.fecha_proxima_dosis < CURDATE();
        """
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        return resultado[0] if resultado else 0
    except Exception as error:
        print(f"Error al obtener alertas sanitarias: {error}")
        return 0
    finally:
        conexion.close()


def obtener_alertas_produccion():
    """Retorna la cantidad de animales activos con baja producción (peso bajo o consumo insuficiente)."""
    conexion = obtener_conexion()
    if not conexion:
        return 0
    try:
        cursor = conexion.cursor()
        # Definimos baja producción como aquellos animales activos que tengan un peso bajo o consumo insuficiente
        # según su especie, basándonos en el último registro biométrico.
        query = """
            SELECT COUNT(DISTINCT a.id_animal)
            FROM animales a
            INNER JOIN registros_biometricos rb ON a.id_animal = rb.id_animal
            WHERE a.id_estado = 1 
              AND rb.fecha_pesaje = (
                  SELECT MAX(fecha_pesaje) 
                  FROM registros_biometricos 
                  WHERE id_animal = a.id_animal
              )
              AND (
                  (a.id_especie = 1 AND (rb.peso_kg < 150.0 OR rb.consumo_alimento_diario < 2.0)) OR
                  (a.id_especie = 2 AND (rb.peso_kg < 40.0 OR rb.consumo_alimento_diario < 1.0)) OR
                  (a.id_especie = 3 AND (rb.peso_kg < 20.0 OR rb.consumo_alimento_diario < 0.5))
              );
        """
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        return resultado[0] if resultado else 0
    except Exception as error:
        print(f"Error al obtener alertas de producción: {error}")
        return 0
    finally:
        conexion.close()


def obtener_conteo_por_especie():
    """Retorna un diccionario con el conteo de animales activos por especie."""
    conexion = obtener_conexion()
    if not conexion:
        return {}
    try:
        cursor = conexion.cursor()
        query = """
            SELECT e.nombre, COUNT(a.id_animal)
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            WHERE a.id_estado = 1
            GROUP BY e.nombre;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        # Convertimos a diccionario
        conteo = {fila[0]: fila[1] for fila in resultados}
        # Aseguramos que existan las especies principales
        for esp in ["Bovino", "Porcino", "Ovino"]:
            if esp not in conteo:
                conteo[esp] = 0
        return conteo
    except Exception as error:
        print(f"Error al obtener conteo por especie: {error}")
        return {"Bovino": 0, "Porcino": 0, "Ovino": 0}
    finally:
        conexion.close()


def obtener_lista_animales():
    """Retorna la lista de animales activos con su especie, sexo y categoría INSAI."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor()
        query = """
            SELECT a.id_animal, a.numero_identificacion, e.nombre, 
                   DATE_FORMAT(a.fecha_nacimiento, '%Y-%m-%d'), a.sexo, a.categoria_insai
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            WHERE a.id_estado = 1
            ORDER BY a.id_animal DESC;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        # Convertimos las tuplas a listas para Reflex
        return [list(fila) for fila in resultados]
    except Exception as error:
        print(f"Error al obtener lista de animales: {error}")
        return []
    finally:
        conexion.close()


def obtener_datos_biometricos_ia():
    """Retorna los últimos datos biométricos de cada animal activo para el módulo de IA."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    try:
        cursor = conexion.cursor()
        query = """
            SELECT a.id_animal,
                   a.numero_identificacion, 
                   COALESCE(rb.peso_kg, 0.0), 
                   COALESCE(rb.consumo_alimento_diario, 0.0), 
                   DATE_FORMAT(COALESCE(rb.fecha_pesaje, CURDATE()), '%Y-%m-%d')
            FROM animales a
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
        # Convertimos tuplas a listas y nos aseguramos de que peso y consumo sean floats
        return [[fila[0], fila[1], float(fila[2]), float(fila[3]), fila[4]] for fila in resultados]
    except Exception as error:
        print(f"Error al obtener datos biométricos para IA: {error}")
        return []
    finally:
        conexion.close()


def registrar_animal(numero_identificacion, id_especie, fecha_nacimiento):
    """Registra un animal básico en la base de datos con un registro biométrico inicial por defecto."""
    conexion = obtener_conexion()
    if not conexion:
        return None
    try:
        cursor = conexion.cursor()
        categoria = calcular_categoria_insai(id_especie, 'F', fecha_nacimiento)
        sql = """
            INSERT INTO animales (numero_identificacion, id_especie, sexo, fecha_nacimiento, categoria_insai, id_estado)
            VALUES (%s, %s, 'F', %s, %s, 1);
        """
        cursor.execute(sql, (numero_identificacion, id_especie, fecha_nacimiento, categoria))
        id_animal_nuevo = cursor.lastrowid
        
        # Insertamos un registro biométrico por defecto con peso 0 y consumo 0 para evitar fallos en la UI
        sql_biometrico = """
            INSERT INTO registros_biometricos (id_animal, peso_kg, consumo_alimento_diario, fecha_pesaje)
            VALUES (%s, 0.0, 0.0, CURDATE());
        """
        cursor.execute(sql_biometrico, (id_animal_nuevo,))
        
        conexion.commit()
        cursor.close()
        return id_animal_nuevo
    except Exception as error:
        conexion.rollback()
        print(f"Error al registrar animal: {error}")
        return None
    finally:
        conexion.close()


def actualizar_estado_animal(id_animal, nuevo_estado):
    """Actualiza el estado de un animal (ej. 2 para dar de baja)."""
    conexion = obtener_conexion()
    if not conexion:
        return False, "Error de conexión con la base de datos."
    try:
        cursor = conexion.cursor()
        sql = "UPDATE animales SET id_estado = %s WHERE id_animal = %s;"
        cursor.execute(sql, (nuevo_estado, id_animal))
        conexion.commit()
        cursor.close()
        return True, "Estado actualizado exitosamente."
    except Exception as error:
        print(f"Error al actualizar estado del animal: {error}")
        return False, f"DB Error (actualizar_estado_animal): {str(error)}"
    finally:
        conexion.close()



        