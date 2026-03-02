# 🏦 Sincronizador de Índices & API Guess

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-2019+-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Instalação Rápida](#-instalação-rápida)
- [Configuração](#-configuração)
- [Como Executar](#-como-executar)
- [Estrutura do Banco](#-estrutura-do-banco)
- [API Endpoints](#-api-endpoints)
- [Deployment (Agendador de Tarefas)](#-deployment-agendador-de-tarefas)
- [Troubleshooting](#-troubleshooting)
- [Contribuindo](#-contribuindo)

---

## 🎯 Sobre o Projeto

Sistema híbrido que centraliza dados econômicos (cotações de moedas e índices) para consumo interno na Guess Brasil.

**Arquitetura:**  
APIs Externas (AwesomeAPI/BCB) → Script Python (Sync Worker) → SQL Server (`HML_GUESS`) → API FastAPI (Gateway) → Sistemas Internos

**Componentes:**

1. **Sync Worker:** Coleta e persiste cotações no banco (INSERT/UPDATE inteligente)
2. **API Gateway:** Expõe os dados com cache (respostas < 50ms)

**Diferenciais:**
- ✅ Modo contingência (funciona mesmo com falha nas APIs externas)
- ✅ Cache em camadas (1h para cotações, 4h para dados diários, 24h para mensais)
- ✅ Documentação interativa automática (Swagger UI)

---

## 🚀 Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/Guess-Brasil/guess-api-indices.git
cd guess-api-indices

# Crie o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

**Pré-requisitos:**
- Python 3.12+
- ODBC Driver 17 for SQL Server ([Download](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server))
- Acesso ao SQL Server da rede corporativa

---

## ⚙️ Configuração

Crie o arquivo `.env` na raiz do projeto:

```ini
# ========================================
# BANCO DE DADOS
# ========================================
DRIVER={ODBC Driver 17 for SQL Server}
SERVER=SEU_SERVIDOR_SQL
DATABASE=NOME_DO_BANCO
DB_USERNAME=seu_usuario
DB_PASSWORD=sua_senha_segura

# ========================================
# API
# ========================================
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=False

# ========================================
# CACHE (segundos)
# ========================================
CACHE_TTL_QUOTES=3600      # 1 hora (cotações)
CACHE_TTL_DAILY=14400      # 4 horas (dados diários)
CACHE_TTL_MONTHLY=86400    # 24 horas (índices mensais)

# ========================================
# PROXY (Opcional - se necessário na rede Corp)
# ========================================
# HTTP_PROXY=http://proxy.empresa.com:8080
# HTTPS_PROXY=http://proxy.empresa.com:8080

# ========================================
# LOGGING
# ========================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 🔒 Segurança

⚠️ **CRÍTICO:** Adicione ao `.gitignore`:

```bash
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
echo "*.log" >> .gitignore
```

**Nunca commite credenciais ou IPs internos!**

---

## 💻 Como Executar

### 🔄 1. Sincronizador (Atualização do Banco)

Executa a coleta de dados e atualização do SQL Server:

```bash
python sync_indices_to_db.py
```

**Saída esperada:**
```
[2025-11-18 10:30:00] INFO - Iniciando sincronização...
[2025-11-18 10:30:02] INFO - Cotação US$ atualizada: R$ 6.1500
[2025-11-18 10:30:03] INFO - Sincronização concluída!
```

---

### 🚀 2. API (Servidor de Consulta)

```bash
# Desenvolvimento (com hot-reload)
uvicorn main:app --reload

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Acesse a documentação:**
- 📖 **Swagger UI:** http://localhost:8000/docs
- 📘 **ReDoc:** http://localhost:8000/redoc

---

## 📊 Estrutura do Banco

### Tabela: `dbo.MOEDAS_CONVERSAO`

```sql
CREATE TABLE dbo.MOEDAS_CONVERSAO (
    MOEDA VARCHAR(10) NOT NULL,
    DATA DATETIME NOT NULL,
    VALOR DECIMAL(18, 4) NOT NULL,
    Data_para_transferencia DATETIME DEFAULT GETDATE(),
    
    CONSTRAINT PK_MOEDAS_CONVERSAO PRIMARY KEY (MOEDA, DATA),
    CONSTRAINT CK_MOEDA_VALIDA CHECK (MOEDA IN ('US$', 'EUR', 'BRL'))
);

-- Índice para performance em consultas por data
CREATE INDEX IX_MOEDAS_DATA ON dbo.MOEDAS_CONVERSAO(DATA DESC, MOEDA);
```

#### Colunas

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `MOEDA` | varchar(10) | Código da moeda (ex: `US$`, `EUR`) |
| `DATA` | datetime | Data de referência da cotação |
| `VALOR` | decimal(18,4) | Valor da cotação |
| `Data_para_transferencia` | datetime | Timestamp da gravação |

---

## 🔌 API Endpoints

A API oferece as seguintes rotas principais:

### Cotações
- `GET /api/v1/cotacoes/{moeda}` - Cotação atual de uma moeda
- `GET /api/v1/cotacoes/historico/{moeda}` - Histórico de cotações

### Índices Econômicos
- `GET /api/v1/indices/{codigo}` - Valor de índices (`ipca_mensal`, `selic`, `cdi`, `pib`)

### Health Check
- `GET /health` - Status da API e suas dependências

**📖 Para detalhes completos, exemplos e schemas de resposta, acesse:**  
👉 **http://localhost:8000/docs** (documentação sempre atualizada)

---

## 🚀 Deployment (Agendador de Tarefas)

O Sync Worker roda automaticamente via **Windows Task Scheduler**.

### Configuração do Agendamento

1. Abra o **Agendador de Tarefas do Windows** (`taskschd.msc`)
2. Clique em **Criar Tarefa Básica**
3. Configure:

| Campo | Valor |
|-------|-------|
| **Nome** | `Sync Índices Guess` |
| **Descrição** | `Atualização automática de cotações e índices` |
| **Gatilho** | Diário - Repetir a cada 4 horas |
| **Ação** | Iniciar programa |
| **Programa/script** | `C:\caminho\para\venv\Scripts\python.exe` |
| **Adicionar argumentos** | `C:\caminho\para\sync_indices_to_db.py` |
| **Iniciar em** | `C:\caminho\para\guess-api-indices` |

4. Em **Condições**, desmarque:
   - ❌ "Iniciar a tarefa somente se o computador estiver conectado à energia CA"

5. Em **Configurações**, marque:
   - ✅ "Permitir que a tarefa seja executada sob demanda"
   - ✅ "Executar tarefa o mais rápido possível se um início agendado for perdido"

### Teste Manual

```bash
# Execute o script manualmente para validar
python sync_indices_to_db.py
```

### Logs

Os logs ficam armazenados em:
```
logs/app.log
```

---

## 🔧 Troubleshooting

### ❌ Erro: "ODBC Driver not found"

**Causa:** Driver SQL não instalado  
**Solução:**

```bash
# Verificar drivers instalados
odbcinst -q -d

# Windows: Instale o ODBC Driver 17
# https://go.microsoft.com/fwlink/?linkid=2223304
```

---

### ❌ Erro: "Login failed for user"

**Causa:** Credenciais incorretas ou usuário sem permissão  
**Solução:**

1. Confirme as credenciais no `.env`
2. Teste a conexão via SQL Server Management Studio (SSMS)
3. Verifique se o usuário tem permissões de `INSERT` e `UPDATE` na tabela `MOEDAS_CONVERSAO`

```sql
-- Conceder permissões (executar como DBA)
GRANT SELECT, INSERT, UPDATE ON dbo.MOEDAS_CONVERSAO TO [seu_usuario];
```

---

### ❌ Erro: "Connection timeout"

**Causa:** Firewall, rede ou SQL Server offline  
**Solução:**

```bash
# Teste conectividade TCP
telnet SEU_SERVIDOR_SQL 1433

# Se não conectar:
# 1. Verifique se SQL Server está rodando
# 2. Confirme regras de firewall
# 3. Valide se TCP/IP está habilitado no SQL Server Configuration Manager
```

---

### ❌ Erro: "SSL Certificate Verify Failed"

**Causa:** Certificados SSL inválidos na rede corporativa  
**Solução temporária (apenas desenvolvimento):**

```python
# No início do arquivo sync_indices_to_db.py
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

⚠️ **Não use em produção!** Solicite os certificados corretos ao time de infra.

---

### ❌ Erro: "API retorna 500 Internal Server Error"

**Causa:** Banco de dados fora do ar ou dados inconsistentes  
**Solução:**

1. Verifique o log da API:
```bash
tail -f logs/app.log
```

2. Teste o endpoint de health:
```bash
curl http://localhost:8000/health
```

3. Se o status do banco estiver "disconnected", verifique a conectividade

---

### ❌ Script não atualiza dados

**Causa:** Task Scheduler não está executando ou falha silenciosa  
**Solução:**

1. Abra o **Visualizador de Eventos** do Windows
2. Navegue até: `Logs do Windows > Aplicativo`
3. Procure por erros relacionados ao **Task Scheduler**
4. Execute manualmente para ver erros:
```bash
python sync_indices_to_db.py
```

---

## 🤝 Contribuindo

### Fluxo de Desenvolvimento

1. **Crie uma Issue** descrevendo a task no Kanban do projeto
2. **Crie uma branch** a partir da `main`:
   ```bash
   git checkout -b feature/nome-da-task
   ```
3. **Desenvolva** e teste localmente
4. **Commit** seguindo [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: adiciona endpoint de histórico de cotações"
   ```
5. **Push** e abra um **Pull Request** linkando a Issue

### Padrão de Commits

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Alteração na documentação
- `refactor:` Refatoração de código
- `test:` Adição/modificação de testes
- `chore:` Tarefas de manutenção

---

## 📄 Licença

Propriedade da **Guess Brasil** - Uso interno exclusivo.

---

## 📞 Contato

- **Equipe:** Time de TI Guess Brasil
- **Suporte:** suporte.linx@guessbrasil.com.br

---

<div align="center">

**Desenvolvido pela equipe TI Guess Brasil** 🚀
