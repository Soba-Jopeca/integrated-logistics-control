# Integrated Logistics Control

**Conferência documental e acompanhamento de entregas — case educacional.**

Projeto de João Pedro Caneca, desenvolvido com orientação técnica, para
transformar necessidades de logística em uma solução verificável com Python
e SQL. Entrega física e regularidade documental são estados independentes.

**Estado em 20/10/2026:** F1 fechada no escopo documental. Passos técnicos
P01, P02A–D e P03 da F2 aceitos com limitações. Verificação final da P04
aprovada localmente; decisão central pendente. F2 aberta e F3–F6 bloqueadas. Este PR não autoriza merge nem início da F3.

## O que está implementado

- Ambiente Python isolado, dependências fixadas com hashes e configuração externa.
- PostgreSQL dedicado e local; conexão SQLAlchemy/psycopg sem imprimir segredos.
- Três revisões Alembic e dezenove tabelas com vínculos, histórico e restrições.
- Ciclos reversíveis observados exclusivamente no banco descartável do case.
- Gerador de entradas sintéticas com semente e volume adicional configurável.
- Fixtures pequenas, manifesto de expectativas, verificação de hashes e testes.

Ainda são futuras: API/ingestão, parsing de PDF/XML, conferência funcional,
aplicação web, SQL/DAX/Power BI, agendamento, CI/E2E e recuperação de release.
Documentos gerados na F2 são referências JSON sintéticas, não PDFs/XML reais.
Resultados de negócio no manifesto são **esperados, não executados**.

## Ambiente aceito

Windows 11 x64; Python 3.13.14; Git 2.55.0.windows.5; PostgreSQL 18.6.
SQLAlchemy 2.0.55, psycopg 3.3.6, Alembic 1.20.0, python-dotenv 1.2.4,
pytest 9.1.1 e Ruff 0.17.1. Dependências completas em requirements.lock.
Versões e fontes oficiais consultadas constam nos registros 09–14.

O lock foi reproduzido em nova venv no mesmo Windows/Python, usando cache.
Isso não comprova instalação limpa do sistema nem portabilidade integral.

### Nova venv — PowerShell na raiz

Este bloco documenta a reprodução anterior; na verificação P04 usa-se a
venv existente, sem reinstalar ou atualizar dependências.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: -r requirements.lock
.\.venv\Scripts\python.exe -m pip check
```

Use Python 3.13.14 x64 para reproduzir o ambiente aceito. Não regenere o lock
como parte da reprodução. Preparação detalhada: [F2-P01](docs/09-f2-p01-environment.md).

### Configuração e conexão

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe scripts/check_db_connection.py
```

Antes da conexão, preencher DB_PASSWORD somente no .env local. As demais
variáveis estão em .env.example: DB_HOST, DB_PORT, DB_NAME, DB_USER,
DB_CONNECT_TIMEOUT e LOG_LEVEL. Não publicar .env nem URL com credenciais.
O verificador imprime identidade, versão, endereço, porta, fuso e privilégios.

Instância exclusiva: 127.0.0.1:55432, UTC, SCRAM, usuário ilc_app sem
privilégios administrativos; banco ilc. Como proprietário, ilc_app pode
alterar DDL: não representa separação de papéis de produção.

Operação da instância existente, se necessária:

```powershell
& 'C:\ILC-PostgreSQL\18.6\bin\pg_ctl.exe' status -D 'C:\ILC-PostgreSQL\ilc-data-18'
```

Inicialização/parada controladas e configuração: [F2-P02A](docs/10-f2-p02a-postgresql.md).
Não repetir initdb nem apagar o cluster como rollback.

## Migrações e testes de integração

As migrações estão protegidas para atuar **somente** em ilc_f2p02b_test,
preparado anteriormente para o case, com proprietário ilc_app. O banco ilc
é usado pelo verificador de conexão; não recebeu estas migrações.
O parâmetro explícito abaixo não altera DB_NAME no .env.

```powershell
.\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade 0003_decisions_conflicts
.\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
$env:ILC_TEST_DATABASE = 'ilc_f2p02b_test'
try {
    .\.venv\Scripts\python.exe -m pytest -q tests/integration
} finally {
    Remove-Item Env:ILC_TEST_DATABASE -ErrorAction SilentlyContinue
}
```

Preparação e evidências: [núcleo 0001](docs/11-f2-p02b-core-migration.md),
[documentos 0002](docs/12-f2-p02c-document-migration.md) e
[decisões/conflitos 0003](docs/13-f2-p02d-decisions-conflicts.md).
Os ciclos de downgrade/upgrade já foram comprovados; P04 não os repete.
Downgrade remove dados próprios da revisão; nova subida recria estrutura,
não restaura dados apagados. Backup/restauração continuam para F6.

## Entradas sintéticas reproduzíveis

Sem banco, ingestão ou parser. Volume é o número de entregas consistentes
adicionais às oito entregas básicas das fixtures. Usar destinos novos:

```powershell
.\.venv\Scripts\python.exe -m scripts.synthetic_generator --seed 20261019 --volume 25 --output data/generated/f2p03-a
.\.venv\Scripts\python.exe -m scripts.synthetic_generator --seed 20261019 --volume 25 --output data/generated/f2p03-b
.\.venv\Scripts\python.exe -m scripts.check_synthetic_dataset data/generated/f2p03-a --compare data/generated/f2p03-b
```

Esses dois diretórios já foram usados na execução P03. Para outra execução,
escolher nomes novos: o gerador recusa sobrescrita. data/generated/ fica fora
do Git. Fixtures pequenas versionadas usam UTF-8/LF fixado por .gitattributes.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_synthetic_generator.py
.\.venv\Scripts\python.exe -m scripts.check_synthetic_dataset tests/fixtures/synthetic/v1
```

Mesmo seed/configuração produziu arquivos, bytes e hashes idênticos.
Detalhes, formatos e manifesto: [F2-P03](docs/14-f2-p03-synthetic-generator.md)
e [fixtures](tests/fixtures/synthetic/README.md).

## Verificação final da F2-P04

```powershell
.\.venv\Scripts\python.exe -m ruff check --select E4,E7,E9,F,I,B,UP,SIM,C4,BLE scripts migrations tests
.\.venv\Scripts\python.exe -m ruff format --check scripts migrations tests
```

Verificação final observada no Windows em 20/10/2026: Ruff aprovado,
21 arquivos já formatados, 24 testes do gerador e 11 subtestes em 0,84 s,
147 testes de integração em 8,44 s, fixture, sentinelas e conexão aprovadas.
A instância existente estava parada; foi iniciada e reconferida sem recriar
banco nem repetir downgrade. Não houve alteração de código nessa verificação.
[Passagem consolidada F2 e pendências](docs/15-f2-p04-consolidation.md).

## Limites e responsabilidades futuras

O banco garante integridade estrutural, não executa as regras operacionais
de conferência, deduplicação ou resolução automática de conflitos.
Acrescentar motivos a avaliações históricas ainda depende de proteção na
aplicação. Concorrência com duas sessões não foi ensaiada. CI, instalação
limpa, backup/restauração e migração do banco ilc não foram comprovados.

Dados exclusivamente sintéticos. Não há integração ERP/WMS real nem
representação oficial de empresa. Nenhum ganho financeiro ou operacional
empresarial foi medido. Não há SLA documental empresarial validado.

## Documentação e histórico

- [Negócio](docs/01-business-understanding.md), [escopo](docs/02-scope-and-acceptance.md) e [arquitetura](docs/03-architecture.md).
- [Plano e estado atual](docs/04-delivery-and-learning-plan.md).
- [Métricas propostas](docs/05-metrics-and-rules.md), [contratos](docs/06-event-and-document-contracts.md) e [modelo](docs/07-conceptual-and-logical-model.md).
- [Fechamento documental F1 — VAL-F1-P04-001](docs/08-f1-consolidation-and-analytical-model.md#registro-final-autorizado--val-f1-p04-001).
- [Contribuição](CONTRIBUTING.md).

F1 fechada documentalmente em 16/10/2026. Os registros 09–14 preservam as
evidências de cada passo da F2; estados pendentes neles são históricos e
devem ser lidos junto da consolidação 15 e das decisões centrais posteriores.
F2 ainda depende de decisão central de fechamento. PR não significa merge.
