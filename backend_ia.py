# backend_ia.py
from openai import OpenAI
import json
from database import obtener_conexion
import backend_alimentacion  # Requerido para cruzar los costos financieros de la finca

# Configuramos el cliente apuntando al servidor local de LM Studio
client = OpenAI(
    base_url="http://localhost:1234/v1",  # Puerto estándar de LM Studio
    api_key="not-needed"                  # No requiere clave real localmente
)

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
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
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
    
    Debes emitir un veredicto técnico respondiendo ÚNICAMENTE en formato JSON plano, respetando esta estructura exacta:
    {
        "estado_salud": "optimo/alerta/critico",
        "diagnostico": "Tu análisis de su relación peso/alimento y si tiene alertas sanitarias críticas en Falcón (ej: Fiebre Aftosa o Rabia vencida, o si está en periodo de retiro).",
        "requerimiento": "Acción inmediata recomendada (ej: ajustar ración alimenticia, aplicar dosis de refuerzo o prohibir venta por residuo biológico)."
    }
    
    Reglas estrictas de salida:
    1. No agregues texto de introducción, saludos ni conclusiones.
    2. Responde puramente el JSON sin usar bloques de código markdown (prohibido usar ```json).
    3. Si el animal está en periodo de retiro, el estado_salud DEBE marcarse como mínimo en 'alerta' para evitar comercialización ilegal.
    """

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.1,
        )
        
        contenido_crudo = response.choices[0].message.content.strip()
        resultado_json = json.loads(contenido_crudo)
        return True, resultado_json

    except json.JSONDecodeError:
        print(f"Error de formato en el modelo local. Texto devuelto: {contenido_crudo}")
        return False, {
            "estado_salud": "alerta",
            "diagnostico": "El modelo local de LM Studio no estructuró la respuesta correctamente.",
            "requerimiento": "Revisar los parámetros de restricción de formato en LM Studio."
        }
    except Exception as error:
        print(f"Error crítico en la comunicación con la IA: {error}")
        return False, {
            "estado_salud": "critico",
            "diagnostico": "El servidor local de Inteligencia Artificial (LM Studio) se encuentra apagado o inaccesible.",
            "requerimiento": "Asegúrate de iniciar el servidor local en el puerto 1234 y verificar la red."
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
    try:
        cursor = conexion.cursor(dictionary=True)
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
    # Consumimos los datos calculados matemáticamente desde el módulo de alimentación
    financiero = backend_alimentacion.calcular_totales_alimentacion_finca()
    animales_riesgo = auditar_riesgos_sanitarios_finca()
    
    resumen_macro_finca = f"""
    ESTADO OPERATIVO GENERAL DE LA FINCA:
    - Costo Diario en Alimentación del Rebaño: ${financiero['costo_diario_usd']} USD
    - Costo Mensual Proyectado de Dieta: ${financiero['costo_mensual_usd']} USD
    - Volumen total de alimento requerido al día: {financiero['total_kg']} Kg
    - Cantidad de animales sin la vacuna obligatoria del Ciclo Nacional de Fiebre Aftosa: {len(animales_riesgo)} animales.
    """
    
    system_prompt = """
    Eres el consultor zootécnico principal de Inteligencia Artificial del software 'Sentinel Agropecuario', especializado en el estado Falcón.
    Analiza las métricas operativas y los gastos financieros colectivos de la finca provistos.
    Tu tarea es emitir advertencias de riesgo biológico y proponer estrategias de optimización de costos.
    
    Debes retornar OBLIGATORIAMENTE un objeto JSON plano con la siguiente estructura exacta:
    {
        "advertencia_riesgo": "Análisis gerencial del peligro de brote o pérdidas por los animales sin vacunar.",
        "estrategia_produccion": "Plan de manejo técnico para optimizar el consumo de kilogramos de alimento, mitigar gastos en USD o agilizar los ciclos de producción en la zona."
    }
    No utilices formato markdown (prohibido usar ```json), no saludes, ve directo a abrir la llave del JSON.
    """

    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": resumen_macro_finca}
            ],
            temperature=0.3
        )
        
        contenido_crudo = response.choices[0].message.content.strip()
        return True, json.loads(contenido_crudo)
        
    except Exception as e:
        print(f"Error en reporte gerencial IA: {e}")
        return False, {
            "advertencia_riesgo": "No se pudo generar el análisis predictivo global de riesgos.",
            "estrategia_produccion": "Verifique que la base de datos contenga registros activos y que LM Studio esté encendido."
        }

        