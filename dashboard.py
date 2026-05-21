#!/usr/bin/env python3
"""
Informe Interactivo Diagnóstico EAMH – Ciclo 1
Ciclo 1 · I.E. Felipe de Restrepo
"""

import os
import csv
from collections import defaultdict, Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Informe Interactivo Diagnóstico EAMH – Ciclo 1",
    page_icon="📊",
    layout="centered",
)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_CASOS  = os.path.join(BASE_DIR, "Caos de respuesta Cuestionario Ciclo 1.csv")
CSV_TABUL  = os.path.join(BASE_DIR, "Tabulación Felipe(Felipe de Restrepo).csv")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Encabezado principal */
.header-banner {
    background: linear-gradient(135deg, #0D47A1 0%, #1565C0 60%, #1976D2 100%);
    border-radius: 12px;
    padding: 24px 28px 20px 28px;
    margin-bottom: 24px;
    color: white;
}
.header-banner h1 {
    color: white !important;
    font-size: 1.6rem;
    margin: 0 0 4px 0;
}
.header-banner p {
    color: #BBDEFB;
    margin: 0;
    font-size: 0.9rem;
}

/* Métricas */
[data-testid="metric-container"] {
    background: white;
    border: 1.5px solid #90CAF9;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="metric-container"] label {
    color: #1565C0 !important;
    font-weight: 600;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1A237E !important;
}
[data-testid="stSidebar"] * {
    color: #E3F2FD !important;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background-color: #1565C0 !important;
}

/* Tabs */
[data-testid="stTab"] {
    font-weight: 600;
    color: #1565C0;
}

/* Divider */
hr { border-color: #BBDEFB !important; }
</style>
""", unsafe_allow_html=True)

PROFILE_COLORS = {
    "Orientación motivacional extrínseco":              "#E65100",
    "Orientación motivacional intrínseca":              "#2E7D32",
    "Orientación motivacional mixta o situada":         "#F9A825",
    "Autopercepción de alta confianza cognitiva":                      "#2E7D32",
    "Autopercepción cognitiva en proceso de diferenciación":           "#F9A825",
    "Autopercepción de necesidad de regulación externa":               "#E65100",
    "Preferencia  por lo  Visual":      "#1565C0",
    "Preferencia  por lo Auditivo":     "#6A1B9A",
    "Preferencia por lo Kinestésico":   "#00838F",
    "Preferencia por el aprendizaje cooperativo":   "#2E7D32",
    "Preferencia por el aprendizaje individual":    "#F9A825",
    "Percepción de  autoconfianza  ante el desafío":    "#2E7D32",
    "Percepción vulnerabilidad ante el desafio":        "#E65100",
    "Vinculación afectiva escolar muy buena":    "#1B5E20",
    "Vinculación afectiva escolar buena":        "#2E7D32",
    "Vinculación afectiva escolar regular":      "#F9A825",
    "Vinculación afectiva escolar desfavorable": "#E65100",
}

COMPONENTES = [
    ("Motivación",        "Componente 1: Motivación"),
    ("Habilidades",       "Componente 2: Habilidades Cognitivas"),
    ("Estilos",           "Componente 3: Estilos de Aprendizaje"),
    ("Socioemocional 13", "Rel. con pares (Ítem 13)"),
    ("Socioemocional 14", "Autoconfianza ante el desafío (Ítem 14)"),
    ("Socioemocional 15", "Vinculación afectiva escolar (Ítem 15)"),
]

# ── CARGA ─────────────────────────────────────────────────────────────────────

@st.cache_data
def load_casos():
    casos = defaultdict(dict)
    with open(CSV_CASOS, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        for row in reader:
            if len(row) < 4:
                continue
            comp, clave, nombre, desc = (
                row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            )
            casos[comp][clave] = (nombre, desc)
    return dict(casos)


@st.cache_data
def load_df():
    df = pd.read_csv(CSV_TABUL, sep=";", encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df["Grado"]  = df["Grupo"].apply(lambda x: x.split(";")[0].strip() if ";" in x else x.strip())
    df["Salon"]  = df["Grupo"].apply(lambda x: x.split(";")[1].strip() if ";" in x else "1")
    df["Nombre"] = df["Nombre"].str.strip()
    for col in [f"P{i}" for i in range(1, 16)]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def clasificar(row, casos):
    p = {}
    clave_mot = f"{row['P1']}-{row['P2']}-{row['P3']}-{row['P4']}"
    p["Motivación"] = casos.get("Componente 1: Motivación", {}).get(clave_mot, ("Sin clasificar", ""))

    clave_hab = "-".join(str(row[f"P{i}"]) for i in range(5, 12))
    p["Habilidades"] = casos.get("Componente 2: Habilidades Cognitivas", {}).get(clave_hab, ("Sin clasificar", ""))

    clave_est = str(row["P12"])
    p["Estilos"] = casos.get("Componente 3: Estilos de Aprendizaje", {}).get(clave_est, ("Sin clasificar", ""))

    for item, col in [("13", "P13"), ("14", "P14"), ("15", "P15")]:
        p[f"Socioemocional {item}"] = casos.get(
            f"Subcomponente Socioemocional (Ítem {item})", {}
        ).get(str(row[col]), ("Sin clasificar", ""))
    return p


@st.cache_data
def build_data():
    casos = load_casos()
    df    = load_df()
    perfiles = [clasificar(row, casos) for _, row in df.iterrows()]
    for key, _ in COMPONENTES:
        df[key] = [p[key][0] for p in perfiles]
    df["_perfiles"] = [p for p in perfiles]
    return df


# ── GRÁFICAS ──────────────────────────────────────────────────────────────────

def chart_barras(series: pd.Series, titulo: str):
    counts = series.value_counts().reset_index()
    counts.columns = ["Perfil", "n"]
    total = counts["n"].sum()
    counts["%"] = (counts["n"] / total * 100).round(1)
    counts["color"] = counts["Perfil"].map(lambda x: PROFILE_COLORS.get(x, "#90A4AE"))

    fig = px.bar(
        counts, x="%", y="Perfil", orientation="h",
        color="Perfil",
        color_discrete_map={row["Perfil"]: row["color"] for _, row in counts.iterrows()},
        text=counts.apply(lambda r: f"{r['%']}% (n={r['n']})", axis=1),
        title=titulo,
    )
    fig.update_traces(textposition="outside", showlegend=False)
    fig.update_layout(
        xaxis_title="%", yaxis_title="",
        margin=dict(l=20, r=30, t=60, b=20),
        height=max(250, len(counts) * 65 + 100),
        plot_bgcolor="#F0F5FF",
        title=dict(font=dict(size=16)),
        yaxis=dict(automargin=True, tickfont=dict(size=12)),
    )
    fig.update_xaxes(range=[0, 125], showgrid=True, gridcolor="#BBDEFB")
    return fig


def chart_dona(series: pd.Series, titulo: str):
    counts = series.value_counts().reset_index()
    counts.columns = ["Perfil", "n"]
    colors = [PROFILE_COLORS.get(p, "#90A4AE") for p in counts["Perfil"]]
    fig = go.Figure(go.Pie(
        labels=counts["Perfil"], values=counts["n"],
        hole=0.5, marker_colors=colors,
        textinfo="percent", hoverinfo="label+value+percent",
    ))
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=16)),
        margin=dict(l=20, r=20, t=60, b=40),
        height=380,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.18, font_size=11),
        showlegend=True,
    )
    return fig


# ── MÉTRICAS KPI ──────────────────────────────────────────────────────────────

def kpi_cards(df_f: pd.DataFrame):
    total = len(df_f)
    mot_int = (df_f["Motivación"] == "Orientación motivacional intrínseca").sum()
    conf_alt = (df_f["Habilidades"] == "Autopercepción de alta confianza cognitiva").sum()
    vinc_buena = df_f["Socioemocional 15"].isin(
        ["Vinculación afectiva escolar muy buena", "Vinculación afectiva escolar buena"]
    ).sum()

    c1, c2 = st.columns(2)
    c1.metric("Estudiantes analizados", total)
    c2.metric("Motivación intrínseca", f"{mot_int/total*100:.0f}%",
              help=f"{mot_int} de {total} estudiantes")
    c3, c4 = st.columns(2)
    c3.metric("Alta confianza cognitiva", f"{conf_alt/total*100:.0f}%",
              help=f"{conf_alt} de {total} estudiantes")
    c4.metric("Vinculación buena/muy buena", f"{vinc_buena/total*100:.0f}%",
              help=f"{vinc_buena} de {total} estudiantes")


# ── TABLA DE ESTUDIANTES ──────────────────────────────────────────────────────

def tabla_estudiantes(df_f: pd.DataFrame):
    cols_show = ["Nombre", "Grado", "Salon",
                 "Motivación", "Habilidades", "Estilos",
                 "Socioemocional 13", "Socioemocional 14", "Socioemocional 15"]
    df_show = df_f[cols_show].copy()
    df_show = df_show.rename(columns={
        "Salon": "Grupo",
        "Socioemocional 13": "Rel. pares",
        "Socioemocional 14": "Autoconfianza",
        "Socioemocional 15": "Vinc. afectiva",
    })

    busqueda = st.text_input("Buscar estudiante por nombre", placeholder="Escribe un nombre…")
    if busqueda:
        df_show = df_show[df_show["Nombre"].str.contains(busqueda, case=False, na=False)]

    st.dataframe(df_show, use_container_width=True, hide_index=True, height=450)
    st.caption(f"{len(df_show)} estudiante(s) mostrado(s)")


# ── DETALLE ESTUDIANTE ────────────────────────────────────────────────────────

def detalle_estudiante(df_f: pd.DataFrame, casos: dict):
    nombres = sorted(df_f["Nombre"].tolist())
    sel = st.selectbox("Selecciona un estudiante", nombres)
    row = df_f[df_f["Nombre"] == sel].iloc[0]
    perfiles = clasificar(row, casos)

    st.markdown(f"### {row['Nombre']}")
    info_cols = st.columns(3)
    info_cols[0].markdown(f"**Institución:** {row['Institución']}")
    info_cols[1].markdown(f"**Grado:** {row['Grado']}° – Grupo {row['Salon']}")
    info_cols[2].markdown(f"**Grupo:** {row['Salon']}")

    st.divider()
    for clave, etiqueta in COMPONENTES:
        nombre_perfil, desc_perfil = perfiles[clave]
        color = PROFILE_COLORS.get(nombre_perfil, "#546E7A")
        with st.expander(f"**{etiqueta}** — {nombre_perfil}", expanded=True):
            st.markdown(
                f"<span style='display:inline-block;width:12px;height:12px;"
                f"background:{color};border-radius:50%;margin-right:6px'></span>"
                f"<strong>{nombre_perfil}</strong>",
                unsafe_allow_html=True,
            )
            if desc_perfil:
                st.markdown(desc_perfil)


# ── COMPARATIVO GRADOS ────────────────────────────────────────────────────────

def comparativo_grados(df: pd.DataFrame, componente: str):
    grados = sorted(df["Grado"].unique(), key=lambda x: int(x) if x.isdigit() else x)
    rows = []
    for g in grados:
        sub = df[df["Grado"] == g]
        c = sub[componente].value_counts(normalize=True).mul(100).reset_index()
        c.columns = ["Perfil", "%"]
        c["Grado"] = f"Grado {g}°"
        rows.append(c)
    if not rows:
        return None
    df_cmp = pd.concat(rows)
    colors = {p: PROFILE_COLORS.get(p, "#90A4AE") for p in df_cmp["Perfil"].unique()}
    fig = px.bar(
        df_cmp, x="Grado", y="%", color="Perfil",
        color_discrete_map=colors,
        barmode="stack", text_auto=".0f",
        title=f"Distribución de perfiles por grado – {componente}",
    )
    fig.update_layout(
        height=440, margin=dict(l=20, r=20, t=60, b=60),
        plot_bgcolor="#F0F5FF", yaxis_title="%",
        title=dict(font=dict(size=16)),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22, font_size=10),
    )
    fig.update_yaxes(range=[0, 105], showgrid=True, gridcolor="#BBDEFB")
    return fig


# ── APP PRINCIPAL ─────────────────────────────────────────────────────────────

def main():
    # ── Encabezado con logos opcionales ──────────────────────────────────────
    logo_izq = os.path.join(ASSETS_DIR, "logo_izquierda.png")
    logo_der = os.path.join(ASSETS_DIR, "logo_derecha.png")

    tiene_logos = os.path.exists(logo_izq) or os.path.exists(logo_der)
    if tiene_logos:
        col_titulo, col_logos = st.columns([5, 2])
        with col_titulo:
            st.markdown("""
            <div class="header-banner">
                <h1>📊 Informe Interactivo Diagnóstico EAMH</h1>
                <p>Ciclo 1 &nbsp;·&nbsp; I.E. Felipe de Restrepo &nbsp;·&nbsp; Aprendizaje Autónomo</p>
            </div>""", unsafe_allow_html=True)
        with col_logos:
            if os.path.exists(logo_izq):
                st.image(logo_izq, use_container_width=True)
            if os.path.exists(logo_der):
                st.image(logo_der, use_container_width=True)
    else:
        st.markdown("""
        <div class="header-banner">
            <h1>📊 Informe Interactivo Diagnóstico EAMH</h1>
            <p>Ciclo 1 &nbsp;·&nbsp; I.E. Felipe de Restrepo &nbsp;·&nbsp; Aprendizaje Autónomo</p>
        </div>""", unsafe_allow_html=True)
    st.divider()

    df_full = build_data()
    casos   = load_casos()

    # ── Sidebar: Filtros ──────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filtros")

        instituciones = sorted(df_full["Institución"].unique())
        inst_sel = st.multiselect("Institución", instituciones, default=instituciones)

        grados = sorted(df_full["Grado"].unique(), key=lambda x: int(x) if x.isdigit() else x)
        grado_sel = st.multiselect("Grado", grados, default=grados,
                                   format_func=lambda g: f"Grado {g}°")

        salones_disponibles = sorted(
            df_full[df_full["Grado"].isin(grado_sel)]["Salon"].unique(),
            key=lambda x: int(x) if x.isdigit() else x,
        )
        salon_sel = st.multiselect("Grupo", salones_disponibles,
                                   default=salones_disponibles,
                                   format_func=lambda s: f"Grupo {s}")

        st.divider()
        st.caption("Todos los filtros son acumulativos.")

    df_f = df_full[
        df_full["Institución"].isin(inst_sel) &
        df_full["Grado"].isin(grado_sel) &
        df_full["Salon"].isin(salon_sel)
    ].reset_index(drop=True)

    if df_f.empty:
        st.warning("No hay estudiantes para los filtros seleccionados.")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_res, tab_comp, tab_cmp, tab_est = st.tabs([
        "Resumen general",
        "Por componente",
        "Comparativo por grado",
        "Explorador de estudiantes",
    ])

    # ── Tab 1: Resumen ────────────────────────────────────────────────────────
    with tab_res:
        st.subheader("Indicadores clave")
        kpi_cards(df_f)
        st.divider()

        st.subheader("Componentes principales")

        charts_principales = [
            ("Motivación",  "Componente 1: Motivación"),
            ("Habilidades", "Componente 2: Habilidades Cognitivas"),
            ("Estilos",     "Componente 3: Estilos de Aprendizaje"),
        ]
        for clave, nombre in charts_principales:
            st.plotly_chart(
                chart_dona(df_f[clave], nombre),
                use_container_width=True,
            )
            st.divider()

        st.subheader("Dimensión socioemocional")

        socio_items = [
            ("Socioemocional 13", "Relación con pares (Ítem 13)"),
            ("Socioemocional 14", "Autoconfianza ante el desafío (Ítem 14)"),
            ("Socioemocional 15", "Vinculación afectiva escolar (Ítem 15)"),
        ]
        for clave, etiq in socio_items:
            st.plotly_chart(
                chart_dona(df_f[clave], etiq),
                use_container_width=True,
            )
            st.divider()

    # ── Tab 2: Por componente ─────────────────────────────────────────────────
    with tab_comp:
        clave_sel, etiq_sel = st.selectbox(
            "Componente",
            COMPONENTES,
            format_func=lambda x: x[1],
        )
        st.plotly_chart(
            chart_barras(df_f[clave_sel], etiq_sel),
            use_container_width=True,
        )
        st.divider()
        cnt = df_f[clave_sel].value_counts().reset_index()
        cnt.columns = ["Perfil", "n"]
        cnt["%"] = (cnt["n"] / len(df_f) * 100).round(1).astype(str) + "%"
        st.dataframe(cnt, hide_index=True, use_container_width=True)

    # ── Tab 3: Comparativo por grado ──────────────────────────────────────────
    with tab_cmp:
        clave_cmp, _ = st.selectbox(
            "Componente a comparar",
            COMPONENTES,
            format_func=lambda x: x[1],
            key="cmp_comp",
        )
        fig_cmp = comparativo_grados(df_f, clave_cmp)
        if fig_cmp:
            st.plotly_chart(fig_cmp, use_container_width=True)

        st.subheader("Tabla cruzada: Perfil × Grado")
        tabla_cruzada = (
            df_f.groupby(["Grado", clave_cmp])
            .size()
            .unstack(fill_value=0)
        )
        st.dataframe(tabla_cruzada, use_container_width=True)

    # ── Tab 4: Explorador de estudiantes ──────────────────────────────────────
    with tab_est:
        sub1, sub2 = st.tabs(["Tabla completa", "Perfil individual"])

        with sub1:
            st.subheader("Listado de estudiantes")
            tabla_estudiantes(df_f)

        with sub2:
            st.subheader("Detalle por estudiante")
            detalle_estudiante(df_f, casos)


if __name__ == "__main__":
    main()
