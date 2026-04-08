# SisDoa - Sistema de Controle de Doações

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/sisdoa)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![CI](https://github.com/yourusername/sisdoa/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/sisdoa/actions)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## Sobre o Projeto

**SisDoa** é uma aplicação CLI (Command Line Interface) desenvolvida para pequenas ONGs gerenciareM o estoque e a validade de doações de alimentos e medicamentos.

### A Dor que Resolve

Pequenas organizações sem fins lucrativos frequentemente:
- **Perdem doações por vencimento** por falta de controle de validade
- **Não têm visibilidade** do que está próximo de vencer
- **Precisam de uma solução simples** sem complexidade de sistemas web

O SisDoa resolve isso com:
- Alertas automáticos de itens próximos do vencimento
- Interface simples via terminal (sem necessidade de navegador)
- Persistência local (SQLite) - sem necessidade de servidor

---

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.12+ |
| CLI Framework | Typer |
| ORM | SQLAlchemy 2.0 (Core) |
| Banco de Dados | SQLite |
| Gerenciador de Pacotes | uv |
| Testes | pytest |
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

Registra uma nova doação no estoque.

```bash
uv run sisdoa add "Arroz 5kg" 10 15/12/2026
```

**Parâmetros:**
- `nome`: Nome do item (ex: "Arroz 5kg", "Paracetamol 500mg")
- `quantidade`: Número de unidades
- `data-validade`: Data no formato DD/MM/AAAA

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
# 1. Registrar doações recebidas
uv run sisdoa add "Arroz 5kg" 20 30/06/2027
uv run sisdoa add "Feijão 1kg" 15 15/01/2026
uv run sisdoa add "Leite UHT" 50 10/01/2026

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

**Cobertura de testes:**
- ✅ Happy path (operações bem-sucedidas)
- ✅ Casos de falha (estoque insuficiente, data inválida)
- ✅ Casos limite (zero quantidade, item expirado)

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

## Autor

**Eduardo Fernandes Alves**

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
