# Integrated Logistics Control

**Conferência documental e acompanhamento de entregas — case educacional de João Pedro Caneca.**

Python/SQL e dados sintéticos para acompanhar entregas, preservar entradas e
investigar divergências com histórico. Entrega física e aprovação documental
são estados independentes. O case não representa a operação de uma empresa.

## Estado em 02/11/2026

F1 fechada documentalmente; F2 fechada com limitações (VAL-F2-P04-001).
F3-P01, P02A, P02B e P03 aceitos no escopo demonstrado; P03 registrado por
**VAL-F3-P03-001**. **F3-P04 em consolidação para avaliação; F3 ABERTA**,
aguardando conferência documental/SQL de João e decisão central de fechamento.
A explicação independente de João permanece pendente para revisão final.
F4–F6 bloqueadas. PR #2 aberto e sem merge; nenhuma autorização de merge.

Branch de trabalho: `feat/f3-p03-reliability`. Código demonstrado: `702ede1`;
evidências anteriores à consolidação: `d0cba49`. Não partir de main desatualizada.
A revisão observada no banco de teste é `0006_reliability`.

## O que foi demonstrado

- Ambiente Python isolado, configuração externa, lock com hashes e PostgreSQL local.
- Migrações, histórico, vínculos e restrições; gerador sintético reproduzível.
- FastAPI com OpenAPI, paginação estável, cursor validado e término explícito.
- Falhas HTTP, timeout, JSON inválido e indisponibilidade por HTTP real.
- Captura preservada e rastreável, importação CSV, pedidos, entregas e eventos.
- Idempotência, conflitos explícitos, rejeições recuperáveis, checkpoint atômico,
  rollback, retry limitado, retomada com validação de snapshot e evento atrasado.

Última regressão F3 executada por João no Windows/PostgreSQL: **98 testes
aprovados, nenhum skip, 1 aviso conhecido, 14,05 s**, saída 0; Ruff aprovado.
A consolidação P04 altera somente documentação e reutiliza essa evidência.

Ainda futuros: parsing PDF/XML, conferência/aprovação documental, IA, interface,
métricas/Power BI, Scheduler, CI/E2E e recuperação de release. Referências
JSON de documentos da F2 não equivalem a documentos processados/aprovados.

## Ambiente e configuração

Windows 11 x64; Python 3.13.14; Git 2.55.0.windows.5; PostgreSQL 18.6.
SQLAlchemy 2.0.55, psycopg 3.3.6, Alembic 1.20.0, python-dotenv 1.2.4,
FastAPI 0.150.0, Uvicorn 0.54.0, HTTPX 0.28.1, Starlette 1.9.0,
Pydantic 2.14.1, pytest 9.1.1, Ruff 0.17.1. Lock completo:
[requirements.lock](requirements.lock); registros de versões nos documentos 09–17.
Não atualizar dependências para eliminar o aviso HTTPX/TestClient neste recorte.

Na raiz do projeto, PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Preencher DB_PASSWORD somente no `.env` local. Configuração esperada:
DB_HOST=127.0.0.1, DB_PORT=55432, DB_NAME=ilc, DB_USER=ilc_app,
DB_CONNECT_TIMEOUT=5 e LOG_LEVEL=INFO. Não imprimir ou publicar credenciais.
Os comandos F3 exigem `--database ilc_f2p02b_test`: selecionam esse banco
explicitamente, mantendo DB_NAME=ilc no arquivo. Não usar ilc para as cargas.
A instância existente é local/UTC/SCRAM; ilc_app não é administrador, mas é
proprietário dos objetos do case, sem separação de papéis de produção.

Reprodução da venv e do lock foi observada no mesmo Windows usando cache;
instalação limpa do sistema e portabilidade integral permanecem não comprovadas.
Não reinstalar dependências para conferir P04. Ver [ambiente](docs/09-f2-p01-environment.md)
e [PostgreSQL](docs/10-f2-p02a-postgresql.md) para preparação anterior.

Verificação de revisão atual (somente leitura):

```powershell
python -m alembic -x database=ilc_f2p02b_test current
```

Esperado: `0006_reliability (head)`. As migrações 0001–0006 já foram aplicadas
no banco do case; não repetir downgrade, recriar o cluster ou executar probes
F2 com expectativa fixa em 0003. Backup/restauração pertencem à F6.

## Comandos da F3

Esta seção é referência operacional. **P04 pede somente consulta de evidências
existentes**; captura/carga/verificadores escrevem novas execuções e não precisam
ser repetidos para a consolidação. Comandos na raiz e venv ativa.

Terminal 1, API limitada a loopback:

```powershell
python -m mock_api
```

Terminal 2, consultas HTTP sem banco:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/events?limit=5' | ConvertTo-Json -Depth 8
Invoke-RestMethod 'http://127.0.0.1:8000/openapi.json' | ConvertTo-Json -Depth 20
Get-NetTCPConnection -State Listen -LocalPort 8000 | Select-Object LocalAddress,LocalPort,OwningProcess
```

`/events` serve os 13 registros da fixture em ordem estável, páginas 5/5/3.
Seguir o next_cursor recebido até `null`, acompanhado de has_more=false.
`/docs` oferece Swagger; seus assets padrão dependem de CDN. OpenAPI JSON é local.

Captura simples e carga da captura aceita (escrevem execuções):

```powershell
python -m scripts.api_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --limit 5 --timeout 2
python -m scripts.business_load --database ilc_f2p02b_test --capture-run capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c
```

A carga usa CSV sintéticos versionados e a captura identificada, mais cinco
entradas de duplicata/conflito/inválidos. O total é 18 entradas processadas,
com classificações explícitas; não são 18 novos eventos. Captura simples P02A
não tem retomada; para esse fim usar a CLI P03 abaixo.

Interrupção e retomada transacional (exemplo para execução futura, não repetir em P04):

```powershell
$raw = python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --stop-after-pages 1
$interruptExit = $LASTEXITCODE
$stopped = $raw | ConvertFrom-Json
if ($interruptExit -ne 1 -or $stopped.error_category -ne 'SIMULATED_INTERRUPT_AFTER_COMMIT') { throw 'Investigar interrupcao.' }
$stopped | ConvertTo-Json -Depth 8
python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --resume-run $stopped.capture_run_id
Write-Output "resume_exit=$LASTEXITCODE"
```

Pós-commit: PARTIAL/1 página/5 registros; retomada: SUCCEEDED/3 páginas/13.
Checkpoint e página ficam visíveis na mesma transação; snapshot diferente
interrompe explicitamente. Encerrar API com Ctrl+C ao terminar.

| Comando | Códigos de saída |
|---|---|
| api_capture | 0 SUCCEEDED; 1 FAILED, podendo preservar páginas anteriores |
| reliable_capture | 0 SUCCEEDED; 1 PARTIAL/FAILED ou falha de configuração |
| business_load | 0 SUCCEEDED; 2 PARTIAL por problemas de dados; 1 FAILED |
| check_api_failures / check_api_capture / check_business_load / check_reliability | 0 verificação PASS; 1 falha da verificação |

PARTIAL e rejeição são resultados observáveis, não sucesso integral. O verificador
pode passar ao comprovar uma falha deliberada; o run de falha continua FAILED/PARTIAL.
[Runbook, consultas SQL de rejeições/checkpoint e passagem final](docs/21-f3-p04-consolidation.md).

## Resultados e limites

Fixture original: **8 pedidos, 8 entregas, 13 eventos**. As 18 entradas de negócio
reconciliaram inicialmente em 13 aceitos, 1 duplicado, 1 conflito e 3 rejeitados;
na reexecução, 14 duplicados, 1 conflito e 3 rejeitados. Há um caso de identidade
e dois de ambiguidade de conclusão, sem sobrescrita do evento original.

Uma sentinela de cada entidade já existia: total global inicial 9/9/14.
A recuperação legítima adicionou 1 pedido, 1 entrega e 2 eventos: global
10/10/16, estável na reexecução. Capturas e tentativas repetidas ampliam histórico,
sem representar crescimento correspondente do domínio.

Interrupções foram controladas, sem ensaio de desligamento abrupto; reconciliação
administrativa de invocação abandonada não foi demonstrada. Retry é limitado a
três tentativas transitórias e backoff 0,1/0,2 s; JSON/rejeições não têm retry.
Recuperação de quarentena é explícita, não automática para todos os casos.
Concorrência com duas sessões, CI, instalação limpa e backup/restauração não
foram comprovados. Nenhum SLA documental ou ganho empresarial foi medido.
Esforço humano total da F3 não medido; 14,05 s é tempo de teste, não de trabalho.

## Documentação e histórico

- [Negócio](docs/01-business-understanding.md), [escopo](docs/02-scope-and-acceptance.md), [arquitetura](docs/03-architecture.md).
- [Plano e estado atual](docs/04-delivery-and-learning-plan.md), [contratos](docs/06-event-and-document-contracts.md), [modelo](docs/07-conceptual-and-logical-model.md).
- [F1 documental](docs/08-f1-consolidation-and-analytical-model.md), [F2 consolidada](docs/15-f2-p04-consolidation.md).
- [P01 API](docs/16-f3-p01-events-api.md), [P01 falhas](docs/17-f3-p01-controlled-failures.md).
- [P02A captura](docs/18-f3-p02a-api-capture.md), [P02B carga](docs/19-f3-p02b-business-load.md).
- [P03 confiabilidade — VAL-F3-P03-001](docs/20-f3-p03-reliability.md).
- [P04 consolidação para decisão de fechamento](docs/21-f3-p04-consolidation.md), [contribuição](CONTRIBUTING.md).

Registros antigos de preparação/submissão são históricos; decisões centrais
posteriores e a consolidação 21 definem o estado atual. F3 não foi fechada por
esta publicação. F4 requer passagem de fechamento e cartão central próprios.
