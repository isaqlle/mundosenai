# 🤖 Sistema de Gestão e Telemetria de Robôs Industriais — Mundo SENAI

Projeto demonstrativo para o estande **Fábrica de Software & Robótica** do Mundo SENAI.

A aplicação simula uma plataforma de gestão de robôs industriais com quatro perspectivas:

1. **Gestão e Requisitos** — Product Owner / Analista;
2. **Código e Controle Operacional** — Desenvolvedor / Programador;
3. **Banco de Dados e Logs** — Backend / DBA;
4. **Dashboard Executivo e Cliente** — Cliente / Deploy.

O projeto foi pensado para funcionar no **GitHub Codespaces**, diretamente pelo navegador, sem necessidade de robôs físicos.

## 1. Tecnologias

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- SQLite3
- qrcode
- GitHub Codespaces

O SQLite é criado automaticamente; não é necessário instalar um servidor de banco.

## 2. Estrutura

```text
mundo_senai_robotica/
├── app.py
├── requirements.txt
├── README.md
└── robotica_senai.db   # criado automaticamente na primeira execução
```

## 3. Colocar no GitHub

Crie um repositório, por exemplo `mundo-senai-robotica`, e envie os três arquivos (`app.py`, `requirements.txt`, `README.md`).

Via Git:

```bash
git init
git add .
git commit -m "Sistema Mundo SENAI - Robótica"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/mundo-senai-robotica.git
git push -u origin main
```

## 4. Abrir no GitHub Codespaces

1. Abra o repositório no GitHub.
2. Clique em **Code**.
3. Entre em **Codespaces**.
4. Clique em **Create codespace on main**.
5. Aguarde o VS Code abrir no navegador.

## 5. Instalar dependências

No terminal do Codespaces:

```bash
pip install -r requirements.txt
```

## 6. Executar

```bash
streamlit run app.py
```

O Streamlit normalmente usa a porta `8501`. No Codespaces, abra a notificação da porta ou a aba **PORTS** e escolha **Open in Browser**.

Se a porta não aparecer:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

## 7. As quatro estações

### Estação 1 — Gestão e Requisitos

Apresenta chamados de manutenção, requisitos, responsáveis, status dos robôs e integração. É a visão do **PO/Analista**.

### Estação 2 — Código e Controle

Permite selecionar um robô e simular comandos de **Mover, Parar, Calibrar, Recarregar e Diagnóstico**. O aluno pode mostrar o snippet Python e o registro dos comandos. É a visão do **Dev/Programador**.

### Estação 3 — Banco de Dados e Logs

Mostra o histórico de telemetria persistido no SQLite e gráficos de temperatura e bateria. É a visão do **Backend/DBA**.

### Estação 4 — Dashboard Executivo

Exibe disponibilidade, bateria, temperatura, mapa operacional simulado e geração de QR Code. É a visão do **Cliente/Deploy**.

## 8. Como funciona a telemetria

A função `generate_telemetry()` cria pequenas variações de bateria, temperatura, velocidade e posição X/Y. Cada leitura é persistida no SQLite.

O sistema pode, portanto, ser demonstrado sem qualquer robô físico.

## 9. Roteiro para quatro monitores

- **Monitor 1:** Gestão e Requisitos — aluno PO/Analista.
- **Monitor 2:** Código e Controle — aluno Dev/Programador.
- **Monitor 3:** Banco de Dados e Logs — aluno Backend/DBA.
- **Monitor 4:** Dashboard Executivo — aluno Cliente/Deploy.

### Roteiro rápido

1. Explique o problema: monitorar uma frota e transformar dados em informação.
2. Mostre os requisitos e chamados.
3. Envie um comando para um robô.
4. Mostre o comando registrado no banco.
5. Mostre os indicadores executivos.
6. Peça ao visitante para escanear o QR Code.

## 10. Publicar para acesso público

Para uma URL pública permanente, uma opção é usar o **Streamlit Community Cloud**:

1. Publique o projeto no GitHub.
2. Acesse o Streamlit Community Cloud.
3. Conecte o GitHub.
4. Escolha o repositório.
5. Selecione `app.py` como arquivo principal.
6. Faça o deploy.
7. Copie a URL pública.
8. Na Estação 4, substitua `https://seu-projeto.streamlit.app` pela URL real.
9. O QR Code passará a apontar para o sistema publicado.

## 11. Executar localmente

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 12. Limpar a demonstração

Pare o Streamlit e apague `robotica_senai.db`. Na próxima execução o banco será recriado com dados iniciais.

## 13. Arquitetura para uma futura versão industrial

Hoje os comandos são simulados. Em uma versão real, `send_command()` poderia ser substituída por uma camada de integração com **MQTT, REST API, OPC-UA, ROS/ROS 2, PLC ou controlador do fabricante**.

Uma arquitetura possível:

```text
Streamlit / Dashboard
        ↓
API / Serviço de Controle
        ↓
Broker ou Gateway Industrial
        ↓
PLC / Controlador
        ↓
Robô Industrial
```

Para produção, também devem ser considerados autenticação, autorização, auditoria, HTTPS/TLS, validação dos comandos, limites operacionais, parada de emergência independente do software, segregação de redes e backups.

## 14. Próximas evoluções

- Login e perfis de usuário;
- CRUD de chamados;
- API FastAPI;
- MQTT;
- PostgreSQL;
- autenticação e auditoria;
- integração com PLC;
- sensores reais;
- Docker e CI/CD;
- histórico por períodos;
- alarmes e notificações;
- manutenção preditiva com Machine Learning.

> **Importante:** este projeto é uma demonstração educacional. Os dados e comandos dos robôs são simulados e não representam equipamentos industriais reais.
