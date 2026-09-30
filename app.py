"""Sistema de Gestão e Telemetria de Robôs Industriais - Mundo SENAI."""
from __future__ import annotations

import io
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import qrcode
import streamlit as st

st.set_page_config(page_title="Mundo SENAI | Gestão de Robôs", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "robotica_senai.db"
ROBOTS = ["ROBÔ-01", "ROBÔ-02", "ROBÔ-03", "ROBÔ-04", "ROBÔ-05", "ROBÔ-06"]

st.markdown("""
<style>
.main { background:#f6f8fb; }
.block-container { max-width:1500px; padding-top:1.2rem; padding-bottom:2rem; }
.hero { padding:1.2rem 1.4rem; border-radius:18px; background:linear-gradient(135deg,#111827,#1f2937); color:white; margin-bottom:1rem; }
.hero h1 { margin-bottom:.2rem; }
.hero p { color:#d1d5db; margin-bottom:0; }
.station { border-left:5px solid #2563eb; padding:.8rem 1rem; background:white; border-radius:10px; margin-bottom:1rem; }
div[data-testid="stMetric"] { background:white; padding:.8rem; border-radius:12px; border:1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Cria as tabelas e os dados iniciais da demonstração."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS robots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL, status TEXT NOT NULL,
            battery REAL NOT NULL, temperature REAL NOT NULL, speed REAL NOT NULL,
            position_x REAL NOT NULL, position_y REAL NOT NULL, updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            robot_name TEXT NOT NULL, battery REAL NOT NULL, temperature REAL NOT NULL,
            speed REAL NOT NULL, position_x REAL NOT NULL, position_y REAL NOT NULL,
            status TEXT NOT NULL, event_type TEXT NOT NULL, message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            robot_name TEXT NOT NULL, command TEXT NOT NULL, parameter REAL,
            result TEXT NOT NULL, created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            robot_name TEXT NOT NULL, priority TEXT NOT NULL, title TEXT NOT NULL,
            status TEXT NOT NULL, assignee TEXT NOT NULL, created_at TEXT NOT NULL
        )
    """)
    if cur.execute("SELECT COUNT(*) FROM robots").fetchone()[0] == 0:
        now = datetime.now().isoformat(timespec="seconds")
        for i, robot in enumerate(ROBOTS):
            cur.execute("""
                INSERT INTO robots(name,status,battery,temperature,speed,position_x,position_y,updated_at)
                VALUES(?,?,?,?,?,?,?,?)
            """, (robot, "Ativo" if i < 5 else "Manutenção", random.uniform(55,100),
                   random.uniform(35,55), random.uniform(0,1.5), random.uniform(0,10),
                   random.uniform(0,10), now))
    if cur.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0] == 0:
        tasks = [
            ("ROBÔ-02","Alta","Calibrar sensor de posição","Em andamento","Ana"),
            ("ROBÔ-05","Média","Inspeção preventiva","Aberto","Carlos"),
            ("ROBÔ-01","Baixa","Atualizar rotina de movimentação","Concluído","João"),
            ("ROBÔ-04","Alta","Verificar temperatura do motor","Aberto","Marina"),
        ]
        for robot, priority, title, status, assignee in tasks:
            cur.execute("""
                INSERT INTO maintenance(robot_name,priority,title,status,assignee,created_at)
                VALUES(?,?,?,?,?,?)
            """, (robot, priority, title, status, assignee, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


def read_dataframe(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def generate_telemetry() -> None:
    """Gera uma nova leitura simulada para cada robô e persiste no SQLite."""
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    rows = cur.execute("SELECT name,status,battery,temperature,speed,position_x,position_y FROM robots").fetchall()
    for row in rows:
        if row["status"] == "Manutenção":
            speed = 0.0
            battery = max(0, row["battery"] - random.uniform(0.00,0.08))
            temperature = max(25, row["temperature"] + random.uniform(-0.4,0.8))
            x, y = row["position_x"], row["position_y"]
            event_type, message = "MANUTENÇÃO", "Robô em manutenção preventiva."
        else:
            speed = min(2.0, max(0, row["speed"] + random.uniform(-0.25,0.25)))
            battery = max(0, row["battery"] - random.uniform(0.02,0.15))
            temperature = min(85, max(25, row["temperature"] + random.uniform(-1.5,1.5)))
            x = min(10, max(0, row["position_x"] + random.uniform(-0.6,0.6)))
            y = min(10, max(0, row["position_y"] + random.uniform(-0.6,0.6)))
            event_type, message = "TELEMETRIA", "Leitura periódica recebida."
            if battery < 15:
                battery = random.uniform(70,100)
                event_type, message = "RECARGA", "Ciclo de recarga simulado concluído."
        cur.execute("""
            UPDATE robots SET battery=?,temperature=?,speed=?,position_x=?,position_y=?,updated_at=? WHERE name=?
        """, (battery,temperature,speed,x,y,now,row["name"]))
        cur.execute("""
            INSERT INTO telemetry(robot_name,battery,temperature,speed,position_x,position_y,status,event_type,message,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (row["name"],battery,temperature,speed,x,y,row["status"],event_type,message,now))
    conn.commit()
    conn.close()


def send_command(robot: str, command: str, parameter: float | None = None) -> str:
    """Simula um comando e grava sua auditoria no banco."""
    conn = get_connection()
    cur = conn.cursor()
    robot_row = cur.execute("SELECT status FROM robots WHERE name=?", (robot,)).fetchone()
    if not robot_row:
        result = "ERRO: robô não encontrado."
    elif robot_row["status"] == "Manutenção" and command != "Diagnóstico":
        result = "BLOQUEADO: robô está em manutenção."
    else:
        result = "OK: comando processado pelo simulador."
        if command == "Parar":
            cur.execute("UPDATE robots SET speed=0 WHERE name=?", (robot,))
        elif command == "Mover":
            cur.execute("UPDATE robots SET speed=? WHERE name=?", (max(0,min(2,parameter or 0)),robot))
        elif command == "Calibrar":
            cur.execute("UPDATE robots SET position_x=5,position_y=5,temperature=40 WHERE name=?", (robot,))
        elif command == "Recarregar":
            cur.execute("UPDATE robots SET battery=100 WHERE name=?", (robot,))
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("INSERT INTO commands(robot_name,command,parameter,result,created_at) VALUES(?,?,?,?,?)",
                (robot,command,parameter,result,now))
    cur.execute("""
        INSERT INTO telemetry(robot_name,battery,temperature,speed,position_x,position_y,status,event_type,message,created_at)
        SELECT name,battery,temperature,speed,position_x,position_y,status,'COMANDO',?,? FROM robots WHERE name=?
    """, (f"{command} executado: {result}",now,robot))
    conn.commit()
    conn.close()
    return result


def create_qr_code(url: str) -> bytes:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def get_robot_status() -> pd.DataFrame:
    return read_dataframe("""
        SELECT name AS Robô,status AS Status,ROUND(battery,1) AS Bateria,
               ROUND(temperature,1) AS Temperatura,ROUND(speed,2) AS Velocidade,
               ROUND(position_x,2) AS X,ROUND(position_y,2) AS Y,updated_at AS Atualizado
        FROM robots ORDER BY name
    """)


def get_telemetry(limit: int = 200) -> pd.DataFrame:
    return read_dataframe("""
        SELECT id AS ID,robot_name AS Robô,ROUND(battery,1) AS Bateria,
               ROUND(temperature,1) AS Temperatura,ROUND(speed,2) AS Velocidade,
               ROUND(position_x,2) AS X,ROUND(position_y,2) AS Y,status AS Status,
               event_type AS Evento,message AS Mensagem,created_at AS DataHora
        FROM telemetry ORDER BY id DESC LIMIT ?
    """, (limit,))


init_database()
if "last_update" not in st.session_state:
    st.session_state.last_update = 0.0
if time.time() - st.session_state.last_update >= 2:
    generate_telemetry()
    st.session_state.last_update = time.time()

st.markdown("""
<div class="hero">
<h1>🤖 Sistema de Gestão e Telemetria de Robôs Industriais</h1>
<p>Mundo SENAI • Fábrica de Software & Robótica • Demonstração educacional</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🏭 Estações da Fábrica")
    station = st.radio("Selecione a estação", [
        "1 — Gestão e Requisitos", "2 — Código e Controle",
        "3 — Banco de Dados e Logs", "4 — Dashboard Executivo",
    ])
    st.divider()
    st.caption("Simulação local")
    st.caption(f"Banco: `{DB_PATH.name}`")
    if st.button("🔄 Atualizar telemetria", use_container_width=True):
        generate_telemetry()
        st.rerun()

if station.startswith("1"):
    st.markdown('<div class="station"><h2>📋 Estação 1 — Gestão e Requisitos</h2><p>Visão do Product Owner / Analista de Sistemas.</p></div>', unsafe_allow_html=True)
    robots_df = get_robot_status()
    maintenance_df = read_dataframe("""
        SELECT robot_name AS Robô,priority AS Prioridade,title AS Tarefa,status AS Status,
               assignee AS Responsável,created_at AS CriadoEm FROM maintenance
        ORDER BY CASE priority WHEN 'Alta' THEN 1 WHEN 'Média' THEN 2 ELSE 3 END,id DESC
    """)
    active = int((robots_df["Status"] == "Ativo").sum())
    maintenance = int((robots_df["Status"] == "Manutenção").sum())
    open_tasks = int(maintenance_df["Status"].isin(["Aberto","Em andamento"]).sum())
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Robôs ativos",active); c2.metric("Em manutenção",maintenance); c3.metric("Tarefas abertas",open_tasks); c4.metric("Integração","ONLINE")
    st.subheader("Quadro de trabalho")
    col1,col2 = st.columns([1.3,1])
    with col1: st.dataframe(maintenance_df,use_container_width=True,hide_index=True)
    with col2:
        st.markdown("### Status da integração")
        st.success("🟢 API de telemetria — conectada (simulada)")
        st.success("🟢 SQLite — conectado")
        st.success("🟢 Painel Streamlit — operacional")
        st.info("🔵 Robôs físicos — não necessários para a demonstração")
    st.subheader("Requisitos demonstrados")
    req = pd.DataFrame([
        ["REQ-001","Visualizar status da frota","Concluído"], ["REQ-002","Receber telemetria","Concluído"],
        ["REQ-003","Enviar comando ao robô","Concluído"], ["REQ-004","Registrar logs no banco","Concluído"],
        ["REQ-005","Exibir indicadores executivos","Concluído"], ["REQ-006","Gerar QR Code do sistema","Concluído"]],
        columns=["ID","Requisito","Situação"])
    st.dataframe(req,use_container_width=True,hide_index=True)
    st.subheader("Frota atual")
    st.dataframe(robots_df,use_container_width=True,hide_index=True)

elif station.startswith("2"):
    st.markdown('<div class="station"><h2>💻 Estação 2 — Código e Controle Operacional</h2><p>Visão do desenvolvedor/programador.</p></div>', unsafe_allow_html=True)
    robots_df = get_robot_status()
    left,right = st.columns([1,1.3])
    with left:
        st.subheader("Painel de comando")
        selected_robot = st.selectbox("Robô",ROBOTS)
        command = st.selectbox("Comando",["Mover","Parar","Calibrar","Recarregar","Diagnóstico"])
        parameter = None
        if command == "Mover":
            parameter = st.slider("Velocidade (m/s)",0.0,2.0,0.8,0.1)
        if st.button("🚀 Enviar comando",type="primary",use_container_width=True):
            result = send_command(selected_robot,command,parameter)
            if result.startswith("OK"): st.success(result)
            elif result.startswith("BLOQUEADO"): st.warning(result)
            else: st.error(result)
        robot_row = robots_df[robots_df["Robô"] == selected_robot]
        if not robot_row.empty:
            row = robot_row.iloc[0]
            a,b,c = st.columns(3)
            a.metric("Bateria",f"{row['Bateria']}%"); b.metric("Temperatura",f"{row['Temperatura']} °C"); c.metric("Velocidade",f"{row['Velocidade']} m/s")
    with right:
        st.subheader("Snippet da lógica Python")
        st.code('''def processar_comando(robo, comando, parametro=None):\n    if robo.status == "Manutenção":\n        return "BLOQUEADO"\n\n    if comando == "Mover":\n        robo.velocidade = parametro\n    elif comando == "Parar":\n        robo.velocidade = 0\n    elif comando == "Calibrar":\n        robo.posicao = (5, 5)\n    elif comando == "Recarregar":\n        robo.bateria = 100\n\n    salvar_log(robo, comando)\n    return "OK"''',language="python")
        st.info("Em uma aplicação industrial real, esta camada poderia conversar com MQTT, REST, OPC-UA, ROS ou outro protocolo.")
    st.subheader("Últimos comandos")
    commands_df = read_dataframe("SELECT id AS ID,robot_name AS Robô,command AS Comando,parameter AS Parâmetro,result AS Resultado,created_at AS DataHora FROM commands ORDER BY id DESC LIMIT 15")
    st.dataframe(commands_df,use_container_width=True,hide_index=True)

elif station.startswith("3"):
    st.markdown('<div class="station"><h2>🗄️ Estação 3 — Banco de Dados e Logs</h2><p>Visão de Backend / DBA: dados persistidos em SQLite.</p></div>', unsafe_allow_html=True)
    telemetry_df = get_telemetry(300)
    c1,c2,c3 = st.columns(3)
    c1.metric("Logs carregados",len(telemetry_df)); c2.metric("Temperatura média",f"{telemetry_df['Temperatura'].mean():.1f} °C" if not telemetry_df.empty else "0 °C"); c3.metric("Bateria média",f"{telemetry_df['Bateria'].mean():.1f}%" if not telemetry_df.empty else "0%")
    st.subheader("Histórico de eventos")
    limit = st.slider("Quantidade de registros",20,300,100,20)
    telemetry_df = get_telemetry(limit)
    st.dataframe(telemetry_df,use_container_width=True,hide_index=True)
    chart_col1,chart_col2 = st.columns(2)
    with chart_col1:
        if not telemetry_df.empty:
            fig = px.line(telemetry_df.sort_values("DataHora"),x="DataHora",y="Temperatura",color="Robô",title="Temperatura ao longo do tempo")
            st.plotly_chart(fig,use_container_width=True)
    with chart_col2:
        if not telemetry_df.empty:
            fig = px.line(telemetry_df.sort_values("DataHora"),x="DataHora",y="Bateria",color="Robô",title="Bateria ao longo do tempo")
            st.plotly_chart(fig,use_container_width=True)
    with st.expander("🔎 SQL utilizado na demonstração"):
        st.code("""SELECT robot_name, battery, temperature, speed, status, created_at\nFROM telemetry\nORDER BY created_at DESC\nLIMIT 100;""",language="sql")

else:
    st.markdown('<div class="station"><h2>📊 Estação 4 — Dashboard Executivo e Cliente</h2><p>Visão do cliente, gestor e equipe de implantação.</p></div>', unsafe_allow_html=True)
    robots_df = get_robot_status()
    total = len(robots_df); active = int((robots_df["Status"] == "Ativo").sum()); availability = active / total * 100 if total else 0
    avg_battery = robots_df["Bateria"].mean(); avg_temp = robots_df["Temperatura"].mean()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Disponibilidade",f"{availability:.1f}%"); c2.metric("Bateria média",f"{avg_battery:.1f}%"); c3.metric("Temperatura média",f"{avg_temp:.1f} °C"); c4.metric("Robôs monitorados",total)
    col1,col2 = st.columns(2)
    with col1:
        fig = px.bar(robots_df,x="Robô",y="Bateria",color="Status",title="Bateria por robô",range_y=[0,100]); st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig = px.bar(robots_df,x="Robô",y="Temperatura",color="Status",title="Temperatura por robô"); st.plotly_chart(fig,use_container_width=True)
    st.subheader("Mapa operacional da fábrica")
    map_df = robots_df.rename(columns={"X":"x","Y":"y","Robô":"robot"})
    fig = px.scatter(map_df,x="x",y="y",color="Status",text="robot",size="Bateria",range_x=[0,10],range_y=[0,10],title="Posição simulada dos robôs")
    fig.update_traces(textposition="top center"); fig.update_xaxes(title="Eixo X — célula industrial"); fig.update_yaxes(title="Eixo Y — célula industrial")
    st.plotly_chart(fig,use_container_width=True)
    st.subheader("📱 QR Code para acesso ao sistema")
    qr_url = st.text_input("URL pública da aplicação",value="https://seu-projeto.streamlit.app",help="Depois do deploy, substitua pela URL real do sistema.")
    if qr_url:
        qr_bytes = create_qr_code(qr_url)
        qr_col1,qr_col2 = st.columns([1,2])
        with qr_col1:
            st.image(qr_bytes,caption="Aponte a câmera do celular")
            st.download_button("⬇️ Baixar QR Code",data=qr_bytes,file_name="qr_code_mundo_senai.png",mime="image/png")
        with qr_col2:
            st.markdown("### Experiência do visitante")
            st.markdown("1. O visitante escaneia o QR Code.\n2. Abre o sistema no celular.\n3. Visualiza a frota simulada.\n4. A equipe explica a arquitetura.\n5. O aluno demonstra a integração entre requisitos, código, banco e dashboard.")
    st.divider()
    st.caption("Demonstração educacional — os dados dos robôs são simulados e não representam equipamentos industriais reais.")
