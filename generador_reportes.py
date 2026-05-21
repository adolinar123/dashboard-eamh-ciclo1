#!/usr/bin/env python3
"""
Generador de Reportes PDF – Cuestionario Diagnóstico EAMH
Ciclo 1 · Múltiples instituciones
Niveles: Institución / Grado / Grupo / Estudiante
"""

import os
import re
import csv
import glob
import tempfile
import shutil
from collections import defaultdict, Counter

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable

# ── RUTAS ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CSV_CASOS   = os.path.join(BASE_DIR, "Caos de respuesta Cuestionario Ciclo 1.csv")
CSV_FINALES = sorted(glob.glob(os.path.join(BASE_DIR, "Tabulación * FINAL.csv")))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
OUT_DIR     = os.path.join(BASE_DIR, "reportes_pdf")
os.makedirs(OUT_DIR, exist_ok=True)

LOGO_IZQ = os.path.join(ASSETS_DIR, "logo_izquierda.png")
LOGO_DER = os.path.join(ASSETS_DIR, "logo_derecha.png")

# ── PALETA ────────────────────────────────────────────────────────────────────
C_AZUL     = colors.HexColor("#1A3A6B")
C_AZUL_CLR = colors.HexColor("#1565C0")
C_VERDE    = colors.HexColor("#2E7D32")
C_NARANJA  = colors.HexColor("#E65100")
C_AMARILLO = colors.HexColor("#F9A825")
C_GRIS     = colors.HexColor("#F5F5F5")
C_GRIS_OSC = colors.HexColor("#37474F")
C_BORDE    = colors.HexColor("#BDBDBD")
C_TEXTO    = colors.HexColor("#212121")

COMP_COLORS = {
    "Motivación":        colors.HexColor("#1565C0"),
    "Habilidades":       colors.HexColor("#2E7D32"),
    "Estilos":           colors.HexColor("#6A1B9A"),
    "Socioemocional 13": colors.HexColor("#00838F"),
    "Socioemocional 14": colors.HexColor("#00838F"),
    "Socioemocional 15": colors.HexColor("#00838F"),
}

PROFILE_COLORS = {
    "Orientación motivacional extrínseco":              "#E65100",
    "Orientación motivacional intrínseca":              "#2E7D32",
    "Orientación motivacional mixta o situada":         "#F9A825",
    "Autopercepción de alta confianza cognitiva":       "#2E7D32",
    "Autopercepción cognitiva en proceso de diferenciación": "#F9A825",
    "Autopercepción de necesidad de regulación externa":"#E65100",
    "Preferencia  por lo  Visual":                      "#1565C0",
    "Preferencia  por lo Auditivo":                     "#6A1B9A",
    "Preferencia por lo Kinestésico":                   "#00838F",
    "Preferencia por el aprendizaje cooperativo":       "#2E7D32",
    "Preferencia por el aprendizaje individual":        "#F9A825",
    "Percepción de  autoconfianza  ante el desafío":    "#2E7D32",
    "Percepción vulnerabilidad ante el desafio":        "#E65100",
    "Vinculación afectiva escolar muy buena":            "#1B5E20",
    "Vinculación afectiva escolar buena":               "#2E7D32",
    "Vinculación afectiva escolar regular":             "#F9A825",
    "Vinculación afectiva escolar desfavorable":        "#E65100",
}

# ── ADVERTENCIA PEDAGÓGICA ────────────────────────────────────────────────────
DISCLAIMER = [
    "Este informe debe ser asumido con rigurosidad pedagógica. Los datos aquí contenidos "
    "reflejan las percepciones del estudiante sobre sus propias características de aprendizaje, "
    "recopiladas a través del cuestionario diagnóstico. Por lo tanto, este documento tiene una "
    "finalidad estrictamente pedagógica y no una naturaleza patológica ni psicométrica.",

    "La información aquí expuesta es de manejo exclusivo de los docentes y directivos. En "
    "consecuencia, la transferencia de estos datos a los padres de familia, a externos o a otros "
    "empleados de la institución educativa queda bajo la completa responsabilidad de la institución.",

    "Es fundamental tener en cuenta que las recomendaciones construidas a partir de este instrumento "
    "deben considerar que el estudiante se encuentra en un proceso formativo dinámico. Por ende, este "
    "diagnóstico no determina de manera fija su forma de aprender ni pretende encasillarlo en "
    "interpretaciones estáticas. El uso de esta herramienta se fundamenta, rigurosamente, en una "
    "reflexión pedagógica cuidada, contextualizada y profesional.",
]

# ── DESCRIPCIONES DE COMPONENTES ──────────────────────────────────────────────
COMP_DESCRIPTIONS = {
    "Motivación": (
        "Componente 1: Orientación Motivacional",
        "Este componente refleja la orientación motivacional predominante del estudiante: si su impulso "
        "hacia el aprendizaje proviene principalmente de factores externos (aprobación social, incentivos, "
        "notas) o de motivaciones internas (curiosidad, satisfacción personal, interés genuino por "
        "aprender). La motivación intrínseca está fuertemente asociada con el aprendizaje autónomo y la "
        "autorregulación. Orientar las estrategias pedagógicas según este perfil permite fortalecer el "
        "compromiso, la persistencia y la autonomía académica del grupo."
    ),
    "Habilidades": (
        "Componente 2: Autopercepción de Habilidades Cognitivas",
        "Muestra la distribución de la autopercepción de los estudiantes respecto a sus habilidades "
        "cognitivas. Este componente no evalúa el desempeño real sino la forma en que el estudiante se "
        "percibe a sí mismo como aprendiz. La autopercepción positiva está asociada con mayor disposición "
        "al reto académico y al aprendizaje autónomo. Permite identificar grupos que requieren "
        "acompañamiento diferenciado para fortalecer su confianza académica y su capacidad de "
        "autorregulación."
    ),
    "Estilos": (
        "Componente 3: Preferencias en Estilos de Aprendizaje",
        "Indica la preferencia del grupo por el canal o formato de presentación de los objetos de "
        "aprendizaje: visual (imágenes, gráficos, esquemas), auditivo (explicaciones orales, sonidos, "
        "discusiones) o kinestésico (manipulación, experimentación, movimiento). Conocer la distribución "
        "de estilos en el grupo es un insumo clave para la diversificación de materiales, actividades y "
        "estrategias de enseñanza que atiendan la variedad de perfiles presentes en el aula."
    ),
    "Socioemocional 13": (
        "Subcomponente Socioemocional – Relación con Pares (Ítem 13)",
        "Refleja la preferencia de los estudiantes por modalidades cooperativas o individuales de "
        "aprendizaje, evidenciando patrones en la disposición social del aula. Un grupo con alta "
        "preferencia cooperativa se beneficia de metodologías de aprendizaje entre pares, aprendizaje "
        "basado en proyectos y trabajo en equipo. Un grupo con preferencia individual puede requerir "
        "mayor diversificación en las modalidades de trabajo y gradualidad en la introducción de "
        "dinámicas colaborativas."
    ),
    "Socioemocional 14": (
        "Subcomponente Socioemocional – Autoconfianza ante el Desafío (Ítem 14)",
        "Indica cómo se perciben los estudiantes al enfrentar situaciones de reto académico: desde la "
        "confianza y la seguridad, o desde la vulnerabilidad y la inseguridad. Este indicador es una "
        "señal relevante para el diseño de andamiajes pedagógicos, niveles de dificultad progresivos y "
        "estrategias de retroalimentación que fortalezcan la resiliencia académica y la disposición "
        "hacia el aprendizaje desafiante."
    ),
    "Socioemocional 15": (
        "Subcomponente Socioemocional – Vinculación Afectiva Escolar (Ítem 15)",
        "Describe el estado de ánimo y el vínculo afectivo general de los estudiantes con la institución "
        "educativa. La vinculación afectiva positiva es un factor protector del bienestar escolar y está "
        "directamente relacionada con la permanencia, el compromiso y el desempeño académico. Un grupo "
        "con baja vinculación afectiva requiere intervenciones prioritarias desde la dimensión "
        "socioemocional del proceso formativo."
    ),
}


# ── CARGA DE DATOS ────────────────────────────────────────────────────────────

def load_casos() -> dict:
    casos = defaultdict(dict)
    with open(CSV_CASOS, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for row in reader:
            if len(row) < 4:
                continue
            comp  = row[0].strip()
            clave = row[1].strip()
            nom   = row[2].strip()
            desc  = row[3].strip()
            casos[comp][clave] = (nom, desc)
    return dict(casos)


def load_all_estudiantes() -> pd.DataFrame:
    dfs = []
    for csv_path in CSV_FINALES:
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig", dtype=str)
        df.columns = [c.strip() for c in df.columns]
        df = df.dropna(subset=["Institución", "Grupo"])
        df = df[df["Institución"].str.strip() != ""]
        df["Grado"] = df["Grupo"].apply(
            lambda x: str(x).split(";")[0].strip() if ";" in str(x) else str(x).strip())
        df["Salon"] = df["Grupo"].apply(
            lambda x: str(x).split(";")[1].strip() if ";" in str(x) else "1")
        df["Nombre"] = df["Nombre"].str.strip()
        df["Institución"] = df["Institución"].str.strip()
        if "Edad" not in df.columns:
            df["Edad"] = "N/D"
        for col in [f"P{i}" for i in range(1, 16)]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            else:
                df[col] = 0
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def clasificar_estudiante(row: pd.Series, casos: dict) -> dict:
    perfiles = {}
    clave_mot = f"{row['P1']}-{row['P2']}-{row['P3']}-{row['P4']}"
    perfiles["Motivación"] = casos.get(
        "Componente 1: Motivación", {}).get(clave_mot, ("Sin clasificar", ""))
    clave_hab = "-".join(str(row[f"P{i}"]) for i in range(5, 12))
    perfiles["Habilidades"] = casos.get(
        "Componente 2: Habilidades Cognitivas", {}).get(clave_hab, ("Sin clasificar", ""))
    perfiles["Estilos"] = casos.get(
        "Componente 3: Estilos de Aprendizaje", {}).get(str(row["P12"]), ("Sin clasificar", ""))
    for item, col in [("13", "P13"), ("14", "P14"), ("15", "P15")]:
        perfiles[f"Socioemocional {item}"] = casos.get(
            f"Subcomponente Socioemocional (Ítem {item})", {}).get(
            str(row[col]), ("Sin clasificar", ""))
    return perfiles


# ── GRÁFICAS ──────────────────────────────────────────────────────────────────

def make_bar_chart(counter: Counter, title: str, filename: str,
                   width=14, height=4) -> str:
    if not counter:
        return None
    labels = list(counter.keys())
    values = list(counter.values())
    total  = sum(values)
    pcts   = [v / total * 100 for v in values]
    bar_colors = [PROFILE_COLORS.get(l, "#90A4AE") for l in labels]
    short_labels = [l if len(l) <= 42 else l[:39] + "..." for l in labels]

    fig, ax = plt.subplots(figsize=(width, max(height, len(labels) * 0.9 + 1.5)))
    bars = ax.barh(range(len(labels)), pcts, color=bar_colors,
                   edgecolor="white", height=0.55, zorder=2)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(short_labels, fontsize=9)
    ax.set_xlim(0, 115)
    ax.set_xlabel("Porcentaje (%)", fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=1)
    ax.spines[["top", "right"]].set_visible(False)
    for bar, pct, val in zip(bars, pcts, values):
        ax.text(pct + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}% (n={val})", va="center", fontsize=8.5)
    plt.tight_layout()
    fig.savefig(filename, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return filename


# ── ESTILOS ───────────────────────────────────────────────────────────────────

def get_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "titulo_doc": ParagraphStyle("titulo_doc", parent=base["Title"],
            fontSize=18, textColor=C_AZUL, alignment=TA_CENTER,
            spaceAfter=4, fontName="Helvetica-Bold"),
        "subtitulo_doc": ParagraphStyle("subtitulo_doc", parent=base["Normal"],
            fontSize=13, textColor=C_AZUL, alignment=TA_CENTER,
            spaceAfter=6, fontName="Helvetica-Bold"),
        "intro": ParagraphStyle("intro", parent=base["Normal"],
            fontSize=9.5, leading=14, textColor=C_GRIS_OSC, alignment=TA_JUSTIFY,
            fontName="Helvetica", spaceAfter=6),
        "perfil_nombre": ParagraphStyle("perfil_nombre", parent=base["Normal"],
            fontSize=10, fontName="Helvetica-Bold", textColor=C_AZUL, spaceAfter=2),
        "cuerpo": ParagraphStyle("cuerpo", parent=base["Normal"],
            fontSize=9, leading=13, textColor=C_TEXTO, alignment=TA_JUSTIFY,
            fontName="Helvetica"),
        "conclusion": ParagraphStyle("conclusion", parent=base["Normal"],
            fontSize=9, leading=13.5, textColor=C_TEXTO, alignment=TA_JUSTIFY,
            fontName="Helvetica", spaceAfter=4),
        "label_tabla": ParagraphStyle("label_tabla", parent=base["Normal"],
            fontSize=8.5, fontName="Helvetica", textColor=C_TEXTO),
        "disclaimer": ParagraphStyle("disclaimer", parent=base["Normal"],
            fontSize=8.5, leading=12.5, textColor=C_GRIS_OSC, alignment=TA_JUSTIFY,
            fontName="Helvetica"),
        "meta": ParagraphStyle("meta", parent=base["Normal"],
            fontSize=9, textColor=colors.HexColor("#546E7A"), fontName="Helvetica"),
        "pie": ParagraphStyle("pie", parent=base["Normal"],
            fontSize=7.5, textColor=colors.HexColor("#757575"),
            alignment=TA_CENTER, fontName="Helvetica"),
    }


class ColorHeader(Flowable):
    def __init__(self, text, bg_color, text_color=colors.white,
                 height=18, font_size=10):
        super().__init__()
        self.text       = text
        self.bg_color   = bg_color
        self.text_color = text_color
        self.height     = height
        self.font_size  = font_size

    def wrap(self, avail_w, avail_h):
        self.width = avail_w
        return avail_w, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg_color)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setFillColor(self.text_color)
        c.setFont("Helvetica-Bold", self.font_size)
        c.drawString(8, 4, self.text)


# ── BLOQUES REUTILIZABLES ─────────────────────────────────────────────────────

def ficha_meta(datos: list, styles: dict) -> Table:
    td = [(Paragraph(f"<b>{k}</b>", styles["label_tabla"]),
           Paragraph(v, styles["label_tabla"])) for k, v in datos]
    t = Table(td, colWidths=[4 * cm, 13 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), C_GRIS),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def tabla_distribucion(counter: Counter, styles: dict, total: int) -> Table:
    header = [
        Paragraph("<b>Perfil</b>", styles["label_tabla"]),
        Paragraph("<b>n</b>",      styles["label_tabla"]),
        Paragraph("<b>%</b>",      styles["label_tabla"]),
    ]
    rows = [header]
    for perfil, n in counter.most_common():
        pct = n / total * 100 if total else 0
        rows.append([
            Paragraph(perfil, styles["label_tabla"]),
            Paragraph(str(n), styles["label_tabla"]),
            Paragraph(f"{pct:.1f}%", styles["label_tabla"]),
        ])
    t = Table(rows, colWidths=[11 * cm, 2 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), C_AZUL),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, C_GRIS]),
        ("GRID",         (0, 0), (-1, -1), 0.3, C_BORDE),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
    ]))
    return t


def seccion_componente(nombre: str, counter: Counter, total: int,
                        styles: dict, tmp_dir: str, comp_key: str,
                        descripcion: str = "") -> list:
    color = COMP_COLORS.get(comp_key, C_AZUL)
    story = []
    story.append(Spacer(1, 6))
    story.append(ColorHeader(nombre, color))
    story.append(Spacer(1, 4))
    if descripcion:
        story.append(Paragraph(descripcion, styles["cuerpo"]))
        story.append(Spacer(1, 6))
    if counter and sum(counter.values()) > 0:
        chart_path = os.path.join(tmp_dir, f"chart_{comp_key.replace(' ', '_')}.png")
        make_bar_chart(counter, "", chart_path,
                       width=14, height=max(3, len(counter) * 1.1 + 1.5))
        if os.path.exists(chart_path):
            story.append(Image(chart_path, width=16 * cm,
                               height=max(4, len(counter) * 1.5 + 2) * cm))
            story.append(Spacer(1, 4))
        story.append(tabla_distribucion(counter, styles, total))
    else:
        story.append(Paragraph("Sin datos disponibles.", styles["cuerpo"]))
    return story


def bloque_conclusion(todos_perfiles: list, total: int, styles: dict,
                      nivel: str = "institución") -> list:
    if not todos_perfiles or total == 0:
        return []

    story = []
    story.append(Spacer(1, 10))
    story.append(ColorHeader("Síntesis y Recomendaciones Pedagógicas",
                              C_GRIS_OSC, height=22, font_size=10))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"A partir del análisis del Cuestionario Diagnóstico EAMH aplicado a <b>{total} "
        f"estudiantes</b> en este {nivel}, se identifican los siguientes patrones "
        f"predominantes y recomendaciones pedagógicas:",
        styles["conclusion"]))
    story.append(Spacer(1, 6))

    # Motivación
    mot_c = Counter(p["Motivación"][0] for p in todos_perfiles
                    if p.get("Motivación") and p["Motivación"][0] != "Sin clasificar")
    if mot_c:
        top, n = mot_c.most_common(1)[0]
        pct = n / total * 100
        if "intrínseca" in top:
            obs = (f"El <b>{pct:.0f}%</b> de los estudiantes ({n} de {total}) presenta "
                   f"orientación motivacional intrínseca, lo que constituye una fortaleza "
                   f"significativa para el aprendizaje autónomo. Se recomienda potenciar "
                   f"experiencias que ofrezcan autonomía, elección y retos significativos "
                   f"para consolidar y profundizar esta disposición positiva hacia el saber.")
        elif "extrínseco" in top:
            obs = (f"El <b>{pct:.0f}%</b> de los estudiantes ({n} de {total}) presenta "
                   f"orientación motivacional extrínseca. Su compromiso académico está "
                   f"sostenido principalmente por incentivos externos. Se recomienda "
                   f"implementar proyectos de interés personal, aprendizaje basado en "
                   f"problemas y reconocimiento de logros propios, transfiriendo gradualmente "
                   f"el valor hacia la tarea misma.")
        else:
            obs = (f"El <b>{pct:.0f}%</b> de los estudiantes ({n} de {total}) presenta "
                   f"orientación motivacional mixta o situada, respondiendo a motivadores "
                   f"internos y externos según el contexto. Se recomienda variar los ambientes "
                   f"y formatos de aprendizaje para aprovechar ambas fuentes de motivación.")
        story.append(Paragraph(f"<b>Orientación motivacional:</b> {obs}",
                                styles["conclusion"]))
        story.append(Spacer(1, 5))

    # Habilidades cognitivas
    hab_c = Counter(p["Habilidades"][0] for p in todos_perfiles
                    if p.get("Habilidades") and p["Habilidades"][0] != "Sin clasificar")
    if hab_c:
        top, n = hab_c.most_common(1)[0]
        pct = n / total * 100
        if "alta confianza" in top:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) presenta alta autopercepción "
                   f"de confianza cognitiva. Este grupo puede beneficiarse de retos "
                   f"académicos más complejos, roles de liderazgo en actividades "
                   f"colaborativas y proyectos de investigación que canalicen su "
                   f"confianza hacia la profundización del aprendizaje.")
        elif "diferenciación" in top:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) se encuentra en proceso "
                   f"de diferenciación cognitiva, construyendo su autopercepción como "
                   f"aprendiz. Se recomienda acompañamiento metacognitivo que ayude a "
                   f"identificar fortalezas propias y desarrollar estrategias de "
                   f"aprendizaje personalizadas.")
        else:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) percibe necesidad de "
                   f"regulación externa en sus procesos cognitivos. Es fundamental "
                   f"diseñar andamiajes pedagógicos claros, rutinas estructuradas e "
                   f"instrucciones paso a paso que fortalezcan progresivamente "
                   f"la autonomía cognitiva.")
        story.append(Paragraph(f"<b>Habilidades cognitivas:</b> {obs}",
                                styles["conclusion"]))
        story.append(Spacer(1, 5))

    # Estilos de aprendizaje
    est_c = Counter(p["Estilos"][0] for p in todos_perfiles
                    if p.get("Estilos") and p["Estilos"][0] != "Sin clasificar")
    if est_c:
        top, n = est_c.most_common(1)[0]
        pct = n / total * 100
        if "Visual" in top:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) prefiere el canal visual. "
                   f"Se recomienda privilegiar recursos gráficos, infografías, esquemas, "
                   f"mapas conceptuales y presentaciones visuales en el diseño de "
                   f"materiales y actividades didácticas.")
        elif "Auditivo" in top:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) prefiere el canal auditivo. "
                   f"Se recomienda incorporar explicaciones orales detalladas, discusiones "
                   f"grupales, podcasts educativos y recursos de escucha activa en las "
                   f"estrategias de enseñanza.")
        else:
            obs = (f"El <b>{pct:.0f}%</b> ({n} estudiantes) prefiere el canal kinestésico. "
                   f"Se recomienda diseñar actividades manipulativas, experimentales y "
                   f"de aprendizaje activo que favorezcan la comprensión a través de "
                   f"la experiencia directa y el movimiento.")
        story.append(Paragraph(f"<b>Estilos de aprendizaje:</b> {obs}",
                                styles["conclusion"]))
        story.append(Spacer(1, 5))

    # Vinculación afectiva
    soc15_c = Counter(p["Socioemocional 15"][0] for p in todos_perfiles
                      if p.get("Socioemocional 15") and
                      p["Socioemocional 15"][0] != "Sin clasificar")
    if soc15_c:
        n_pos = sum(v for k, v in soc15_c.items()
                    if "muy buena" in k or ("buena" in k and "muy" not in k))
        pct_pos = n_pos / total * 100
        n_des = soc15_c.get("Vinculación afectiva escolar desfavorable", 0)
        pct_des = n_des / total * 100
        if pct_pos >= 60:
            obs = (f"El <b>{pct_pos:.0f}%</b> de los estudiantes reporta vinculación "
                   f"afectiva escolar positiva (buena o muy buena). Este es un factor "
                   f"protector del bienestar y la permanencia escolar. Se recomienda "
                   f"mantener y fortalecer el clima institucional y el vínculo "
                   f"docente-estudiante como condición para el aprendizaje efectivo.")
        else:
            obs = (f"Se identifica una señal de alerta socioemocional con un "
                   f"<b>{pct_des:.0f}%</b> de estudiantes en vinculación afectiva "
                   f"desfavorable. Esto requiere intervención prioritaria desde el "
                   f"acompañamiento, el clima de aula, las estrategias de acogida y "
                   f"el fortalecimiento del sentido de pertenencia institucional.")
        story.append(Paragraph(f"<b>Vinculación afectiva escolar:</b> {obs}",
                                styles["conclusion"]))

    return story


def bloque_advertencia(styles: dict) -> list:
    story = []
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=1.2, color=C_GRIS_OSC))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Advertencia Pedagógica e Institucional</b>",
                            styles["subtitulo_doc"]))
    story.append(Spacer(1, 6))
    for par in DISCLAIMER:
        story.append(Paragraph(par, styles["disclaimer"]))
        story.append(Spacer(1, 5))
    return story


# ── HEADER / FOOTER CON LOGOS ─────────────────────────────────────────────────

def on_page(canvas, doc, nivel_texto: str):
    canvas.saveState()
    w, h = A4

    # Barra superior azul
    canvas.setFillColor(C_AZUL)
    canvas.rect(0, h - 1.8 * cm, w, 1.8 * cm, fill=1, stroke=0)

    # Logo izquierda
    if os.path.exists(LOGO_IZQ):
        try:
            canvas.drawImage(LOGO_IZQ, 0.3 * cm, h - 1.7 * cm,
                             width=1.3 * cm, height=1.4 * cm,
                             preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawCentredString(w / 2, h - 0.9 * cm,
                             "Cuestionario Diagnóstico EAMH – Aprendizaje Autónomo")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(w / 2, h - 1.4 * cm, nivel_texto)

    # Logo derecha
    if os.path.exists(LOGO_DER):
        try:
            canvas.drawImage(LOGO_DER, w - 1.6 * cm, h - 1.7 * cm,
                             width=1.3 * cm, height=1.4 * cm,
                             preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

    # Pie de página
    canvas.setFillColor(C_GRIS)
    canvas.rect(0, 0, w, 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#757575"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1 * cm, 0.32 * cm, "Documento de uso interno | Ciclo 1 · 2025")
    canvas.drawRightString(w - 1 * cm, 0.32 * cm, f"Pág. {doc.page}")
    canvas.restoreState()


def portada_logos(styles: dict) -> list:
    """Bloque de logos para portada de documentos."""
    story = []
    tiene_izq = os.path.exists(LOGO_IZQ)
    tiene_der = os.path.exists(LOGO_DER)
    if not (tiene_izq or tiene_der):
        return story

    celdas = []
    if tiene_izq:
        celdas.append(Image(LOGO_IZQ, width=3 * cm, height=2.5 * cm,
                            kind="proportional"))
    else:
        celdas.append(Spacer(3 * cm, 2.5 * cm))

    celdas.append(Spacer(1, 1))

    if tiene_der:
        celdas.append(Image(LOGO_DER, width=3 * cm, height=2.5 * cm,
                            kind="proportional"))
    else:
        celdas.append(Spacer(3 * cm, 2.5 * cm))

    t = Table([celdas], colWidths=[3.5 * cm, 10 * cm, 3.5 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",  (0, 0), (0, 0),   "LEFT"),
        ("ALIGN",  (2, 0), (2, 0),   "RIGHT"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))
    return story


# ── REPORTE INDIVIDUAL ────────────────────────────────────────────────────────

def report_estudiante(row: pd.Series, perfiles: dict, styles: dict,
                       out_path: str, tmp_dir: str):
    nombre  = row["Nombre"]
    grado   = row["Grado"]
    salon   = row["Salon"]
    inst    = row["Institución"]
    edad    = row.get("Edad", "N/D")

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            topMargin=2.1 * cm, bottomMargin=1.2 * cm,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    nivel_txt = f"{inst} · Grado {grado}° – Grupo {salon}"
    story = []

    story += portada_logos(styles)
    story.append(Paragraph("Reporte Individual de Aprendizaje", styles["titulo_doc"]))
    story.append(Paragraph("Cuestionario Diagnóstico EAMH – Aprendizaje Autónomo",
                            styles["subtitulo_doc"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_AZUL))
    story.append(Spacer(1, 0.4 * cm))

    story.append(ficha_meta([
        ("Estudiante",  f"<b>{nombre}</b>"),
        ("Institución", inst),
        ("Grado",       f"{grado}°"),
        ("Grupo",       salon),
        ("Edad",        str(edad)),
    ], styles))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "El presente reporte presenta el perfil diagnóstico del estudiante en cuatro dimensiones "
        "del aprendizaje autónomo: orientación motivacional, autopercepción de habilidades "
        "cognitivas, estilos de aprendizaje y dimensión socioemocional. Los resultados reflejan "
        "la autopercepción del estudiante y deben ser interpretados como un insumo pedagógico "
        "orientador, no como una evaluación definitiva.", styles["intro"]))
    story.append(Spacer(1, 0.3 * cm))

    sections = [
        ("Componente 1: Orientación Motivacional",
         "Motivación", "Motivación",
         "Refleja si el impulso del estudiante hacia el aprendizaje proviene principalmente "
         "de factores externos (reconocimiento, recompensas, notas) o internos (curiosidad, "
         "satisfacción personal, interés genuino). La motivación intrínseca favorece el "
         "aprendizaje autónomo y la autorregulación."),
        ("Componente 2: Autopercepción de Habilidades Cognitivas",
         "Habilidades", "Habilidades",
         "Muestra la autopercepción del estudiante sobre las habilidades cognitivas en las "
         "que se siente más competente o confiado. No evalúa el desempeño real sino la "
         "forma en que el estudiante se percibe a sí mismo como aprendiz."),
        ("Componente 3: Preferencias en Estilos de Aprendizaje",
         "Estilos", "Estilos",
         "Indica el canal de presentación de los objetos de aprendizaje con el que el "
         "estudiante se siente más cómodo: visual (imágenes, gráficos), auditivo "
         "(explicaciones orales) o kinestésico (manipulación, experiencia directa)."),
        ("Subcomponente Socioemocional – Relación con Pares (Ítem 13)",
         "Socioemocional 13", "Socioemocional 13",
         "Preferencia del estudiante por trabajar de forma cooperativa o individual."),
        ("Subcomponente Socioemocional – Autoconfianza ante el Desafío (Ítem 14)",
         "Socioemocional 14", "Socioemocional 14",
         "Percepción del estudiante sobre su propia capacidad al enfrentar retos académicos."),
        ("Subcomponente Socioemocional – Vinculación Afectiva Escolar (Ítem 15)",
         "Socioemocional 15", "Socioemocional 15",
         "Estado de ánimo y vínculo afectivo general del estudiante con la institución."),
    ]

    for titulo_largo, clave, comp_key, desc_comp in sections:
        color = COMP_COLORS.get(comp_key, C_AZUL)
        perfil = perfiles.get(clave, ("Sin clasificar", ""))
        nombre_perf, desc_perf = perfil
        story.append(Spacer(1, 4))
        story.append(ColorHeader(titulo_largo, color, height=17, font_size=9))
        story.append(Spacer(1, 3))
        story.append(Paragraph(desc_comp, styles["cuerpo"]))
        story.append(Spacer(1, 3))
        story.append(Paragraph(f"<b>Perfil identificado:</b> {nombre_perf}",
                                styles["perfil_nombre"]))
        if desc_perf:
            story.append(Paragraph(desc_perf, styles["cuerpo"]))
        story.append(Spacer(1, 2))

    story += bloque_advertencia(styles)

    doc.build(story,
              onFirstPage=lambda c, d: on_page(c, d, nivel_txt),
              onLaterPages=lambda c, d: on_page(c, d, nivel_txt))


# ── REPORTE AGREGADO (institución / grado / grupo) ────────────────────────────

def report_agregado(df_grupo: pd.DataFrame, todos_perfiles: list,
                    titulo: str, subtitulo: str, nivel_txt: str,
                    out_path: str, tmp_dir: str, styles: dict,
                    meta_extra: list = None, con_conclusion: bool = True):
    total = len(df_grupo)
    doc = SimpleDocTemplate(out_path, pagesize=A4,
                            topMargin=2.1 * cm, bottomMargin=1.2 * cm,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    # Portada
    story += portada_logos(styles)
    story.append(Paragraph(titulo, styles["titulo_doc"]))
    story.append(Paragraph("Cuestionario Diagnóstico EAMH – Aprendizaje Autónomo",
                            styles["subtitulo_doc"]))
    story.append(Paragraph(subtitulo, styles["subtitulo_doc"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_AZUL))
    story.append(Spacer(1, 0.4 * cm))

    meta = [("Total estudiantes", str(total))]
    if meta_extra:
        meta = meta_extra + meta
    story.append(ficha_meta(meta, styles))
    story.append(Spacer(1, 0.3 * cm))

    # Introducción
    if con_conclusion:
        story.append(Paragraph(
            "El presente informe sintetiza los resultados del Cuestionario Diagnóstico EAMH "
            "aplicado al conjunto de estudiantes indicado. Presenta la distribución de perfiles "
            "en cuatro dimensiones del aprendizaje autónomo y una síntesis pedagógica con "
            "recomendaciones específicas para orientar la práctica docente y la planificación "
            "curricular.", styles["intro"]))
        story.append(Spacer(1, 0.3 * cm))

    # Por componente
    for clave, (titulo_comp, desc_comp) in COMP_DESCRIPTIONS.items():
        counter = Counter(p[clave][0] for p in todos_perfiles
                          if p.get(clave) and p[clave][0] != "Sin clasificar")
        story += seccion_componente(titulo_comp, counter, total,
                                     styles, tmp_dir, clave, desc_comp)

    # Conclusión
    if con_conclusion:
        nivel_label = "nivel institucional" if "Institución" in titulo else "grado"
        story += bloque_conclusion(todos_perfiles, total, styles, nivel_label)

    # Listado de estudiantes
    story.append(PageBreak())
    story.append(ColorHeader("Listado de Estudiantes y Perfiles Diagnósticos",
                              C_AZUL, height=22, font_size=10))
    story.append(Spacer(1, 6))

    header_row = [
        Paragraph("<b>Nombre</b>",      styles["label_tabla"]),
        Paragraph("<b>Grado</b>",       styles["label_tabla"]),
        Paragraph("<b>Grp</b>",         styles["label_tabla"]),
        Paragraph("<b>Motivación</b>",  styles["label_tabla"]),
        Paragraph("<b>Habilidades</b>", styles["label_tabla"]),
        Paragraph("<b>Estilos</b>",     styles["label_tabla"]),
    ]
    table_rows = [header_row]
    for (_, row), perfiles in zip(df_grupo.iterrows(), todos_perfiles):
        def sht(s, n=22):
            return s[:n] + "…" if len(s) > n else s
        table_rows.append([
            Paragraph(sht(row["Nombre"], 28), styles["label_tabla"]),
            Paragraph(f"{row['Grado']}°",     styles["label_tabla"]),
            Paragraph(row["Salon"],            styles["label_tabla"]),
            Paragraph(sht(perfiles["Motivación"][0]),  styles["label_tabla"]),
            Paragraph(sht(perfiles["Habilidades"][0]), styles["label_tabla"]),
            Paragraph(sht(perfiles["Estilos"][0]),     styles["label_tabla"]),
        ])

    t = Table(table_rows, colWidths=[5.5*cm, 1.5*cm, 1*cm, 4*cm, 4*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_AZUL),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, C_GRIS]),
        ("GRID",          (0, 0), (-1, -1), 0.3, C_BORDE),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
    ]))
    story.append(t)

    story += bloque_advertencia(styles)

    doc.build(story,
              onFirstPage=lambda c, d: on_page(c, d, nivel_txt),
              onLaterPages=lambda c, d: on_page(c, d, nivel_txt))


# ── ORQUESTADOR ───────────────────────────────────────────────────────────────

def sanitize(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name.strip())


def generar_todos(verbose=True):
    tmp_dir = tempfile.mkdtemp(prefix="ciclo1_charts_")
    styles  = get_styles()

    if not CSV_FINALES:
        print("ERROR: No se encontraron archivos 'Tabulación * FINAL.csv'")
        return

    if verbose:
        print("Cargando datos de todas las instituciones…")
    casos  = load_casos()
    df_all = load_all_estudiantes()

    instituciones = sorted(df_all["Institución"].unique())
    if verbose:
        print(f"Instituciones: {instituciones}")
        print(f"Total estudiantes: {len(df_all)}\n")

    for inst_name in instituciones:
        df = df_all[df_all["Institución"] == inst_name].reset_index(drop=True)
        todos_perfiles = [clasificar_estudiante(row, casos) for _, row in df.iterrows()]
        inst_safe = sanitize(inst_name)
        inst_dir  = os.path.join(OUT_DIR, inst_safe)
        os.makedirs(inst_dir, exist_ok=True)

        if verbose:
            print(f"═══ {inst_name} ({len(df)} est.) ═══")

        # Reporte institucional
        out_inst = os.path.join(inst_dir, f"reporte_institucion_{inst_safe}.pdf")
        report_agregado(df, todos_perfiles,
                        titulo="Reporte Institucional de Diagnóstico",
                        subtitulo=inst_name, nivel_txt="Reporte Institucional",
                        out_path=out_inst, tmp_dir=tmp_dir, styles=styles,
                        meta_extra=[("Institución", inst_name)],
                        con_conclusion=True)
        if verbose:
            print(f"  ✓ Institucional")

        # Por grado
        grados = sorted(df["Grado"].unique(),
                        key=lambda x: int(x) if x.isdigit() else x)
        for grado in grados:
            mask_g = df["Grado"] == grado
            df_g   = df[mask_g].reset_index(drop=True)
            pf_g   = [p for p, m in zip(todos_perfiles, mask_g) if m]
            label_g = f"Grado {grado}°"

            grado_dir = os.path.join(inst_dir, f"grado_{grado}")
            os.makedirs(grado_dir, exist_ok=True)

            out_grado = os.path.join(grado_dir, f"reporte_grado_{grado}.pdf")
            report_agregado(df_g, pf_g,
                            titulo=f"Reporte por Grado – {label_g}",
                            subtitulo=inst_name, nivel_txt=label_g,
                            out_path=out_grado, tmp_dir=tmp_dir, styles=styles,
                            meta_extra=[("Institución", inst_name),
                                        ("Grado", f"{grado}°")],
                            con_conclusion=True)
            if verbose:
                print(f"  ✓ {label_g} ({len(df_g)} est.)")

            # Por grupo
            salones = sorted(df_g["Salon"].unique(),
                             key=lambda x: int(x) if x.isdigit() else x)
            for salon in salones:
                mask_s  = df_g["Salon"] == salon
                df_s    = df_g[mask_s].reset_index(drop=True)
                pf_s    = [p for p, m in zip(pf_g, mask_s) if m]
                label_s = f"Grado {grado}° – Grupo {salon}"

                salon_dir = os.path.join(grado_dir, f"grupo_{salon}")
                os.makedirs(salon_dir, exist_ok=True)

                out_salon = os.path.join(
                    salon_dir, f"reporte_grado{grado}_grupo{salon}.pdf")
                report_agregado(df_s, pf_s,
                                titulo=f"Reporte por Grupo – {label_s}",
                                subtitulo=inst_name, nivel_txt=label_s,
                                out_path=out_salon, tmp_dir=tmp_dir, styles=styles,
                                meta_extra=[("Institución", inst_name),
                                            ("Grado", f"{grado}°"),
                                            ("Grupo", salon)],
                                con_conclusion=False)

                # Por estudiante
                est_dir = os.path.join(salon_dir, "estudiantes")
                os.makedirs(est_dir, exist_ok=True)
                for (_, row_e), pf_e in zip(df_s.iterrows(), pf_s):
                    nombre_safe = sanitize(row_e["Nombre"])[:60]
                    out_est = os.path.join(est_dir, f"estudiante_{nombre_safe}.pdf")
                    report_estudiante(row_e, pf_e, styles, out_est, tmp_dir)

        if verbose:
            n_inst = sum(len(fs) for _, _, fs in os.walk(inst_dir))
            print(f"  → {n_inst} PDFs en {inst_safe}/\n")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    if verbose:
        n_total = sum(len(fs) for _, _, fs in os.walk(OUT_DIR))
        print(f"✓ TOTAL PDFs generados: {n_total}")


if __name__ == "__main__":
    generar_todos(verbose=True)
