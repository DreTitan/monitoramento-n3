# GOAir Monitoramento N3 - Engenharia

Sistema web para registro e acompanhamento de sub-chamados de calibração encaminhados à engenharia.

## 🚀 Deploy no Railway (Hospedagem na Nuvem)

### Passo 1: Criar conta no Railway
1. Acesse https://railway.app
2. Faça login com GitHub
3. Clique em **"New Project"** → **"Deploy from GitHub repo"**
4. Selecione este repositório

### Passo 2: Configurar variáveis de ambiente
No Railway, após criar o projeto:
1. Vá em **Settings** → **Variables**
2. Adicione as seguintes variáveis:

```
SUPABASE_URL=https://cucwpacpsrkrvkyltaqa.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (chave pública do Supabase)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (chave secreta do Supabase)
```

**Como pegar as chaves do Supabase:**
1. Acesse https://supabase.com/dashboard
2. Selecione o projeto `cucwpacpsrkrvkyltaqa`
3. Vá em **Settings** → **API**
4. Copie: `Project URL` → SUPABASE_URL
5. Copie: `anon public` → SUPABASE_KEY
6. Copie: `service_role secret` → SUPABASE_SERVICE_KEY

### Passo 3: Deploy
1. O Railway detectará o Dockerfile automaticamente
2. Clique em **Deploy** 
3. Aguarde o deploy finalizar (~2-3 minutos)

### Passo 4: Acessar a aplicação
1. No Railway, vá em **Settings** → **Networking**
2. Clique em **Generate Domain**
3. Use o link `.up.railway.app` fornecido
4. Compartilhe esse link com sua equipe!

### Passo 5: Atualizar o Frontend (importante!)
O frontend está configurado para localhost. Após ter o URL de produção:

1. Edite o arquivo `backend/app/frontend.html`
2. Na linha 345, mude:
```javascript
// De:
const API_BASE = 'http://localhost:8000/api/v1';
// Para:
const API_BASE = 'https://seu-app.up.railway.app/api/v1';
```
3. Commit e push - o Railway fará deploy automaticamente

---

## 📋 Requisitos

- Conta no Railway (gratuita)
- Conta no Supabase (já configurada)
- GitHub (para hospedar o código)
- Python 3.11+ (para desenvolvimento local)

## 🚀 Configuração do Supabase

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Clique em "New Project"
3. Preencha os dados:
   - **Name**: `monitoramento-calibracao`
   - **Database Password**: Anote a senha gerada
   - **Region**: Escolha a mais próxima

4. Após criar, vá em **Settings > API**
5. Copie as seguintes informações:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`
   - `service_role` secret → `SUPABASE_SERVICE_KEY`

### 2. Criar Tabela no Banco

1. No Supabase Dashboard, vá em **SQL Editor**
2. Execute o script `backend/app/infrastructure/scripts/create_table.sql`

Ou execute manualmente:

```sql
CREATE TABLE IF NOT EXISTS subchamados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente VARCHAR(255) NOT NULL,
    numero_serie VARCHAR(100) NOT NULL,
    hgid VARCHAR(50) NOT NULL,
    data_fabricacao TIMESTAMP,
    quantidade_exames INTEGER,
    go_premium BOOLEAN DEFAULT FALSE,
    descricao TEXT NOT NULL,
    prioridade VARCHAR(20) DEFAULT 'media',
    status VARCHAR(30) DEFAULT 'aberto',
    analise TEXT,
    imagens JSONB DEFAULT '[]',
    criado_por VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    prazo_sla TIMESTAMP NOT NULL,
    CONSTRAINT chk_prioridade CHECK (prioridade IN ('baixa', 'media', 'alta', 'critica')),
    CONSTRAINT chk_status CHECK (status IN ('aberto', 'em_analise', 'aguardando_informacoes', 'resolvido', 'cancelado'))
);

CREATE INDEX IF NOT EXISTS idx_subchamados_status ON subchamados(status);
CREATE INDEX IF NOT EXISTS idx_subchamados_criado_em ON subchamados(criado_em);
CREATE INDEX IF NOT EXISTS idx_subchamados_prazo_sla ON subchamados(prazo_sla);

ALTER TABLE subchamados ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permitir operações públicas" ON subchamados FOR ALL TO public USING (true) WITH CHECK (true);
```

## 🐳 Executando com Docker

### 1. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e preencha:

```bash
cp backend/.env.example backend/.env
```

Edite o `backend/.env` com suas credenciais do Supabase:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[SUA-SENHA]@db.xxxxx.supabase.co:5432/postgres
```

### 2. Executar com Docker Compose

```bash
# Build e start do container
docker-compose up --build

# Ou em background
docker-compose up -d
```

### 3. Acessar a aplicação

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## 💻 Desenvolvimento Local (sem Docker)

### 1. Criar ambiente virtual

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar ambiente

```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

### 4. Executar

```bash
uvicorn app.main:app --reload
```

## 📁 Estrutura do Projeto

```
monitoramento-calibracao/
├── docker-compose.yml          # Configuração Docker
├── python-api/
│   ├── README.md              # Documentação da API Python
│   ├── docker-compose.yml     # Configuração Docker
│   └── backend/
│       ├── Dockerfile         # Imagem Docker do backend
│       ├── requirements.txt   # Dependências Python
│       ├── .env.example       # Exemplo de variáveis de ambiente
│       └── app/
│           ├── main.py           # Entry point FastAPI
│           ├── config.py         # Configurações
│           ├── api/
│           │   └── routes.py     # Endpoints REST
│           ├── domain/
│           │   ├── entities/     # Entidades de domínio
│           │   └── repositories/ # Interfaces de repositório
│           ├── application/
│           │   └── use_cases/    # Casos de uso / lógica de negócio
│           └── infrastructure/
│               ├── database/     # Cliente Supabase
│               ├── repositories/ # Implementação de repositórios
│               └── scripts/      # Scripts SQL
└── frontend/
    └── index.html            # Interface web
```

## 🔌 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/subchamados` | Criar novo sub-chamado |
| GET | `/api/v1/subchamados` | Listar sub-chamados |
| GET | `/api/v1/subchamados/{id}` | Buscar por ID |
| PUT | `/api/v1/subchamados/{id}` | Atualizar sub-chamado |
| DELETE | `/api/v1/subchamados/{id}` | Deletar sub-chamado |
| POST | `/api/v1/subchamados/{id}/analise` | Adicionar análise |
| GET | `/api/v1/subchamados/atrasados` | Listar atrasados |
| GET | `/api/v1/relatorio-diario` | Relatório diário |
| GET | `/api/v1/estatisticas` | Estatísticas por status |

## 📊 SLA - 48h Úteis

O sistema calcula automaticamente o prazo do SLA de 48h úteis:
- Apenas dias úteis (segunda a sexta)
- Horário comercial (8h às 18h)
- Fins de semana são ignorados

## 👥 Usuários

A aplicação pode ser acessada por todos os analistas de suporte e engenharia **sem necessidade de login/senha**.

---

Desenvolvido para o time de Suporte Nível 3
