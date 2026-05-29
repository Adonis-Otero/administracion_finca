import pymysql

try:
    conexion = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="finca_db",
        port=3306
    )
    print("¡CONEXIÓN EXITOSA A MYSQL! Todo configurado y listo para trabajar.")
    
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM especies;")
    print(f"Especies en base de datos: {cursor.fetchall()}")
    cursor.close()
    conexion.close()

except Exception as e:
    print(f"❌ Error al conectar a MySQL: {e}")