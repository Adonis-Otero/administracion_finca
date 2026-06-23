# backend_reporte_pdf.py
# Módulo para generar reportes gerenciales en PDF descargable con FPDF2 nativo
import io
import datetime
from fpdf import FPDF
from fpdf.fonts import FontFace
from database import obtener_conexion
import backend_alimentacion
import backend_animales
import backend_ia


class ReportePDF(FPDF):
    """PDF personalizado con encabezado y pie de página para AdmiFinca."""
    
    def __init__(self, nombre_finca="Finca AdmiFinca"):
        super().__init__()
        self.nombre_finca = nombre_finca
        self.fecha_reporte = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    def header(self):
        # Fondo del header
        self.set_fill_color(88, 28, 135)  # Púrpura oscuro
        self.rect(0, 0, 210, 28, 'F')
        
        # Título
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "REPORTE GERENCIAL ZOOTÉCNICO", new_x="LMARGIN", new_y="NEXT", align="C")
        
        # Subtítulo
        self.set_font("Helvetica", "", 9)
        self.set_text_color(216, 180, 254)
        self.cell(0, 6, f"{self.nombre_finca} | Generado: {self.fecha_reporte}", new_x="LMARGIN", new_y="NEXT", align="C")
        
        # Línea decorativa
        self.set_draw_color(168, 85, 247)
        self.set_line_width(0.8)
        self.line(10, 30, 200, 30)
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"AdmiFinca - Reporte Gerencial | Página {self.page_no()}/{{nb}} | {self.fecha_reporte}", align="C")
    
    def titulo_seccion(self, titulo, icono=""):
        """Agrega un título de sección con fondo coloreado."""
        self.ln(4)
        self.set_fill_color(243, 232, 255)  # Lila claro
        self.set_text_color(88, 28, 135)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"  {icono}  {titulo}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(30, 41, 59)
        self.ln(2)
    
    def subtitulo(self, texto):
        """Agrega un subtítulo menor."""
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(71, 85, 105)
        self.cell(0, 6, texto, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 41, 59)
        self.ln(1)
    
    def texto_normal(self, texto):
        """Texto normal."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(51, 65, 85)
        self.multi_cell(0, 5, texto)
        self.ln(1)
    
    def texto_alerta(self, texto, tipo="warning"):
        """Texto de alerta con fondo coloreado."""
        if tipo == "danger":
            self.set_fill_color(254, 226, 226)
            self.set_text_color(153, 27, 27)
        elif tipo == "warning":
            self.set_fill_color(254, 249, 195)
            self.set_text_color(146, 64, 14)
        elif tipo == "success":
            self.set_fill_color(220, 252, 231)
            self.set_text_color(22, 101, 52)
        else:
            self.set_fill_color(239, 246, 255)
            self.set_text_color(30, 64, 175)
        
        self.set_font("Helvetica", "", 8)
        self.multi_cell(0, 5, texto, fill=True)
        self.set_text_color(30, 41, 59)
        self.ln(2)
    
    def linea_kpi(self, label, valor, unidad=""):
        """Agrega una línea de KPI (indicador clave)."""
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 116, 139)
        self.cell(70, 5, label + ":", align="R")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 23, 42)
        self.cell(50, 5, f"  {valor} {unidad}", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 41, 59)


def agregar_tabla_fpdf2(pdf, headers, datos, anchos, alineaciones):
    """Genera una tabla utilizando la API nativa de tablas de FPDF2 que envuelve el texto automáticamente."""
    align_mapping = {"C": "CENTER", "L": "LEFT", "R": "RIGHT"}
    alineaciones_mapeadas = tuple(align_mapping.get(a, "CENTER") for a in alineaciones)
    
    header_style = FontFace(emphasis="BOLD", color=255, fill_color=(88, 28, 135))
    
    pdf.set_font("Helvetica", size=8)
    with pdf.table(
        headings_style=header_style,
        align="CENTER",
        col_widths=anchos,
        text_align=alineaciones_mapeadas,
        cell_fill_color=(248, 250, 252),
        cell_fill_mode="ROWS"
    ) as table:
        # FPDF2 table handles first row as headings automatically
        row = table.row()
        for h in headers:
            row.cell(h)
        for fila in datos:
            row = table.row()
            for celda in fila:
                row.cell(str(celda))
    pdf.ln(3)


def _obtener_censo_animales():
    """Retorna el censo completo de animales activos con datos biométricos."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT a.id_animal, a.numero_identificacion, e.nombre AS especie,
                   a.sexo, a.id_especie, a.fecha_nacimiento, a.categoria_insai,
                   COALESCE(rb.peso_kg, 0) AS peso_kg,
                   COALESCE(rb.consumo_alimento_diario, 0) AS consumo_diario,
                   COALESCE(a.tipo_alimento, 'Sin asignar') AS dieta,
                   DATE_FORMAT(rb.fecha_pesaje, '%d/%m/%Y') AS fecha_pesaje
            FROM animales a
            INNER JOIN especies e ON a.id_especie = e.id_especie
            LEFT JOIN registros_biometricos rb ON a.id_animal = rb.id_animal
                AND rb.fecha_pesaje = (
                    SELECT MAX(fecha_pesaje) FROM registros_biometricos WHERE id_animal = a.id_animal
                )
            WHERE a.id_estado = 1
            ORDER BY e.nombre, a.numero_identificacion;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener censo de animales: {e}")
        return []
    finally:
        conexion.close()


def _obtener_historial_vacunacion():
    """Retorna el historial de vacunas aplicadas de todos los animales activos."""
    conexion = obtener_conexion()
    if not conexion:
        return []
    import pymysql.cursors
    try:
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT a.numero_identificacion, cv.nombre_enfermedad AS vacuna,
                   DATE_FORMAT(rv.fecha_aplicacion, '%d/%m/%Y') AS fecha_aplicacion,
                   DATE_FORMAT(rv.fecha_proxima_dosis, '%d/%m/%Y') AS proxima_dosis,
                   IF(rv.fecha_proxima_dosis IS NOT NULL AND rv.fecha_proxima_dosis < CURDATE(), 'VENCIDA', 'VIGENTE') AS estatus
            FROM registro_vacunacion rv
            INNER JOIN animales a ON rv.id_animal = a.id_animal
            INNER JOIN lotes_biologicos lb ON rv.id_lote_bio = lb.id_lote_bio
            INNER JOIN catalogo_vacunas cv ON lb.id_vacuna = cv.id_vacuna
            WHERE a.id_estado = 1
            ORDER BY a.numero_identificacion, rv.fecha_aplicacion DESC;
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        return resultados
    except Exception as e:
        print(f"Error al obtener historial de vacunación: {e}")
        return []
    finally:
        conexion.close()


def _calcular_rangos_ideales(id_especie, edad_meses):
    """Retorna los rangos ideales de peso y consumo según especie y edad."""
    if id_especie == 1:  # Bovinos
        if edad_meses < 6:
            return (60, 120), (1.5, 3.0)
        elif edad_meses < 12:
            return (120, 220), (3.0, 5.0)
        elif edad_meses <= 24:
            return (220, 380), (5.0, 8.0)
        else:
            return (380, 550), (8.0, 12.0)
    elif id_especie == 3:  # Ovinos/Caprinos
        if edad_meses < 6:
            return (15, 30), (0.5, 1.0)
        elif edad_meses < 12:
            return (30, 50), (1.0, 1.5)
        else:
            return (50, 80), (1.5, 2.5)
    else:  # Porcinos u otros
        if edad_meses < 3:
            return (10, 30), (0.5, 1.5)
        elif edad_meses < 6:
            return (30, 70), (1.5, 3.0)
        else:
            return (70, 120), (3.0, 5.0)


def generar_pdf_gerencial(costo_por_kg=0.50):
    """
    Genera un reporte PDF completo con toda la información gerencial de la finca.
    Retorna bytes del PDF generado.
    """
    pdf = ReportePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # ===================================================================
    # SECCIÓN 1: RESUMEN EJECUTIVO Y FINANCIERO
    # ===================================================================
    pdf.titulo_seccion("RESUMEN EJECUTIVO Y FINANCIERO", "$$")
    
    # Obtener datos financieros
    financiero = backend_alimentacion.calcular_totales_alimentacion_finca(costo_por_kg)
    total_kg = financiero.get('total_kg', 0.0)
    costo_diario = financiero.get('costo_diario_usd', 0.0)
    costo_mensual = financiero.get('costo_mensual_usd', 0.0)
    
    # Obtener censo
    censo = _obtener_censo_animales()
    total_animales = len(censo)
    
    # Contar por especie
    conteo_especies = {}
    for a in censo:
        esp = a['especie']
        conteo_especies[esp] = conteo_especies.get(esp, 0) + 1
    
    pdf.subtitulo("Indicadores Clave de Operación")
    pdf.linea_kpi("Total de animales activos", str(total_animales), "cabezas")
    for especie, cantidad in conteo_especies.items():
        pdf.linea_kpi(f"  - {especie}", str(cantidad), "cabezas")
    pdf.linea_kpi("Costo por kg de alimento", f"${costo_por_kg:.2f}", "USD/kg")
    pdf.linea_kpi("Consumo diario total de la finca", f"{total_kg:.2f}", "kg/día")
    pdf.linea_kpi("Costo diario de alimentación", f"${costo_diario:.2f}", "USD/día")
    pdf.linea_kpi("Proyección mensual (30 días)", f"${costo_mensual:.2f}", "USD/mes")
    pdf.linea_kpi("Proyección anual (365 días)", f"${costo_diario * 365:.2f}", "USD/año")
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 2: CENSO Y ESTADO BIOMÉTRICO DEL REBAÑO
    # ===================================================================
    pdf.titulo_seccion("CENSO Y ESTADO BIOMÉTRICO DEL REBAÑO", ">>")
    
    if censo:
        headers_censo = ["Código", "Especie", "Sexo", "Categoría", "Peso (kg)", "Ideal (kg)", "Estado Peso", "Consumo (kg/día)", "Dieta"]
        anchos_censo = [22, 18, 12, 22, 18, 22, 22, 24, 30]
        alineaciones_censo = ["C", "C", "C", "C", "C", "C", "C", "C", "L"]
        datos_censo = []
        
        for a in censo:
            fecha_nac = a['fecha_nacimiento']
            if fecha_nac:
                if isinstance(fecha_nac, str):
                    try:
                        nacimiento = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").date()
                    except:
                        nacimiento = datetime.date.today()
                else:
                    nacimiento = fecha_nac if isinstance(fecha_nac, datetime.date) else fecha_nac.date()
                edad_meses = (datetime.date.today() - nacimiento).days // 30
            else:
                edad_meses = 12
            
            rango_peso, rango_consumo = _calcular_rangos_ideales(a['id_especie'], edad_meses)
            peso = float(a['peso_kg'])
            
            # Determinar estado del peso
            if peso < rango_peso[0]:
                estado_peso = "BAJO"
            elif peso > rango_peso[1]:
                estado_peso = "ALTO"
            else:
                estado_peso = "NORMAL"
            
            sexo_txt = "M" if a['sexo'] == 'M' else "H"
            ideal_txt = f"{rango_peso[0]}-{rango_peso[1]}"
            
            datos_censo.append([
                a['numero_identificacion'],
                a['especie'][:10],
                sexo_txt,
                a['categoria_insai'] or "-",
                f"{peso:.1f}",
                ideal_txt,
                estado_peso,
                f"{float(a['consumo_diario']):.1f}",
                str(a['dieta'])
            ])
        
        agregar_tabla_fpdf2(pdf, headers_censo, datos_censo, anchos_censo, alineaciones_censo)
    else:
        pdf.texto_normal("No se encontraron animales activos en el sistema.")
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 3: ESTADO SANITARIO - VACUNAS FALTANTES
    # ===================================================================
    pdf.titulo_seccion("ESTADO SANITARIO - VACUNAS FALTANTES", "!!")
    
    vacunas_faltantes = backend_ia.auditar_vacunas_faltantes_finca()
    
    if vacunas_faltantes:
        pdf.texto_alerta(
            f"ALERTA: Se detectaron {len(vacunas_faltantes)} vacunas faltantes en el rebaño. "
            "Esto representa un riesgo sanitario y potenciales sanciones del INSAI.",
            tipo="danger"
        )
        
        # Agrupar faltantes por animal
        faltantes_por_animal = {}
        for vf in vacunas_faltantes:
            key = vf['numero_identificacion']
            if key not in faltantes_por_animal:
                faltantes_por_animal[key] = {"especie": vf['especie'], "vacunas": []}
            faltantes_por_animal[key]["vacunas"].append(vf['vacuna'])
        
        headers_falt = ["Código Animal", "Especie", "Vacunas Faltantes"]
        anchos_falt = [35, 30, 125]
        alineaciones_falt = ["C", "C", "L"]
        datos_falt = []
        for codigo, info in faltantes_por_animal.items():
            datos_falt.append([
                codigo,
                info['especie'],
                ", ".join(info['vacunas'])
            ])
        agregar_tabla_fpdf2(pdf, headers_falt, datos_falt, anchos_falt, alineaciones_falt)
    else:
        pdf.texto_alerta(
            "EXCELENTE: Todos los animales activos tienen al menos una dosis aplicada de cada vacuna de su catálogo de especie.",
            tipo="success"
        )
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 4: ESTADO SANITARIO - VACUNAS VENCIDAS
    # ===================================================================
    pdf.titulo_seccion("DOSIS DE VACUNAS VENCIDAS (RETRASOS)", "!!")
    
    vacunas_vencidas = backend_ia.obtener_detalles_alertas_sanitarias()
    
    if vacunas_vencidas:
        pdf.texto_alerta(
            f"ATENCIÓN: Se detectaron {len(vacunas_vencidas)} dosis de vacunas vencidas (fuera de fecha de próxima aplicación). "
            "Se requiere reaplicación inmediata.",
            tipo="warning"
        )
        
        headers_venc = ["Código Animal", "Vacuna", "Próx. Dosis", "Días Vencida"]
        anchos_venc = [40, 60, 45, 45]
        alineaciones_venc = ["C", "L", "C", "C"]
        datos_venc = []
        for v in vacunas_vencidas:
            datos_venc.append([
                v['numero_identificacion'],
                v['vacuna'],
                v['fecha_proxima_dosis'],
                f"{v['dias_vencidos']} días"
            ])
        agregar_tabla_fpdf2(pdf, headers_venc, datos_venc, anchos_venc, alineaciones_venc)
    else:
        pdf.texto_alerta(
            "SIN RETRASOS: Todas las vacunas aplicadas se encuentran vigentes y dentro de sus fechas de próxima dosis.",
            tipo="success"
        )
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 5: HISTORIAL DE VACUNACIÓN COMPLETO
    # ===================================================================
    pdf.titulo_seccion("HISTORIAL DE VACUNACIÓN COMPLETO", "++")
    
    historial_vac = _obtener_historial_vacunacion()
    
    if historial_vac:
        headers_hist = ["Código Animal", "Vacuna", "Fecha Aplicación", "Próxima Dosis", "Estatus"]
        anchos_hist = [30, 50, 35, 35, 40]
        alineaciones_hist = ["C", "L", "C", "C", "C"]
        datos_hist = []
        for h in historial_vac:
            datos_hist.append([
                h['numero_identificacion'],
                h['vacuna'],
                h['fecha_aplicacion'],
                h['proxima_dosis'] or "N/A",
                h['estatus']
            ])
        agregar_tabla_fpdf2(pdf, headers_hist, datos_hist, anchos_hist, alineaciones_hist)
    else:
        pdf.texto_normal("No se encontraron registros de vacunación en el sistema.")
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 6: ANOMALÍAS DE PRODUCCIÓN
    # ===================================================================
    pdf.titulo_seccion("ANOMALÍAS DE PRODUCCIÓN (PESO Y ALIMENTACIÓN)", "!!")
    
    codigos_alertas = backend_animales.obtener_codigos_alertas_produccion()
    detalles_alertas = backend_ia.obtener_detalles_animales_por_codigos(codigos_alertas)
    
    if detalles_alertas:
        pdf.texto_alerta(
            f"Se detectaron {len(detalles_alertas)} animales con peso o consumo de alimento fuera del rango saludable para su especie y edad.",
            tipo="warning"
        )
        
        headers_anom = ["Código", "Especie", "Edad (meses)", "Peso (kg)", "Rango Ideal", "Consumo (kg/día)", "Diagnóstico"]
        anchos_anom = [22, 20, 20, 18, 25, 25, 60]
        alineaciones_anom = ["C", "C", "C", "C", "C", "C", "L"]
        datos_anom = []
        
        for p in detalles_alertas:
            edad = int(p['edad_meses']) if p['edad_meses'] else 0
            peso = float(p['peso_kg']) if p['peso_kg'] else 0
            consumo = float(p['consumo_alimento_diario']) if p['consumo_alimento_diario'] else 0
            
            # Determinar especie_id para rangos
            especie_id = 1 if "bovin" in p['especie'].lower() else (3 if "ovin" in p['especie'].lower() or "caprin" in p['especie'].lower() else 2)
            rango_peso, rango_consumo = _calcular_rangos_ideales(especie_id, edad)
            
            # Determinar diagnóstico
            diagnosticos = []
            if peso < rango_peso[0]:
                diagnosticos.append("Bajo peso")
            elif peso > rango_peso[1]:
                diagnosticos.append("Sobrepeso")
            if consumo < rango_consumo[0]:
                diagnosticos.append("Subalimentación")
            elif consumo > rango_consumo[1]:
                diagnosticos.append("Sobrealimentación")
            if not diagnosticos:
                diagnosticos.append("Revisar datos")
            
            datos_anom.append([
                p['numero_identificacion'],
                p['especie'][:10],
                str(edad),
                f"{peso:.1f}",
                f"{rango_peso[0]}-{rango_peso[1]}",
                f"{consumo:.1f}",
                " / ".join(diagnosticos)
            ])
        
        agregar_tabla_fpdf2(pdf, headers_anom, datos_anom, anchos_anom, alineaciones_anom)
    else:
        pdf.texto_alerta(
            "SIN ANOMALÍAS: Todos los animales activos tienen peso y consumo de alimento dentro del rango saludable.",
            tipo="success"
        )
    pdf.ln(3)
    
    # ===================================================================
    # SECCIÓN 7: RESUMEN DE COSTOS POR ESPECIE
    # ===================================================================
    pdf.titulo_seccion("DESGLOSE DE COSTOS POR ESPECIE", "$$")
    
    if censo:
        costos_especie = {}
        for a in censo:
            esp = a['especie']
            consumo = float(a['consumo_diario'])
            if esp not in costos_especie:
                costos_especie[esp] = {"cantidad": 0, "consumo_total": 0.0}
            costos_especie[esp]["cantidad"] += 1
            costos_especie[esp]["consumo_total"] += consumo
        
        headers_costos = ["Especie", "Cantidad", "Consumo Total (kg/día)", "Costo Diario (USD)", "Costo Mensual (USD)", "% del Gasto"]
        anchos_costos = [30, 22, 35, 33, 35, 35]
        alineaciones_costos = ["L", "C", "C", "C", "C", "C"]
        datos_costos = []
        
        consumo_total_finca = sum(e["consumo_total"] for e in costos_especie.values())
        
        for especie, info in costos_especie.items():
            costo_dia = info["consumo_total"] * costo_por_kg
            costo_mes = costo_dia * 30
            porcentaje = (info["consumo_total"] / consumo_total_finca * 100) if consumo_total_finca > 0 else 0
            
            datos_costos.append([
                especie,
                str(info["cantidad"]),
                f"{info['consumo_total']:.2f}",
                f"${costo_dia:.2f}",
                f"${costo_mes:.2f}",
                f"{porcentaje:.1f}%"
            ])
        
        agregar_tabla_fpdf2(pdf, headers_costos, datos_costos, anchos_costos, alineaciones_costos)
    pdf.ln(3)
    
    # ===================================================================
    # PIE LEGAL
    # ===================================================================
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(0, 4, 
        "NOTA LEGAL: Este reporte fue generado automáticamente por el sistema AdmiFinca. "
        "Los datos biométricos, sanitarios y financieros reflejan la información registrada "
        "en la base de datos al momento de la generación. Los rangos ideales de peso y consumo "
        "son aproximaciones zootécnicas referenciales y no sustituyen la evaluación de un "
        "médico veterinario certificado. Para fines de auditoría del INSAI, este documento "
        "debe acompañarse de los registros físicos oficiales de la finca."
    )
    
    # Generar bytes del PDF
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)
