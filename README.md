# Mundo SENAI — Fábrica Inteligente

Sistema educacional de demonstração de uma fábrica robotizada, desenvolvido em Python + Streamlit + SQLite.

## Apresentação com quatro computadores e quatro TVs

A aplicação foi preparada para funcionar com **um único Codespace como servidor da fábrica** e quatro computadores como telas de apresentação.

Cada computador abre a mesma aplicação, usando um parâmetro diferente na URL:

- `?station=1` — Controle da Produção
- `?station=2` — Controle dos Robôs
- `?station=3` — Central de Dados
- `?station=4` — Fábrica — Visão Geral

Isso mantém **um único SQLite e um único estado da fábrica**. Não execute uma cópia independente da aplicação em cada computador.

### Execução no Codespace

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Depois, use a porta encaminhada **8501** do Codespace. O endereço dessa porta é o endereço base que deve ser colocado nos quatro arquivos:

- `abrir_tv1.bat`
- `abrir_tv2.bat`
- `abrir_tv3.bat`
- `abrir_tv4.bat`

Cada arquivo abre automaticamente a página correspondente.

### Exemplo

Se o endereço encaminhado for:

```text
https://SEU-ENDERECO
```

as telas serão:

```text
https://SEU-ENDERECO/?station=1
https://SEU-ENDERECO/?station=2
https://jubilant-umbrella-g4qxw7rp99vcvj-8501.app.github.dev/?station=3
https://SEU-ENDERECO/?station=4
```

> O endereço real é fornecido pelo próprio Codespace; não coloque um endereço inventado no código.

## Organização da experiência

A interface foi pensada para parecer uma fábrica digital real, sem transformar a apresentação em um tutorial de arquitetura. O visitante vê controle, operação, dados e visão geral; a integração acontece por trás da interface.

## Tecnologias

- Python 3.10+
- Streamlit
- Pandas
- Plotly
- SQLite
- QRCode

## Observação

Os robôs são simulados. Nenhum equipamento industrial real é comandado pelo sistema.
