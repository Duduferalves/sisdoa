# SisDoa - Sistema de Controle de Doações

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/sisdoa)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![CI](https://github.com/yourusername/sisdoa/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/sisdoa/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## Sobre o Projeto

**SisDoa** é uma aplicação CLI (Command Line Interface) desenvolvida para pequenas ONGs gerenciarem o estoque e a validade de doações de alimentos e medicamentos.

### A Dor que Resolve

Pequenas organizações sem fins lucrativos frequentemente:
- **Perdem doações por vencimento** por falta de controle de validade
- **Não têm visibilidade** do que está próximo de vencer
- **Precisam de uma solução simples** sem complexidade de sistemas web

O SisDoa resolve isso com:
- Alertas automáticos de itens próximos do vencimento
- Interface simples via terminal (sem necessidade de navegador)
- Persistência local (SQLite) - sem necessidade de servidor
- Busca automática de produtos por código de barras via API Open Food Facts

---

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.12+ |
| CLI Framework | Typer |
| ORM | SQLAlchemy 2.0 (Core) |
| Banco de Dados | SQLite |
| Gerenciador de Pacotes | uv |
| Testes | pytest + respx |
| HTTP Client | httpx |
| Linting/Format | Ruff |
| CI/CD | GitHub Actions |

---

## Arquitetura

O projeto segue **Clean Architecture** com separação clara de responsabilidades:

```
src/sisdoa/
├── domain/          # Entidades e regras de negócio
├── repository/      # Acesso a dados (SQLite)
├── cli/             # Interface com usuário (Typer)
├── infrastructure/  # Integrações externas (API Gateway)
└── config.py        # Configurações
```

**Princípio:** A camada CLI NÃO contém lógica de banco de dados.

---

## Instalação

### Pré-requisitos

- Python 3.12 ou superior
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/yourusername/sisdoa.git
   cd sisdoa
   ```

2. **Instale as dependências com uv:**
   ```bash
   uv sync --all-extras
   ```

3. **Verifique a instalação:**
   ```bash
   uv run sisdoa --help
   ```

---

## Uso

### Comandos Disponíveis

#### 1. Adicionar Item (`add`)

Registra uma nova doação no estoque. O nome do produto é buscado automaticamente na API do Open Food Facts usando o código de barras (EAN).

```bash
uv run sisdoa add 7891010101010 10 "15/12/2026"
```

**Parâmetros:**
- `ean`: Código de barras do produto (EAN-13 ou EAN-8)
- `quantidade`: Número de unidades
- `data-validade`: Data no formato DD/MM/AAAA

**Exemplo:**
```bash
# Adicionar 10 unidades de um produto com validade em 15/12/2026
uv run sisdoa add 7891010101010 10 "15/12/2026"
```

**Tratamento de Erros:**
- Se o produto não for encontrado na API, uma mensagem amigável será exibida
- Erros de conexão ou timeout são tratados e informados ao usuário

#### 2. Listar Itens (`list`)

Mostra todos os itens no estoque com status de validade.

```bash
# Listar todos os itens
uv run sisdoa list

# Mostrar apenas itens que precisam de atenção
uv run sisdoa list --alerts
```

#### 3. Alertas (`alerts`)

Exibe apenas itens vencidos ou próximos do vencimento.

```bash
uv run sisdoa alerts
```

#### 4. Dar Baixa (`remove`)

Reduz a quantidade de um item (quando consumido/doado).

```bash
uv run sisdoa remove 1 5
```

**Parâmetros:**
- `id`: ID do item
- `quantidade`: Quantas unidades remover

#### 5. Remover Item (`delete`)

Exclui completamente um registro do estoque.

```bash
uv run sisdoa delete 1
```

#### 6. Informações (`info`)

Mostra detalhes de um item específico.

```bash
uv run sisdoa info 1
```

#### 7. Versão (`version`)

```bash
uv run sisdoa version
```

---

## Exemplo de Fluxo de Uso

```bash
# 1. Registrar doações recebidas (usando código de barras)
uv run sisdoa add 7891010101010 20 "30/06/2027"
uv run sisdoa add 7892020202020 15 "15/01/2026"
uv run sisdoa add 7893030303030 50 "10/01/2026"

# 2. Verificar estoque completo
uv run sisdoa list

# 3. Verificar alertas de validade
uv run sisdoa alerts

# 4. Dar baixa quando distribuir itens
uv run sisdoa remove 1 5  # Remove 5 unidades do item ID 1

# 5. Remover registro inserido por engano
uv run sisdoa delete 2
```

---

## Desenvolvimento

### Rodando Testes

Os testes usam SQLite em memória (`:memory:`) e NÃO tocam no disco.

```bash
# Executar todos os testes
uv run pytest

# Executar com verbose
uv run pytest -v

# Executar testes específicos
uv run pytest tests/test_repository.py -v
uv run pytest tests/test_cli.py -v
uv run pytest tests/integration/test_api_client.py -v

# Executar com coverage
uv run pytest --cov=src/sisdoa
```

### Rodando Linter (Ruff)

```bash
# Verificar problemas
uv run ruff check src tests

# Corrigir automaticamente
uv run ruff check src tests --fix

# Verificar formatação
uv run ruff format --check src tests

# Formatar código
uv run ruff format src tests
```

### Estrutura de Testes

| Arquivo | Responsabilidade |
|---------|------------------|
| `conftest.py` | Fixtures com DB em memória |
| `test_repository.py` | Testes da camada de dados |
| `test_cli.py` | Testes da interface CLI |
| `tests/integration/test_api_client.py` | Testes de integração com API (mock) |

**Cobertura de testes:**
- ✅ Happy path (operações bem-sucedidas)
- ✅ Casos de falha (estoque insuficiente, data inválida)
- ✅ Casos limite (zero quantidade, item expirado)
- ✅ Integração com API Open Food Facts (cenários 200 OK e 404 Not Found)

---

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SISDOA_DB_PATH` | Caminho do banco de dados | `~/.sisdoa/sisdoa.db` |
| `SISDOA_EXPIRY_THRESHOLD` | Dias para alerta de validade | `7` |

**Exemplo:**
```bash
export SISDOA_DB_PATH=/custom/path/db.sqlite
export SISDOA_EXPIRY_THRESHOLD=14
```

---

## CI/CD

O pipeline do GitHub Actions é executado em cada `push` ou `pull request` para `main`:

1. **Setup** - Python 3.12 + uv
2. **Lint** - Ruff check (falha se houver erros)
3. **Format** - Ruff format --check
4. **Testes** - pytest com todos os testes

---

## Deploy e Execução em Container/Nuvem

O SisDoa pode ser empacotado em um container Docker para execução em ambientes de nuvem ou qualquer sistema com Docker instalado.

### Pré-requisitos

- Docker instalado e configurado
- Acesso ao terminal com permissões para executar Docker

### Construindo a Imagem

1. **Navegue até a raiz do projeto:**
   ```bash
   cd sisdoa
   ```

2. **Construa a imagem Docker:**
   ```bash
   docker build -t sisdoa .
   ```

   **O que acontece:**
   - A imagem base `python:3.12-slim` é baixada (se não estiver em cache)
   - O `uv` (gerenciador de pacotes) é instalado
   - As dependências são instaladas a partir do `pyproject.toml` e `uv.lock`
   - O código fonte é copiado e o projeto é instalado

### Executando o Container

1. **Ver ajuda do comando:**
   ```bash
   docker run -it sisdoa --help
   ```

2. **Listar itens no estoque:**
   ```bash
   docker run -it sisdoa list
   ```

3. **Adicionar um novo item:**
   ```bash
   docker run -it sisdoa add 7891010101010 10 "15/12/2026"
   ```

4. **Ver alertas de validade:**
   ```bash
   docker run -it sisdoa alerts
   ```

### Persistência de Dados

Por padrão, os dados são armazenados dentro do container e serão perdidos quando o container for removido. Para persistir os dados:

1. **Use um volume Docker:**
   ```bash
   docker run -it -v sisdoa-data:/root/.sisdoa sisdoa list
   ```

2. **Ou monte um diretório local:**
   ```bash
   docker run -it -v /caminho/local:/root/.sisdoa sisdoa list
   ```

### Execução em Nuvem

A imagem Docker pode ser executada em qualquer plataforma que suporte containers:

- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

**Exemplo com Google Cloud Run:**
```bash
# Build e push para Google Container Registry
docker build -t gcr.io/SEU_PROJETO/sisdoa .
docker push gcr.io/SEU_PROJETO/sisdoa

# Deploy no Cloud Run
gcloud run deploy sisdoa --image gcr.io/SEU_PROJETO/sisdoa
```

---

## Versionamento Semântico

Este projeto segue [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Mudanças incompatíveis
- **MINOR** (1.1.0): Novas funcionalidades compatíveis
- **PATCH** (1.0.1): Correções de bugs compatíveis

**Versão atual:** `1.0.0`

---

## Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Autores

- **Eduardo Fernandes Alves**
- **Paulo**

---

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Requisitos para PR:**
- ✅ Todos os testes passando
- ✅ Ruff check sem erros
- ✅ Código formatado com Ruff
