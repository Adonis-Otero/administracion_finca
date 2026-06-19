# backend_ia.py
import json
from database import obtener_conexion
import backend_alimentacion  # Requerido para cruzar los costos financieros de la finca
from ia_provider import get_ia_client

# El cliente y el modelo se obtienen del proveedor configurado en el .env
# Cambia IA_PROVIDER en .env para alternar entre 'lmstudio' (local) y 'gemini' (nube)
try:
    client, _ia_model, _ia_extra = get_ia_client()
except Exception as _ia_err:
    print(f"[IA Provider] ADVERTENCIA: No se pudo inicializar el cliente de IA: {_ia_err}")
    client, _ia_model, _ia_extra = None, "no-provider", {}

def limpiar_y_cargar_json(contenido: str) -> dict:
    """Limpia y extrae de forma robusta un objeto JSON de una cadena de texto."""
    contenido = contenido.strip()
    
    # 1. Quitar bloques de código Markdown (```json o ```) si están presentes al inicio/fin
    if contenido.startswith("```"):
        lineas = contenido.splitlines()
        if len(lineas) >= 2:
            if lineas[0].startswith("```"):
                lineas = lineas[1:]
            if lineas[-1].endswith("```"):
                lineas = lineas[:-1]
            contenido = "\n".join(lineas).strip()
            
    # 2. Extraer el bloque entre el primer '{' y el último '}'
    if "{" in contenido:
        inicio = contenido.find("{")
        fin = contenido.rfind("}") + 1
        contenido = contenido[inicio:fin]
        
    return json.loads(contenido)

# ============================================================================
# BLOQUE 1: DIAGNÓSTICO INDIVIDUAL (Mantiene tu código funcional intacto)
# ============================================================================

def obtener_contexto_clinico(id_animal):
    """
    Consulta la base de datos para compilar la ficha médica y biométrica más reciente
    del animal, incluyendo el estatus de sus vacunas e INSAI.
    """
    conexion = obtener_conexion()
    if not conexion:
        return None
    
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        # 1. Obtener datos del animal y su última biometría
        query_animal = """
            SELECT a.id_animal, a.numero_identificacion, e.nombre AS especie, 
                   a.sexo, a.categoria_insai, a.fecha_nacimiento,
                   b.peso_kg, b.consumo_alimento_diario, b.fecha_pesaje
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            LEFT JOIN registros_biometricos b ON a.id_animal = b.id_animal
            WHERE a.id_animal = %s
            ORDER BY b.fecha_pesaje DESC LIMIT 1;
        """
        cursor.execute(query_animal, (id_animal,))
        animal = cursor.fetchone()
        
        if not animal:
            return None
            
        # 2. Obtener su historial de vacunas aplicadas con el cálculo de vigencia y retiro
        query_vacunas = """
            SELECT cv.nombre_enfermedad, rv.fecha_aplicacion, rv.fecha_proxima_dosis,
                   cv.dias_retiro,
                   IF(rv.fecha_proxima_dosis IS NOT NULL AND rv.fecha_proxima_dosis < CURDATE(), 'VENCIDA', 'VIGENTE') AS estatus_vigencia,
                   IF(DATE_ADD(rv.fecha_aplicacion, INTERVAL cv.dias_retiro DAY) > CURDATE(), 'ACTIVO', 'CUMPLIDO') AS estatus_retiro
            FROM registro_vacunacion rv
            INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio
            INNER JOIN catalogo_vacunas cv ON lb.id_vacuna = cv.id_vacuna
            WHERE rv.id_animal = %s;
        """
        cursor.execute(query_vacunas, (id_animal,))
        vacunas = cursor.fetchall()
        
        cursor.close()
        
        # Estructuramos el historial médico en texto limpio para el prompt de la IA
        historial_vacunas_texto = ""
        en_periodo_retiro = "No"
        
        if vacunas:
            for v in vacunas:
                historial_vacunas_texto += f"- Vacuna: {v['nombre_enfermedad']} | Aplicada: {v['fecha_aplicacion']} | Estatus: {v['estatus_vigencia']}\n"
                if v['estatus_retiro'] == 'ACTIVO' and v['dias_retiro'] > 0:
                    en_periodo_retiro = f"SÍ (Fármaco: {v['nombre_enfermedad']}, requiere {v['dias_retiro']} días de resguardo)"
        else:
            historial_vacunas_texto = "- Ninguna vacuna registrada en el sistema hasta la fecha.\n"
            
        # Unificamos todo el reporte zootécnico (Se corrigió la variable de retorno a minúscula)
        ficha_clinica = {
            "id": animal["numero_identificacion"],
            "especie": animal["especie"],
            "sexo": "Macho" if animal["sexo"] == "M" else "Hembra",
            "categoria": animal["categoria_insai"],
            "nacimiento": animal["fecha_nacimiento"],
            "peso": animal["peso_kg"] if animal["peso_kg"] else "No registrado",
            "alimento": animal["consumo_alimento_diario"] if animal["consumo_alimento_diario"] else "No registrado",
            "historial_vacunas": historial_vacunas_texto,
            "cuarentena_retiro": en_periodo_retiro
        }
        return ficha_clinica
        
    except Exception as error:
        print(f"Error al compilar historial para IA: {error}")
        return None
    finally:
        conexion.close()


def generar_diagnostico_ia(id_animal):
    """
    Extrae la información médica real del animal y consulta a LM Studio 
    para obtener un dictamen experto en formato JSON estricto.
    """
    ficha = obtener_contexto_clinico(id_animal)
    
    if not ficha:
        return False, {
            "estado_salud": "alerta",
            "diagnostico": "No se encontraron datos biométricos suficientes para evaluar al animal.",
            "requerimiento": "Registre el peso inicial y consumo de alimento del animal."
        }

    prompt_usuario = f"""
    Evaluar la siguiente ficha técnica del semoviente:
    - Identificador Único: {ficha['id']}
    - Especie: {ficha['especie']}
    - Clasificación INSAI: {ficha['categoria']}
    - Sexo: {ficha['sexo']}
    - Fecha de Nacimiento: {ficha['nacimiento']}
    - Peso registrado: {ficha['peso']} Kg
    - Consumo de Alimento Diario: {ficha['alimento']} Kg
    
    Historial Sanitario de Vacunación:
    {ficha['historial_vacunas']}
    ¿Se encuentra actualmente en Período de Retiro de Medicamento?: {ficha['cuarentena_retiro']}
    """

    system_prompt = """
    Eres un sistema experto en zootecnia de precisión, medicina veterinaria y normativas del INSAI para el estado Falcón, Venezuela.
    Tu trabajo es analizar la ficha de datos del animal (especie, peso, alimento y vacunas) para auditar su estado productivo y sanitario.
    
    Debes emitir un veredicto técnico respondiendo con un objeto JSON dentro de un bloque de código Markdown (```json ... ```), respetando esta estructura:
    {
        "estado_salud": "optimo/alerta/critico",
        "diagnostico": "Tu análisis conciso. Máximo 20 palabras.",
        "requerimiento": "Acción inmediata recomendada. Máximo 15 palabras."
    }
    
    Reglas:
    1. Sé sumamente breve en cada campo (máximo 20 palabras) para evitar que la respuesta sea truncada.
    2. Responde con el bloque de código JSON completo y cerrado, sin texto adicional fuera del bloque.
    3. Si el animal está en periodo de retiro, el estado_salud DEBE marcarse como mínimo en 'alerta' para evitar comercialización ilegal.
    """

    try:
        if not client:
            raise ConnectionError("El cliente de IA no pudo ser inicializado. Verifica la configuración en el archivo .env.")
        response = client.chat.completions.create(
            model=_ia_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.1,
            **_ia_extra,
        )
        
        contenido_crudo = response.choices[0].message.content.strip()
        resultado_json = limpiar_y_cargar_json(contenido_crudo)
        return True, resultado_json

    except json.JSONDecodeError:
        print(f"Error de formato en el modelo IA. Texto devuelto: {contenido_crudo}")
        return False, {
            "estado_salud": "alerta",
            "diagnostico": "El modelo de IA no pudo estructurar la respuesta en formato JSON correctamente.",
            "requerimiento": f"Proveedor activo: '{_ia_model}'. Verifica la configuración en el archivo .env."
        }
    except Exception as error:
        print(f"Error crítico en la comunicación con la IA: {error}")
        return False, {
            "estado_salud": "critico",
            "diagnostico": f"No se pudo conectar con el proveedor de IA configurado ({_ia_model}).",
            "requerimiento": "Verifica el archivo .env y que el proveedor de IA esté disponible (LM Studio activo o conexión a internet para Gemini)."
        }


# ============================================================================
# BLOQUE 2: REPORTE GERENCIAL DE LA FINCA (Nuevas funciones añadidas)
# ============================================================================

def auditar_riesgos_sanitarios_finca():
    """
    Busca anomalías a nivel global. Específicamente detecta animales activos 
    bovinos que NO cuenten con la vacuna de Fiebre Aftosa obligatoria nacional.
    """
    conexion = obtener_conexion()
    if not conexion: 
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        # Filtra bovinos (id_especie=1) activos (id_estado=1) sin vacuna id=1 (Aftosa)
        query = """
            SELECT a.numero_identificacion, a.categoria_insai 
            FROM animales a 
            WHERE a.id_especie = 1 AND a.id_estado = 1 AND a.id_animal NOT IN (
                SELECT rv.id_animal FROM registro_vacunacion rv
                INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio
                WHERE lb.id_vacuna = 1
            );
        """
        cursor.execute(query)
        alertas = cursor.fetchall()
        cursor.close()
        return alertas
    except Exception as e:
        print(f"Error en auditoría de riesgos de la finca: {e}")
        return []
    finally:
        conexion.close()


def generar_reporte_gerencial_ia():
    """
    Recopila los totales financieros de alimentación y los riesgos de salud colectivos 
    para enviar un informe a LM Studio y obtener directrices macro de producción.
    """
    try:
        # Consumimos los datos calculados matemáticamente desde el módulo de alimentación
        financiero = backend_alimentacion.calcular_totales_alimentacion_finca()
        animales_riesgo = auditar_riesgos_sanitarios_finca()
        
        costo_diario = financiero.get('costo_diario_usd', 0.0)
        costo_mensual = financiero.get('costo_mensual_usd', 0.0)
        total_kg = financiero.get('total_kg', 0.0)
        
        resumen_macro_finca = f"""
        ESTADO OPERATIVO GENERAL DE LA FINCA:
        - Costo Diario en Alimentación del Rebaño: ${costo_diario} USD
        - Costo Mensual Proyectado de Dieta: ${costo_mensual} USD
        - Volumen total de alimento requerido al día: {total_kg} Kg
        - Cantidad de animales sin la vacuna obligatoria del Ciclo Nacional de Fiebre Aftosa: {len(animales_riesgo)} animales.
        """
        
        system_prompt = """
        Eres el consultor zootécnico principal de Inteligencia Artificial del software 'Sentinel Agropecuario', especializado en el estado Falcón, Venezuela.
        Analiza las métricas operativas y los gastos financieros de la finca provistos.
        
        Responde únicamente con un objeto JSON dentro de un bloque de código Markdown (```json ... ```) con la siguiente estructura:
        {
            "advertencia_riesgo": "Tu análisis de riesgos biológicos. Sé breve (máximo 20 palabras).",
            "estrategia_produccion": "Tus recomendaciones zootécnicas para optimizar alimento y costos. Sé breve (máximo 20 palabras)."
        }
        Reemplaza los valores de las llaves con tus análisis. No dejes textos explicativos.
        Asegúrate de cerrar correctamente el bloque JSON y de no incluir texto adicional fuera del bloque de código.
        """

        if not client:
            raise ConnectionError("El cliente de IA no pudo ser inicializado. Verifica la configuración en el archivo .env.")
        response = client.chat.completions.create(
            model=_ia_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": resumen_macro_finca}
            ],
            temperature=0.3,
            **_ia_extra,
        )
        
        contenido_crudo = response.choices[0].message.content.strip()
        resultado_json = limpiar_y_cargar_json(contenido_crudo)
        return True, resultado_json
        
    except json.JSONDecodeError as json_err:
        print(f"Error de formato JSON en reporte gerencial IA: {json_err}. Texto devuelto: {contenido_crudo}")
        return False, {
            "advertencia_riesgo": "Error de formato en el modelo local de IA.",
            "estrategia_produccion": "El modelo local de LM Studio no estructuró la respuesta en formato JSON correcto. Revisa la configuración de LM Studio."
        }
    except Exception as e:
        print(f"Error en reporte gerencial IA: {e}")
        return False, {
            "advertencia_riesgo": "No se pudo generar el análisis predictivo global de riesgos.",
            "estrategia_produccion": "Verifique que la base de datos contenga registros activos y que el servidor de LM Studio en el puerto 1234 esté encendido."
        }

        