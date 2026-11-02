# F3-P03 — Falhas, retomada e reprocessamento recuperável

Estado: estrutura preparada; cartão ABERTO, dependente da ligação de João e das evidências Windows/PostgreSQL. A F3 não está fechada. O próximo cartão depende do gerente.

## Base e preservação

Base técnica aceita `44fcbff`; aceite de P02B e liberação de P03 registrados em `6e10e91589dc7f4f495974d658316eaaf7adf188`. Banco exclusivo do caso: `ilc_f2p02b_test`, usuário `ilc_app`, loopback. Captura de referência preservada: `capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c`. Não apagar evidências, conflitos, sentinelas nem `.vscode/`.

Sem dependências novas. Aviso HTTPX/TestClient permanece como manutenção, sem mudança de versões.

## Lacuna concreta e migração

As revisões anteriores preservam páginas/entradas, mas não guardam posição retomável, histórico de checkpoint, tentativas HTTP ou vínculo entre tentativa rejeitada e reprocessamento interno. A migração aditiva `0006_reliability` cria somente `capture_checkpoints`, `capture_checkpoint_history`, `capture_request_log` e `reprocessing_links`. Reutiliza runs, páginas, inputs, receipts, attempts, entidades e decisões existentes. Nenhuma tabela anterior é removida ou reescrita pela migração. Histórico e vínculos novos são imutáveis; somente o checkpoint corrente muda.

## Captura e retry

`scripts.reliable_capture` usa páginas de cinco itens e URLs HTTP literais `127.0.0.1`, sem redirecionamento/proxy. `advance_page` grava página, entradas, recibos, tentativas, posição e histórico; João conecta essa operação a `engine.begin()`. O checkpoint só fica visível junto com o commit da página. Uma falha dentro do bloco reverte tudo. Registro HTTP separado comprova resposta recebida e NÃO comprova persistência da página.

Retomada utiliza o mesmo capture_run_id e uma nova execução de invocação. Um lock por execução evita duas capturas concorrentes do mesmo checkpoint. Antes de usar cursor salvo, uma sondagem da primeira página verifica dataset_id e total; divergência encerra como SNAPSHOT_CHANGED e não avança. Páginas seguintes também validam snapshot/total. Captura completa não refaz HTTP. Capturas antigas de P02A não ganham checkpoint retroativamente.

Política fixa: no máximo três tentativas por requisição, esperas 0,1 e 0,2 segundos. Transitórios: HTTP 408, 429, 500, 502, 503, 504; ConnectError, ConnectTimeout, ReadTimeout. Outros erros HTTP, JSON inválido, envelope/proveniência/snapshot inválido e rejeições de negócio não recebem retry automático. Timeout configurável 0,1–10 s por operação de rede, resposta limitada a 1 MiB. Não há promessa de deadline global contra servidor que envia bytes indefinidamente.

503 preserva status/corpo das três respostas. Timeout real usa cenário delay de P01. Erro esgotado encerra com código 1, FAILED sem página ou PARTIAL com páginas confirmadas. Invocações antigas preservam o próprio erro mesmo quando a captura termina posteriormente.

## Prática de João — uma ligação central

No editor, abrir **scripts/reliable_capture.py** e substituir a função inteira `commit_page_and_checkpoint`, incluindo o raise `JOAO_RECOVERY_LINK_PENDING`, por:

```python
def commit_page_and_checkpoint(engine, before_commit=False, **page):
    """Grava pagina e checkpoint na mesma transacao."""
    with engine.begin() as connection:
        advance_page(connection, **page)
        if before_commit:
            raise CaptureError("SIMULATED_BEFORE_COMMIT")
```

O erro deliberado ocorre depois das instruções SQL e antes da saída do bloco/commit. A flag de interrupção após commit ocorre depois de ler o checkpoint em outra conexão. São falhas controladas, não ensaio de desligamento do sistema operacional. Encerramento abrupto pode deixar uma invocação antiga RUNNING; reconciliação administrativa de execução abandonada não foi demonstrada neste recorte.

## Comandos Windows — executar na ordem, sem descartar alterações

```powershell
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch falhou.' }
git switch -c feat/f3-p03-reliability --track origin/feat/f3-p03-reliability
if ($LASTEXITCODE -ne 0) { throw 'Troca de branch interrompida; preservar alteracoes.' }
git status --short --branch
git log -2 --oneline
```

Após João salvar a função:

```powershell
python -m ruff format scripts/reliable_capture.py
python -m ruff check mock_api scripts migrations/versions tests/unit tests/capture tests/business tests/reliability
python -m ruff format --check mock_api scripts/reliable_capture.py scripts/reprocess_rejection.py scripts/check_reliability.py scripts/api_capture.py scripts/business_load.py scripts/check_business_load.py scripts/check_api_failures.py migrations/versions/0006_reliability.py tests/unit/test_reliable_capture.py tests/reliability
python -m pytest tests/unit/test_events_api.py tests/unit/test_api_failures.py tests/unit/test_api_capture.py tests/unit/test_business_load.py tests/unit/test_reliable_capture.py -q
if ($LASTEXITCODE -ne 0) { throw 'Testes falharam; interrompido.' }
python -m alembic -x database=ilc_f2p02b_test upgrade 0006_reliability
if ($LASTEXITCODE -ne 0) { throw 'Migracao falhou; interrompido.' }
python -m alembic -x database=ilc_f2p02b_test current
```

Terminal 1, no projeto e venv: `python -m mock_api`. Terminal 2, mesmo projeto e venv:

```powershell
$raw = python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --stop-after-pages 1
$interruptExit = $LASTEXITCODE
$stopped = $raw | ConvertFrom-Json
$stopped | ConvertTo-Json -Depth 8
Write-Output "interrupt_exit=$interruptExit"
if ($interruptExit -ne 1 -or $stopped.records -ne 5 -or $stopped.error_category -ne 'SIMULATED_INTERRUPT_AFTER_COMMIT') { throw 'Interrupcao inesperada.' }
python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --resume-run $stopped.capture_run_id
if ($LASTEXITCODE -ne 0) { throw 'Retomada falhou.' }
```

Esperado: PARTIAL/5/uma página e depois SUCCEEDED/13/três páginas. Encerrar o servidor do terminal 1 com Ctrl+C. Conferir sua porta: `Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue`. Não encerrar processos de terceiros.

## Provas HTTP/SQL automatizadas

```powershell
python -m scripts.check_reliability --database ilc_f2p02b_test --original-capture capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c
$verificationExit = $LASTEXITCODE
Write-Output "verification_exit=$verificationExit"
if ($verificationExit -ne 0) { throw 'Confiabilidade falhou; preservar evidencias.' }
```

O verificador cria e encerra somente seus servidores próprios, em portas efêmeras loopback. Mantém as execuções no banco; nunca as limpa para fabricar sucesso. Reconcilia checkpoint/páginas/entradas/recibos/tentativas/histórico por SQL em novas conexões, compara os 13 payloads recuperados integralmente e reaplica negócio sem novas entidades da fixture original.

| Caso | Esperado | Observado Windows |
|---|---|---|
| Interrupção depois de commit | checkpoint 1, registros 5, PARTIAL | Pendente |
| Falha antes do commit da página 2 | mesma posição; sem página/entradas/recibos/tentativas extras | Pendente |
| Retomada | três páginas, 13 registros, SUCCEEDED | Pendente |
| Reexecutar captura completa | zero requisições | Pendente |
| Snapshot alterado | SNAPSHOT_CHANGED; 1 página/5 registros preservados | Pendente |
| Restaurar snapshot e retomar | 3 páginas/13 registros | Pendente |
| HTTP 503 | três tentativas, corpos preservados, RETRY_EXHAUSTED | Pendente |
| Delay com timeout 0,2 s | três ReadTimeout; erro observável | Pendente |
| JSON inválido | uma requisição; INVALID_JSON | Pendente |
| Recarga de domínio dos mesmos eventos | 14 duplicados, 1 conflito, 3 rejeitados; nenhuma entidade extra | Pendente |
| Referência recuperada | nova tentativa aceita/duplicada, rejeição anterior intacta | Pendente |
| Evento atrasado em ENT-008 | novo histórico; conclusão DELIVERED em 17h intacta | Pendente |
| Reexecutar recuperação | ambos DUPLICATE, entidades sem crescimento | Pendente |

`scripts.reprocess_rejection.recover` usa a rejeição preservada UNRESOLVED-REFERENCE. Cadastra referências legítimas separadas em CSV/JSONL sintéticos versionados (ENT-UNKNOWN, pedido próprio), preserva bytes/hash/run e reprocessa o MESMO input. A tentativa nova tem receipt_key nulo, sem inventar novo recebimento, e `reprocessing_links` aponta para a rejeição original. Evento P03-LATE-TRANSIT, ocorrido às 14h, chega depois da conclusão de ENT-008 às 17h; a decisão vigente permanece idêntica. Na primeira recuperação, esperado acréscimo global de 1 pedido, 1 entrega e 2 eventos; na reexecução, nenhum acréscimo. Não é reparo automático de toda a quarentena.

As consultas estão em `assert_checkpoint`, `inspect_run`, `preserved`, `global_counts`, `recover` e no relatório emitido pelo verificador. O verificador P02B passa a declarar o escopo dos IDs originais, mantendo a expectativa 8/8/13 após as referências legítimas adicionais. A antiga rejeição INVALID_REFERENCE continua histórica; o novo processamento do mesmo caso passa a duplicado após recuperação.

Regressão com banco explicitamente habilitado:

```powershell
$env:ILC_CAPTURE_TEST_DATABASE = 'ilc_f2p02b_test'
$env:ILC_BUSINESS_TEST_DATABASE = 'ilc_f2p02b_test'
$env:ILC_BUSINESS_CAPTURE_RUN = 'capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c'
$env:ILC_RELIABILITY_TEST_DATABASE = 'ilc_f2p02b_test'
$env:ILC_RELIABILITY_CAPTURE_RUN = $env:ILC_BUSINESS_CAPTURE_RUN
try {
    python -m pytest tests/unit/test_events_api.py tests/unit/test_api_failures.py tests/unit/test_api_capture.py tests/unit/test_business_load.py tests/unit/test_reliable_capture.py tests/capture tests/business tests/reliability -q -s
    $regressionExit = $LASTEXITCODE
    Write-Output "regression_exit=$regressionExit"
} finally {
    Remove-Item Env:ILC_CAPTURE_TEST_DATABASE,Env:ILC_BUSINESS_TEST_DATABASE,Env:ILC_BUSINESS_CAPTURE_RUN,Env:ILC_RELIABILITY_TEST_DATABASE,Env:ILC_RELIABILITY_CAPTURE_RUN -ErrorAction SilentlyContinue
}
git diff --check
git status --short --branch
```

## Evidências disponíveis e passagem

Em 02/11/2026, assistente executou testes locais Linux/Python 3.12: 118 testes unitários aprovados, 11 subtestes, um aviso HTTPX/TestClient já conhecido; 18 casos novos de retry/snapshot incluídos. Esses testes não comprovam persistência, rollback ou retomada em PostgreSQL. A função central publicada fica deliberadamente pendente para João; o verificador SQL falhará enquanto ela não for implementada. Nenhum teste PostgreSQL deste cartão foi executado pelo assistente; nenhuma migração foi aplicada por ele no banco de João. Ruff aprovado em mock_api/scripts/migrações/testes do recorte; format aprovado (15 arquivos). Comando de regressão do recorte executado sem banco habilitado: 94 passed, 4 skipped (PostgreSQL), 1 warning. Os skips são pendências explícitas, não aceite de integração.

Feito: estrutura, política limitada, auditoria, cenários, fixtures legítimas, testes e comandos. Prática/aprendizagem: ligação, interrupção e retomada pendentes; explicação independente reservada à revisão final. Pendências: resultados HTTP/SQL Windows, diferenças esperado × observado, regressão, commit da contribuição de João publicado e passagem ao gerente. Não consolidar nem fechar F3 antes da validação central.
