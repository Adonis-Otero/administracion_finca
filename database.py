import pymysql

def obtener_conexion():
    """Establece y retorna la conexión con la base de datos MySQL."""
    try:
        conexion = pymysql.connect(
            host="localhost",
            user="root",          
            password="",          
            database="finca_db", 
            port=3306,            
            cursorclass=pymysql.cursors.Cursor 
        )
        return conexion
    except Exception as error:
        print(f"Error de conexión a MySQL: {error}")
        return None


        