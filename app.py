"""Mundo SENAI — Fábrica Inteligente.
Demonstração educacional de software, controle e dados para uma célula robótica.
"""
from __future__ import annotations

import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Mundo SENAI | Fábrica Inteligente",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "robotica_senai.db"
ROBOTS = [f"ROBÔ-{i:02d}" for i in range(1, 7)]
STATIONS = {
    "1": "Controle da Produção",
    "2": "Controle dos Robôs",
    "3": "Central de Dados",
    "4": "Fábrica — Visão Geral",
}

st.markdown(
    """
<style>
:root {
  --bg:#07111f; --panel:#0e1a2b; --panel2:#132238; --line:#263850;
  --text:#f8fafc; --muted:#aebdd0; --blue:#60a5fa; --green:#34d399;
  --yellow:#fbbf24; --red:#fb7185;
}
.stApp { background:var(--bg); color:var(--text); }
.block-container { max-width:1600px; padding:1rem 1.8rem 2rem; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"] { visibility:hidden; }
section[data-testid="stSidebar"] { background:#08101d; }
section[data-testid="stSidebar"] * { color:var(--text); }
.factory-top {
  display:flex; justify-content:space-between; align-items:center; gap:1rem;
  padding:.8rem 1rem; margin-bottom:.8rem; border-bottom:1px solid var(--line);
}
.brand { color:#fff; font-weight:800; letter-spacing:.02em; font-size:1.05rem; }
.brand span { color:#8ea6c4; font-weight:500; }
.clock { color:#8ea6c4; font-size:.85rem; }
.title { margin:.3rem 0 .25rem; color:#fff; font-size:clamp(1.8rem,3vw,2.7rem); font-weight:850; }
.subtitle { color:var(--muted); margin:0 0 1.1rem; font-size:1rem; }
.panel {
  background:linear-gradient(180deg,var(--panel),#0b1727); border:1px solid var(--line);
  border-radius:16px; padding:1rem; height:100%; box-shadow:0 10px 30px rgba(0,0,0,.12);
}
.panel h3 { color:#fff; margin:.1rem 0 .55rem; }
.panel p { color:var(--muted); }
.kpi {
  background:var(--panel); border:1px solid var(--line); border-radius:14px;
  padding:.9rem 1rem; min-height:92px;
}
.kpi-label { color:#8fa2bb; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { color:#fff; font-size:1.65rem; font-weight:850; margin-top:.2rem; }
.kpi-note { color:#8fa2bb; font-size:.78rem; margin-top:.15rem; }
.robot-card { background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:.9rem; }
.robot-name { color:#fff; font-weight:800; font-size:1.05rem; }
.robot-meta { color:var(--muted); font-size:.85rem; }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.dot-ok { background:var(--green); } .dot-warn { background:var(--yellow); } .dot-err { background:var(--red); }
.event {
  background:#0b1e1a; border:1px solid #1c5948; border-radius:14px; padding:.8rem 1rem;
}
.event-label { color:#7ee7c1; font-size:.73rem; text-transform:uppercase; letter-spacing:.1em; }
.event-main { color:#fff; font-size:1.15rem; font-weight:800; margin-top:.15rem; }
.event-sub { color:#9cc9bb; font-size:.8rem; margin-top:.15rem; }
.helper { color:#8fa2bb; font-size:.82rem; margin-top:.25rem; }
[data-testid="stMetric"] { background:var(--panel)!important; border:1px solid var(--line)!important; border-radius:14px!important; }
[data-testid="stMetricLabel"] { color:#aebdd0!important; }
[data-testid="stMetricValue"] { color:#fff!important; }
.stDataFrame { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
button[kind="primary"] { min-height:3rem; }
</style>
""",
    unsafe_allow_html=True,
)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_database() -> None:
    conn = db()
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS robots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          status TEXT NOT NULL,
          battery REAL NOT NULL,
          temperature REAL NOT NULL,
          speed REAL NOT NULL,
          position_x REAL NOT NULL,
          position_y REAL NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS telemetry (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          robot_name TEXT NOT NULL,
          battery REAL NOT NULL,
          temperature REAL NOT NULL,
          speed REAL NOT NULL,
          position_x REAL NOT NULL,
          position_y REAL NOT NULL,
          status TEXT NOT NULL,
          event_type TEXT NOT NULL,
          message TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS commands (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          robot_name TEXT NOT NULL,
          command TEXT NOT NULL,
          parameter REAL,
          result TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS maintenance (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          robot_name TEXT NOT NULL,
          priority TEXT NOT NULL,
          title TEXT NOT NULL,
          status TEXT NOT NULL,
          assignee TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS system_state (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        """
    )
    if cur.execute("SELECT COUNT(*) FROM robots").fetchone()[0] == 0:
        now = datetime.now().isoformat(timespec="seconds")
        for i, robot in enumerate(ROBOTS):
            status = "Ativo" if i != 5 else "Manutenção"
            cur.execute(
                """INSERT INTO robots
                (name,status,battery,temperature,speed,position_x,position_y,updated_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    robot, status, random.uniform(72, 99), random.uniform(35, 48),
                    random.uniform(.2, 1.4) if status == "Ativo" else 0,
                    random.uniform(1, 9), random.uniform(1, 9), now,
                ),
            )
    if cur.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0] == 0:
        tasks = [
            ("ROBÔ-06", "Alta", "Inspeção do módulo de movimento", "Em andamento", "Equipe A"),
            ("ROBÔ-02", "Média", "Calibração do sensor de posição", "Aberto", "Equipe B"),
            ("ROBÔ-04", "Baixa", "Atualização da rotina de movimentação", "Aberto", "Equipe C"),
            ("ROBÔ-01", "Baixa", "Checklist de partida", "Concluído", "Equipe A"),
        ]
        for task in tasks:
            cur.execute(
                "INSERT INTO maintenance(robot_name,priority,title,status,assignee,created_at) VALUES(?,?,?,?,?,?)",
                (*task, datetime.now().isoformat(timespec="seconds")),
            )
    cur.execute("INSERT OR IGNORE INTO system_state(key,value) VALUES('last_tick','0')")
    conn.commit(); conn.close()


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = db()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def tick_telemetry(interval: float = 2.0) -> bool:
    conn = db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT value FROM system_state WHERE key='last_tick'").fetchone()
        last = float(row["value"] if row else 0)
        now_epoch = time.time()
        if now_epoch - last < interval:
            conn.rollback(); return False
        now = datetime.now().isoformat(timespec="seconds")
        rows = conn.execute("SELECT * FROM robots").fetchall()
        for r in rows:
            if r["status"] == "Manutenção":
                speed = 0
                battery = max(0, r["battery"] - random.uniform(0, .03))
                temp = max(25, r["temperature"] + random.uniform(-.25, .4))
                x, y = r["position_x"], r["position_y"]
                event, msg = "MANUTENÇÃO", "Monitoramento do equipamento."
            else:
                speed = min(2.0, max(0, r["speed"] + random.uniform(-.18, .18)))
                battery = max(0, r["battery"] - random.uniform(.01, .06))
                temp = min(80, max(25, r["temperature"] + random.uniform(-.7, .7)))
                x = min(9.5, max(.5, r["position_x"] + random.uniform(-.35, .35)))
                y = min(9.5, max(.5, r["position_y"] + random.uniform(-.35, .35)))
                event, msg = "TELEMETRIA", "Leitura operacional recebida."
                if battery < 15:
                    battery = 100; event, msg = "RECARGA", "Ciclo de recarga concluído."
            conn.execute(
                "UPDATE robots SET battery=?,temperature=?,speed=?,position_x=?,position_y=?,updated_at=? WHERE name=?",
                (battery, temp, speed, x, y, now, r["name"]),
            )
            conn.execute(
                """INSERT INTO telemetry
                (robot_name,battery,temperature,speed,position_x,position_y,status,event_type,message,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (r["name"], battery, temp, speed, x, y, r["status"], event, msg, now),
            )
        conn.execute("UPDATE system_state SET value=? WHERE key='last_tick'", (str(now_epoch),))
        conn.commit(); return True
    except sqlite3.OperationalError:
        conn.rollback(); return False
    finally:
        conn.close()


def send_command(robot: str, command: str, parameter: float | None = None) -> str:
    conn = db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        r = conn.execute("SELECT * FROM robots WHERE name=?", (robot,)).fetchone()
        if not r:
            result = "Robô não encontrado."
        elif r["status"] == "Manutenção" and command != "Diagnóstico":
            result = "Comando bloqueado: equipamento em manutenção."
        else:
            result = "Comando executado."
            if command == "Mover":
                conn.execute("UPDATE robots SET speed=? WHERE name=?", (max(0, min(2, parameter or 0)), robot))
            elif command == "Parar":
                conn.execute("UPDATE robots SET speed=0 WHERE name=?", (robot,))
            elif command == "Calibrar":
                conn.execute("UPDATE robots SET position_x=5,position_y=5,temperature=40 WHERE name=?", (robot,))
            elif command == "Recarregar":
                conn.execute("UPDATE robots SET battery=100 WHERE name=?", (robot,))
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO commands(robot_name,command,parameter,result,created_at) VALUES(?,?,?,?,?)",
            (robot, command, parameter, result, now),
        )
        conn.execute(
            """INSERT INTO telemetry
            (robot_name,battery,temperature,speed,position_x,position_y,status,event_type,message,created_at)
            SELECT name,battery,temperature,speed,position_x,position_y,status,'COMANDO',?,? FROM robots WHERE name=?""",
            (f"{command}: {result}", now, robot),
        )
        conn.commit(); return result
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def robots_df() -> pd.DataFrame:
    return query_df(
        """SELECT name AS Robô,status AS Status,ROUND(battery,1) AS Bateria,
        ROUND(temperature,1) AS Temperatura,ROUND(speed,2) AS Velocidade,
        ROUND(position_x,2) AS X,ROUND(position_y,2) AS Y,updated_at AS Atualizado
        FROM robots ORDER BY name"""
    )


def latest_event() -> pd.DataFrame:
    return query_df(
        """SELECT robot_name AS Robô, command AS Comando, result AS Resultado, created_at AS DataHora
        FROM commands ORDER BY id DESC LIMIT 1"""
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="title">{title}</div><div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_row(items: list[tuple[str, str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value, note) in zip(cols, items):
        with col:
            st.markdown(
                f'<div class="kpi"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
                unsafe_allow_html=True,
            )


def live_status() -> None:
    df = robots_df()
    active = int((df["Status"] == "Ativo").sum())
    maintenance = int((df["Status"] == "Manutenção").sum())
    commands = int(query_df("SELECT COUNT(*) AS n FROM commands").iloc[0]["n"])
    st.markdown(
        f'<div class="factory-top"><div class="brand">MUNDO SENAI <span>• Fábrica Inteligente</span></div>'
        f'<div class="clock">{active} em operação &nbsp;•&nbsp; {maintenance} em manutenção &nbsp;•&nbsp; {commands} comandos</div></div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every="2s")
def refresh_state() -> None:
    tick_telemetry()
    live_status()


@st.fragment(run_every="2s")
def station_production() -> None:
    df = robots_df()
    maint = query_df(
        """SELECT robot_name AS Robô,priority AS Prioridade,title AS Tarefa,status AS Status,assignee AS Responsável
        FROM maintenance ORDER BY CASE priority WHEN 'Alta' THEN 1 WHEN 'Média' THEN 2 ELSE 3 END, id DESC"""
    )
    active = int((df["Status"] == "Ativo").sum())
    open_tasks = int(maint["Status"].isin(["Aberto", "Em andamento"]).sum())
    low_battery = int((df["Bateria"] < 25).sum())
    kpi_row([
        ("Produção", "Operação", f"{active} robôs ativos"),
        ("Tarefas abertas", str(open_tasks), "manutenção e melhoria"),
        ("Alertas", str(low_battery), "bateria abaixo de 25%"),
        ("Frota", str(len(df)), "equipamentos monitorados"),
    ])
    st.write("")
    a, b = st.columns([1.3, .9])
    with a:
        st.markdown('<div class="panel"><h3>Ordens de trabalho</h3>', unsafe_allow_html=True)
        st.dataframe(maint, width="stretch", hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel"><h3>Status da frota</h3>', unsafe_allow_html=True)
        for _, r in df.iterrows():
            dot = "dot-ok" if r["Status"] == "Ativo" else "dot-warn"
            st.markdown(
                f'<div class="robot-card" style="margin:.45rem 0"><div class="robot-name">'
                f'<span class="dot {dot}"></span>{r["Robô"]}</div>'
                f'<div class="robot-meta">{r["Status"]} &nbsp;•&nbsp; {r["Bateria"]}% bateria &nbsp;•&nbsp; {r["Temperatura"]} °C</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


@st.fragment(run_every="2s")
def station_robots() -> None:
    df = robots_df()
    page_header("Controle dos Robôs", "Operação da célula robótica")
    left, right = st.columns([.82, 1.18])
    with left:
        st.markdown('<div class="panel"><h3>Comando</h3><p>Escolha o equipamento e execute uma operação.</p>', unsafe_allow_html=True)
        robot = st.selectbox("Robô", ROBOTS, key="robot_select")
        command = st.radio("Operação", ["Mover", "Parar", "Calibrar", "Recarregar", "Diagnóstico"], horizontal=True, key="command_select")
        parameter = None
        if command == "Mover":
            parameter = st.slider("Velocidade", 0.0, 2.0, .8, .1, key="speed_select")
        if st.button("EXECUTAR OPERAÇÃO", type="primary", width="stretch"):
            result = send_command(robot, command, parameter)
            if result == "Comando executado.":
                st.success(result)
            else:
                st.warning(result)
        selected = df[df["Robô"] == robot]
        if not selected.empty:
            r = selected.iloc[0]
            st.markdown('<h3 style="margin-top:1rem">Estado atual</h3>', unsafe_allow_html=True)
            x, y, z = st.columns(3)
            x.metric("Bateria", f"{r['Bateria']}%")
            y.metric("Temperatura", f"{r['Temperatura']} °C")
            z.metric("Velocidade", f"{r['Velocidade']} m/s")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><h3>Último comando</h3>', unsafe_allow_html=True)
        ev = latest_event()
        if ev.empty:
            st.info("Nenhuma operação registrada ainda.")
        else:
            r = ev.iloc[0]
            st.markdown(
                f'<div class="event"><div class="event-label">Execução registrada</div>'
                f'<div class="event-main">{r["Robô"]} → {r["Comando"]}</div>'
                f'<div class="event-sub">{r["Resultado"]} • {r["DataHora"]}</div></div>',
                unsafe_allow_html=True,
            )
        with st.expander("Ver lógica utilizada"):
            param_text = f"parametro = {parameter:.1f}" if parameter is not None else "parametro = None"
            st.code(
                f'robo = "{robot}"\ncomando = "{command}"\n{param_text}\n\n'
                'if robo.status == "Manutenção" and comando != "Diagnóstico":\n'
                '    return "BLOQUEADO"\n\n'
                'if comando == "Mover":\n'
                '    robo.velocidade = parametro\n'
                'elif comando == "Parar":\n'
                '    robo.velocidade = 0\n'
                'elif comando == "Calibrar":\n'
                '    robo.posicao = (5, 5)\n'
                'elif comando == "Recarregar":\n'
                '    robo.bateria = 100\n\n'
                'registrar_evento(robo, comando)', language="python"
            )
        st.markdown('<div class="helper">As operações são simuladas e registradas no SQLite.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="panel"><h3>Histórico recente</h3>', unsafe_allow_html=True)
    cmds = query_df(
        """SELECT robot_name AS Robô,command AS Operação,parameter AS Parâmetro,result AS Resultado,created_at AS DataHora
        FROM commands ORDER BY id DESC LIMIT 8"""
    )
    st.dataframe(cmds, width="stretch", hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


@st.fragment(run_every="2s")
def station_data() -> None:
    page_header("Central de Dados", "Telemetria, eventos e histórico operacional")
    telem = query_df(
        """SELECT id AS ID,robot_name AS Robô,ROUND(battery,1) AS Bateria,
        ROUND(temperature,1) AS Temperatura,ROUND(speed,2) AS Velocidade,
        event_type AS Evento,message AS EventoDetalhe,created_at AS DataHora
        FROM telemetry ORDER BY id DESC LIMIT 250"""
    )
    avg_bat = telem["Bateria"].mean() if not telem.empty else 0
    avg_temp = telem["Temperatura"].mean() if not telem.empty else 0
    commands = int(query_df("SELECT COUNT(*) AS n FROM commands").iloc[0]["n"])
    kpi_row([
        ("Registros", f"{len(telem)}", "telemetria disponível"),
        ("Bateria média", f"{avg_bat:.1f}%", "últimas leituras"),
        ("Temperatura média", f"{avg_temp:.1f} °C", "últimas leituras"),
        ("Comandos", str(commands), "operações registradas"),
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="panel"><h3>Temperatura</h3>', unsafe_allow_html=True)
        if not telem.empty:
            fig = px.line(telem.sort_values("DataHora"), x="DataHora", y="Temperatura", color="Robô")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10), legend_title_text="")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="panel"><h3>Bateria</h3>', unsafe_allow_html=True)
        if not telem.empty:
            fig = px.line(telem.sort_values("DataHora"), x="DataHora", y="Bateria", color="Robô")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=20,b=10), legend_title_text="")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="panel"><h3>Eventos recentes</h3>', unsafe_allow_html=True)
    st.dataframe(telem.head(35), width="stretch", hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    with st.expander("Detalhes técnicos"):
        st.code("SELECT robot_name, battery, temperature, speed, status, created_at\nFROM telemetry\nORDER BY created_at DESC\nLIMIT 100;", language="sql")


@st.fragment(run_every="2s")
def station_dashboard() -> None:
    page_header("Fábrica — Visão Geral", "Estado atual da operação")
    df = robots_df()
    total = len(df)
    active = int((df["Status"] == "Ativo").sum())
    availability = active / total * 100 if total else 0
    avg_bat = df["Bateria"].mean() if not df.empty else 0
    avg_temp = df["Temperatura"].mean() if not df.empty else 0
    kpi_row([
        ("Disponibilidade", f"{availability:.0f}%", "estado atual da frota"),
        ("Bateria média", f"{avg_bat:.1f}%", "frota monitorada"),
        ("Temperatura média", f"{avg_temp:.1f} °C", "frota monitorada"),
        ("Equipamentos", str(total), "na célula"),
    ])
    st.write("")
    left, right = st.columns([1.15, .85])
    with left:
        st.markdown('<div class="panel"><h3>Mapa operacional</h3>', unsafe_allow_html=True)
        m = df.rename(columns={"X":"x", "Y":"y", "Robô":"robot"})
        fig = px.scatter(m, x="x", y="y", color="Status", text="robot", size="Bateria", range_x=[0,10], range_y=[0,10])
        fig.update_traces(textposition="top center")
        fig.update_xaxes(title="Célula X", showgrid=True, dtick=1)
        fig.update_yaxes(title="Célula Y", showgrid=True, dtick=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(7,17,31,1)", margin=dict(l=10,r=10,t=10,b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><h3>Frota</h3>', unsafe_allow_html=True)
        for _, r in df.iterrows():
            dot = "dot-ok" if r["Status"] == "Ativo" else "dot-warn"
            st.markdown(
                f'<div class="robot-card" style="margin:.5rem 0"><div class="robot-name">'
                f'<span class="dot {dot}"></span>{r["Robô"]}</div>'
                f'<div class="robot-meta">{r["Status"]} • {r["Bateria"]}% • {r["Temperatura"]} °C • {r["Velocidade"]} m/s</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    ev = latest_event()
    if not ev.empty:
        r = ev.iloc[0]
        st.write("")
        st.markdown(
            f'<div class="event"><div class="event-label">Última operação</div>'
            f'<div class="event-main">{r["Robô"]} → {r["Comando"]}</div>'
            f'<div class="event-sub">{r["Resultado"]} • {r["DataHora"]}</div></div>',
            unsafe_allow_html=True,
        )
    st.write("")
    st.caption("Demonstração educacional: dados simulados, sem conexão com equipamentos industriais reais.")


init_database()

params = st.query_params
station = str(params.get("station", "4"))
if station not in STATIONS:
    station = "4"

# A barra superior é propositalmente discreta: não explica a arquitetura ao visitante.
refresh_state()

if station == "1":
    page_header("Controle da Produção", "Operação da linha • tarefas • manutenção")
    station_production()
elif station == "2":
    station_robots()
elif station == "3":
    station_data()
else:
    station_dashboard()
