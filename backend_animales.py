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
        return False, "Error: El número de identificación ya existe o los datos son inválidos."
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


        