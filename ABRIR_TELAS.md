# Configuração das quatro TVs

## 1. No computador central

Abra o Codespace, instale as dependências e execute:

```bash
python -m streamlit run app.py
```

A aplicação usa o SQLite dentro do mesmo Codespace. As quatro TVs devem acessar **o mesmo endereço encaminhado da porta 8501**.

## 2. Porta 8501

No painel **PORTS** do Codespace, localize a porta 8501 e deixe a visibilidade adequada para os computadores das TVs. Se o acesso for feito fora da sessão autenticada, use uma porta pública; se todos os computadores estiverem autenticados e a configuração permitir, a porta privada pode ser usada.

## 3. Copie o endereço

Copie somente o endereço base da porta 8501 e cole no `BASE_URL` dos quatro arquivos `.bat`:

- `abrir_tv1.bat` → `?station=1`
- `abrir_tv2.bat` → `?station=2`
- `abrir_tv3.bat` → `?station=3`
- `abrir_tv4.bat` → `?station=4`

Exemplo:

```text
https://SEU-ENDERECO:8501/?station=2
```

O navegador já abre a tela correta. Ninguém precisa digitar o endereço durante a apresentação.

## 4. GitHub nos quatro computadores

Se a porta do Codespace exigir autenticação, entre com sua conta GitHub nos computadores antes da apresentação. Depois, os atalhos `.bat` abrem diretamente a tela correspondente.

## 5. Por que não usar localhost nas quatro TVs?

`localhost` aponta para o próprio computador. Se cada TV tiver um computador diferente, cada uma poderia acabar executando uma aplicação e um banco diferentes.

Aqui, o desenho correto é:

```text
                 CODESPACE
        Streamlit + SQLite central
                    │
          ──────────┼──────────
          │         │         │
        TV 1      TV 2      TV 3      TV 4
       station=1 station=2 station=3 station=4
```

Assim, uma ação feita na tela de Controle dos Robôs pode aparecer na Central de Dados e na Visão Geral da Fábrica.
