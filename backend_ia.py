# backend_ia.py
import json
from database import obtener_conexion
import backend_alimentacion  # Requerido para cruzar los costos financieros de la finca
import backend_animales
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
                   a.sexo, a.id_especie, a.fecha_nacimiento,
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
            "categoria": backend_animales.calcular_categoria_insai(
                animal["id_especie"], 
                animal["sexo"], 
                animal["fecha_nacimiento"]
            ),
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
    Evaluar la siguiente ficha técnica del animal:
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
            SELECT a.numero_identificacion, a.id_especie, a.sexo, a.fecha_nacimiento
            FROM animales a 
            WHERE a.id_especie = 1 AND a.id_estado = 1 AND a.id_animal NOT IN (
                SELECT rv.id_animal FROM registro_vacunacion rv
                INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio
                WHERE lb.id_vacuna = 1
            );
        """
        cursor.execute(query)
        alertas_raw = cursor.fetchall()
        cursor.close()
        
        alertas = []
        for animal in alertas_raw:
            categoria = backend_animales.calcular_categoria_insai(
                animal["id_especie"],
                animal["sexo"],
                animal["fecha_nacimiento"]
            )
            alertas.append({
                "numero_identificacion": animal["numero_identificacion"],
                "categoria_insai": categoria
            })
        return alertas
    except Exception as e:
        print(f"Error en auditoría de riesgos de la finca: {e}")
        return []
    finally:
        conexion.close()


def obtener_detalles_alertas_sanitarias():
    """Retorna los detalles de los animales con dosis de vacunas vencidas."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT a.numero_identificacion, cv.nombre_enfermedad AS vacuna,
                   DATE_FORMAT(rv.fecha_proxima_dosis, '%Y-%m-%d') AS fecha_proxima_dosis,
                   TIMESTAMPDIFF(DAY, rv.fecha_proxima_dosis, CURDATE()) AS dias_vencidos
            FROM registro_vacunacion rv
            INNER JOIN (
                SELECT id_animal, id_vacuna, MAX(id_registro) as max_id
                FROM registro_vacunacion r
                INNER JOIN lotes_biologicos lb ON r.id_lote_bio = lb.id_lote_bio
                GROUP BY id_animal, id_vacuna
            ) latest ON rv.id_registro = latest.max_id
            INNER JOIN animales a ON rv.id_animal = a.id_animal
            INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio
            INNER JOIN catalogo_vacunas cv ON lb.id_vacuna = cv.id_vacuna
            WHERE a.id_estado = 1
              AND rv.fecha_proxima_dosis IS NOT NULL
              AND rv.fecha_proxima_dosis < CURDATE();
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener detalles de alertas sanitarias: {e}")
        return []
    finally:
        conexion.close()


def obtener_detalles_animales_por_codigos(codigos):
    """Retorna los datos biométricos y de especie de los animales por su código de identificación."""
    if not codigos:
        return []
    conexion = obtener_conexion()
    if not conexion:
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        format_strings = ','.join(['%s'] * len(codigos))
        query = f"""
            SELECT a.numero_identificacion, e.nombre AS especie,
                   TIMESTAMPDIFF(MONTH, a.fecha_nacimiento, CURDATE()) AS edad_meses,
                   rb.peso_kg, rb.consumo_alimento_diario
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            LEFT JOIN registros_biometricos rb ON a.id_animal = rb.id_animal
                AND rb.fecha_pesaje = (
                    SELECT MAX(fecha_pesaje)
                    FROM registros_biometricos
                    WHERE id_animal = a.id_animal
                )
            WHERE a.numero_identificacion IN ({format_strings}) AND a.id_estado = 1;
        """
        cursor.execute(query, tuple(codigos))
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener detalles por códigos: {e}")
        return []
    finally:
        conexion.close()


def auditar_vacunas_faltantes_finca():
    """
    Busca todos los animales activos y determina qué vacunas de su catálogo de especie
    nunca se les han aplicado (vacunas faltantes).
    """
    conexion = obtener_conexion()
    if not conexion:
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        # 1. Obtener todos los animales activos
        query_animales = """
            SELECT a.id_animal, a.numero_identificacion, a.id_especie, e.nombre AS especie_nombre, a.sexo
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            WHERE a.id_estado = 1;
        """
        cursor.execute(query_animales)
        animales = cursor.fetchall()
        
        # 2. Obtener todas las vacunas por especie
        query_vacunas = """
            SELECT id_vacuna, nombre_enfermedad, especie_destino
            FROM catalogo_vacunas;
        """
        cursor.execute(query_vacunas)
        vacunas = cursor.fetchall()
        
        # 3. Obtener el historial de vacunas aplicadas
        query_aplicadas = """
            SELECT DISTINCT rv.id_animal, lb.id_vacuna
            FROM registro_vacunacion rv
            INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio;
        """
        cursor.execute(query_aplicadas)
        aplicadas_raw = cursor.fetchall()
        
        cursor.close()
        
        # Crear un set de tuplas (id_animal, id_vacuna) aplicadas
        aplicadas = {(row['id_animal'], row['id_vacuna']) for row in aplicadas_raw}
        
        # Organizar vacunas por especie_destino
        vacunas_por_especie = {}
        for v in vacunas:
            esp = v['especie_destino']
            if esp not in vacunas_por_especie:
                vacunas_por_especie[esp] = []
            vacunas_por_especie[esp].append(v)
            
        faltantes = []
        for a in animales:
            id_animal = a['id_animal']
            id_especie = a['id_especie']
            sexo = a['sexo']
            
            # Buscar vacunas de su especie
            vacunas_especie = vacunas_por_especie.get(id_especie, [])
            for v in vacunas_especie:
                id_vacuna = v['id_vacuna']
                
                # Brucelosis (id=3) solo para hembras
                if id_vacuna == 3 and sexo != 'F':
                    continue
                    
                if (id_animal, id_vacuna) not in aplicadas:
                    faltantes.append({
                        "id_animal": id_animal,
                        "numero_identificacion": a['numero_identificacion'],
                        "especie": a['especie_nombre'],
                        "vacuna": v['nombre_enfermedad']
                    })
        return faltantes
    except Exception as e:
        print(f"Error al auditar vacunas faltantes: {e}")
        return []
    finally:
        conexion.close()


def generar_reporte_gerencial_ia(costo_por_kg=0.5):
    """
    Recopila detalladamente los totales financieros de alimentación, riesgos de aftosa,
    vacunas vencidas, vacunas faltantes por animal y anomalías de peso/consumo individual
    para generar un informe gerencial zootécnico ultra-preciso mediante IA.
    """
    try:
        # 1. Calcular totales financieros basados en el costo real por kg
        financiero = backend_alimentacion.calcular_totales_alimentacion_finca(costo_por_kg)
        costo_diario = financiero.get('costo_diario_usd', 0.0)
        costo_mensual = financiero.get('costo_mensual_usd', 0.0)
        total_kg = financiero.get('total_kg', 0.0)

        # 2. Auditar vacunas vencidas (retrasos)
        vacunas_vencidas = obtener_detalles_alertas_sanitarias()

        # 3. Auditar todas las vacunas faltantes (nunca aplicadas) por animal
        vacunas_faltantes = auditar_vacunas_faltantes_finca()

        # 4. Obtener anomalías de producción con detalles biométricos
        codigos_alertas_prod = backend_animales.obtener_codigos_alertas_produccion()
        detalles_alertas_prod = obtener_detalles_animales_por_codigos(codigos_alertas_prod)

        # Construir contexto sumamente rico y preciso para la IA
        # Agrupar vacunas faltantes por animal
        faltantes_por_animal = {}
        for vf in vacunas_faltantes:
            key = f"{vf['numero_identificacion']} ({vf['especie']})"
            if key not in faltantes_por_animal:
                faltantes_por_animal[key] = []
            faltantes_por_animal[key].append(vf['vacuna'])
            
        faltantes_texto = ""
        if faltantes_por_animal:
            for animal, vacs in faltantes_por_animal.items():
                faltantes_texto += f"- **{animal}** no tiene aplicadas: {', '.join(vacs)}\n"
        else:
            faltantes_texto = "- Ninguno (Todos los animales tienen al menos una dosis de todas las vacunas de su catálogo)."

        vacunas_texto = "\n".join([f"- Código: {v['numero_identificacion']} | Vacuna: {v['vacuna']} | Vencida hace: {v['dias_vencidos']} días (Debía aplicarse el: {v['fecha_proxima_dosis']})" for v in vacunas_vencidas]) if vacunas_vencidas else "- Ninguno (Todas las vacunas aplicadas están vigentes)."
        prod_texto = "\n".join([f"- Código: {p['numero_identificacion']} ({p['especie']}) | Edad: {p['edad_meses']} meses | Peso: {p['peso_kg']} kg | Consumo de alimento: {p['consumo_alimento_diario']} kg/día" for p in detalles_alertas_prod]) if detalles_alertas_prod else "- Ninguno (Todos los animales tienen peso y consumo dentro del rango saludable)."

        resumen_macro_finca = f"""
        DATOS REALES OPERATIVOS Y FINANCIEROS DE LA FINCA:
        - Costo de alimento configurado: ${costo_por_kg:.2f} USD/Kg
        - Consumo total diario de alimento de la finca: {total_kg:.2f} Kg
        - Costo diario total en alimentación: ${costo_diario:.2f} USD/día
        - Proyección de costo mensual de alimentación (30 días): ${costo_mensual:.2f} USD/mes

        1. ANIMALES SIN VACUNAS APLICADAS (ESQUEMA DE VACUNACIÓN INCOMPLETO/VACUNAS FALTANTES):
        {faltantes_texto}

        2. ANIMALES CON DOSIS DE OTRAS VACUNAS VENCIDAS (RETRASOS SANITARIOS):
        {vacunas_texto}

        3. ANIMALES CON ANOMALÍAS DE PRODUCCIÓN (PESO O INGESTA DE ALIMENTO FUERA DEL RANGO NORMAL):
        {prod_texto}
        """

        system_prompt = f"""
        Eres el consultor zootécnico principal de Inteligencia Artificial de la plataforma 'AdmiFinca', especializado en el estado Falcón, Venezuela.
        Analiza detalladamente las métricas operativas, anomalías sanitarias y gastos financieros provistos de la finca.
        
        Debes emitir un informe técnico de manera muy precisa, analítica, organizada y sumamente legible en formato JSON dentro de un bloque de código Markdown (```json ... ```).
        Usa Markdown (listas con viñetas `-`, títulos breves `###` e indicadores clave `**Negritas**`) para estructurar el contenido de cada campo de manera limpia, presentable y directa.
        NO escribas párrafos extensos o compactos de texto corrido. Cada recomendación y análisis debe ser una viñeta objetiva.
        
        Estructura del JSON:
        {{
            "advertencia_riesgo": "### Riesgos Sanitarios por Falta de Vacunas\\n- **Vacunas Faltantes por Animal:** Detallar los códigos de los animales y la lista de vacunas que nunca se les han aplicado (menciona tanto ovinos como bovinos, ej. `OVI-11` y `OVI-2144` sin vacunas de su especie, y `BOV-99` sin Aftosa, Rabia, etc.).\\n- **Dosis Vencidas:** Detallar códigos de animales y días de retraso (si hay).\\n- **Riesgo Epidemiológico:** Explicar el peligro sanitario en Falcón por tener animales sin inmunizar.",
            "estrategia_produccion": "### Análisis de Costos de Alimentación\\n- **Costo Proyectado:** ${costo_mensual:.2f} USD/mes.\\n- **Eficiencia Diaria:** Consumo total de {total_kg:.2f} Kg con costo diario de ${costo_diario:.2f} USD.\\n\\n### Casos con Anomalías Zootécnicas\\n- Listar cada animal con anomalías, indicando de forma **muy explícita** si el problema es **Sobrealimentación** (consumo excesivo de X kg/día por encima del rango saludable) o **Subalimentación** (riesgo de desnutrición/ingesta insuficiente). **Prohibido** usar la frase ambigua 'desvío en ingesta'. Explica detalladamente si es consumo de más (sobregasto) o consumo de menos (desnutrición).\\n\\n### Recomendaciones Inmediatas\\n- **Ajuste:** Medidas de racionamiento o suplementación específicas para los animales desviados.\\n- **Alternativas:** Fuentes locales baratas de forraje."
        }}
        
        Reglas de Formato y Contenido:
        1. Emplea saltos de línea `\\n` para espaciar secciones y listas de viñetas.
        2. Mantén cada viñeta breve, objetiva y al grano. Cita siempre los códigos de los animales correspondientes.
        3. Sé explícito al calificar las anomalías alimenticias: indica claramente si se trata de sobrealimentación (sobregasto) o subalimentación (desnutrición), detallando el impacto.
        4. Devuelve únicamente el objeto JSON cerrado dentro del bloque ```json ... ```, sin introducciones ni comentarios adicionales.
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

        