# F3-P03 — Falhas, retomada e reprocessamento recuperável

Estado atual em 02/11/2026: F3-P03 ACEITO no escopo demonstrado — **VAL-F3-P03-001**, recebido no cartão humano F3-P04. F3 permanece ABERTA, em consolidação para avaliação central. A F3 não está fechada. O próximo cartão depende do gerente.

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
| Interrupção depois de commit | checkpoint 1, registros 5, PARTIAL | PARTIAL; last_page=1, records=5; saída 1 na prática manual |
| Falha antes do commit da página 2 | mesma posição; sem página/entradas/recibos/tentativas extras | SIMULATED_BEFORE_COMMIT; checkpoint 1/5 e contagens SQL intactas |
| Retomada | três páginas, 13 registros, SUCCEEDED | SUCCEEDED; last_page=3, records=13 |
| Reexecutar captura completa | zero requisições | SUCCEEDED; requests=0 |
| Snapshot alterado | SNAPSHOT_CHANGED; 1 página/5 registros preservados | SNAPSHOT_CHANGED; PARTIAL com 1/5 preservados |
| Restaurar snapshot e retomar | 3 páginas/13 registros | SUCCEEDED; 3/13 |
| HTTP 503 | três tentativas, corpos preservados, RETRY_EXHAUSTED | FAILED; RETRY_EXHAUSTED:HTTP_503; requests=3; três corpos 503 preservados |
| Delay com timeout 0,2 s | três ReadTimeout; erro observável | FAILED; RETRY_EXHAUSTED:ReadTimeout; requests=3 |
| JSON inválido | uma requisição; INVALID_JSON | FAILED; INVALID_JSON; requests=1 |
| Recarga de domínio dos mesmos eventos | 14 duplicados, 1 conflito, 3 rejeitados; nenhuma entidade extra | 18 entradas = 14 DUPLICATE + 1 CONFLICT + 3 REJECTED; entidades inalteradas |
| Referência recuperada | nova tentativa aceita/duplicada, rejeição anterior intacta | ACCEPTED; nova tentativa ligada à rejeição anterior; mesmo input e received_at |
| Evento atrasado em ENT-008 | novo histórico; conclusão DELIVERED em 17h intacta | ACCEPTED; DELIVERED antes/depois; conclusão 17h, ocorrido atrasado 14h |
| Reexecutar recuperação | ambos DUPLICATE, entidades sem crescimento | DUPLICATE nos dois eventos; contagens 10/10/16 inalteradas |

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

## Registro histórico da preparação (anterior à execução Windows)

Em 02/11/2026, assistente executou testes locais Linux/Python 3.12: 118 testes unitários aprovados, 11 subtestes, um aviso HTTPX/TestClient já conhecido; 18 casos novos de retry/snapshot incluídos. Esses testes não comprovam persistência, rollback ou retomada em PostgreSQL. A função central publicada fica deliberadamente pendente para João; o verificador SQL falhará enquanto ela não for implementada. Nenhum teste PostgreSQL deste cartão foi executado pelo assistente; nenhuma migração foi aplicada por ele no banco de João. Ruff aprovado em mock_api/scripts/migrações/testes do recorte; format aprovado (15 arquivos). Comando de regressão do recorte executado sem banco habilitado: 94 passed, 4 skipped (PostgreSQL), 1 warning. Os skips são pendências explícitas, não aceite de integração.

Feito: estrutura, política limitada, auditoria, cenários, fixtures legítimas, testes e comandos. Prática/aprendizagem: ligação, interrupção e retomada pendentes; explicação independente reservada à revisão final. Pendências: resultados HTTP/SQL Windows, diferenças esperado × observado, regressão, commit da contribuição de João publicado e passagem ao gerente. Não consolidar nem fechar F3 antes da validação central.

## Evidências Windows/PostgreSQL — execução de João em 02/11/2026

Fonte: saídas fornecidas por João neste chat executor, após implementar a ligação central. Nenhuma execução PostgreSQL remota pelo assistente foi alegada.

- Migração aplicada e consultada: `0006_reliability (head)`.
- Contribuição local: `commit_page_and_checkpoint` usa `engine.begin()`, chama `advance_page` na conexão da transação e lança SIMULATED_BEFORE_COMMIT antes do commit quando solicitado. Ruff/format e 18 testes de política aprovados antes da prática.
- Prática manual: captura `capture-p03-c2e882d8-5f83-4dd7-bbcb-bca8b926ed6d` interrompida em 1 página/5 registros/PARTIAL (interrupt_exit=1), retomada até 3 páginas/13 registros/SUCCEEDED. A linha numérica resume_exit não foi incluída na saída manual; o estado SUCCEEDED foi observado, sem inferir o valor omitido.
- API manual iniciou em 127.0.0.1:8000, PID 18956; logs mostram partida, chamadas e encerramento completo.
- Verificador HTTP/SQL: verification=PASS, verification_exit=0, http_children_stopped=true, último PID 19296. Capture_run principal `capture-p03-02e5146c-2341-4cd9-846a-49922afd3f2a`: interrupção pós-commit 1/5; rollback pré-commit 1/5; retomada 3/13; noop concluído com zero requisições.
- Invocações auditáveis: interrupção `capture-invocation-fef70fef-082a-4c8b-8c3d-7f52c789240b`; rollback `capture-invocation-de1cddd4-47fa-4854-9d2b-47675ebdbb19`; retomada `capture-invocation-31cb3a93-8a98-4092-8bd9-77fcdb64a92b`.
- Retry HTTP: captura `capture-p03-2276a7f4-299b-4776-8bfa-c0cba91b30e1`, FAILED/zero registros/três tentativas. Cada status 503 e corpo `{"scenario":"http_503","error":"SIMULATED_UNAVAILABLE"}` recuperado por SQL.
- Timeout: `capture-p03-469a626c-eee3-4472-8a5a-239dca999536`, FAILED/RETRY_EXHAUSTED:ReadTimeout/três tentativas/zero registros.
- JSON inválido: `capture-p03-02b459d0-f8b8-4dc2-8b46-6d56f118be4c`, FAILED/INVALID_JSON/uma requisição/zero registros.
- Snapshot: `capture-p03-9c86513e-dcdf-4b61-a736-e0e01d23984d` bloqueado em 1/5; retomado com snapshot original até 3/13.
- Recarga de negócio `business-355810fb-430e-4e59-9967-027701c8992f`: 8 pedidos e 8 entregas DUPLICATE; 18 entradas de evento reconciliadas em 14 DUPLICATE, 1 CONFLICT e 3 REJECTED, sem crescimento das entidades.
- Recuperação `reprocess-p03-47614ec6-c595-458a-a36d-d3d27d70a849`: rejeição anterior `8e22fc1a-3e32-49c1-ada9-8cca7376185b`, nova tentativa aceita `e5ca25a8-8956-49e7-902f-9670b1855c26`, mesmo input `569d6b2d-1ba0-4a8e-a57a-037c5878bb50`. received_at original 2026-11-02T22:38:32.004797+00:00 preservado, rejeição mantida e nenhum novo recibo.
- Evento atrasado aceito, ocorrido em 2026-10-16T14:00:00Z; conclusão em 2026-10-16T17:00:00.000000Z e estado DELIVERED mantidos.
- Reexecução `reprocess-p03-e641c0ef-91ce-429c-b81c-77628b89e441`: ambos DUPLICATE; nova tentativa `0d6140a0-2835-472d-ab4d-5d1b879cd260` ligada à rejeição original.
- Contagens globais (pedidos/entregas/eventos), incluindo sentinelas: 9/9/14 antes, 10/10/16 após recuperação e 10/10/16 após reexecução. Acréscimo legítimo de 1/1/2; não se confunde com o escopo original de 8/8/13.
- Captura P02A e sentinelas preservadas; assinatura SQL/bytes original permanece `153cbf78785fdefe83848db9426a195083bdde8eae8a13a51f957ca49bf7aad0`.
- Regressão final Windows, com os cinco env vars de opt-in acima e os testes unitários/capture/business/reliability: **98 passed, 1 warning in 14.05s**, nenhum skip, regression_exit=0. Ruff aprovado; git diff --check sem saída de erro. O aviso StarletteDeprecationWarning HTTPX/TestClient permanece manutenção, sem alteração de dependências.
- Git ao fim da regressão: feat/f3-p03-reliability alinhada ao origin em f008c32; única alteração rastreada local em scripts/reliable_capture.py e .vscode/ não rastreado preservado.

## Passagem ao gerente — entrega publicada em 02/11/2026

Requisitos exercitados: R06/R07, regressão de R05 e controles locais de R15. Artefatos: migração 0006, scripts de captura confiável/reprocessamento/verificação, fixtures de referências legítimas e atraso, testes e este registro esperado × observado.

Prática concluída de João: implementou a ligação transacional central, executou migração, iniciou/encerrou API, provocou interrupção, retomou e executou verificador e regressão com PostgreSQL. Explicação independente permanece adiada para a revisão final por decisão do cartão; não foi inferida a partir dos comandos.

Entrega técnica publicada por João em `702ede1` — `feat: connect atomic page and checkpoint recovery`, após sincronizar as evidências de `48fe921`. O push foi observado; a saída Git confirmou HEAD e origin/feat/f3-p03-reliability em 702ede1, sem alterações rastreadas pendentes e com `.vscode/` não rastreado preservado. Este registro documental posterior somente atualiza a passagem; não altera o código testado. O commit de preparação f008c32 permanece histórico e contém o ponto de edição anterior.

Decisão posterior recebida no cartão humano F3-P04: P03 aceito por VAL-F3-P03-001 no escopo demonstrado, preservando as limitações acima. Sem merge, sem consolidação e sem fechamento da F3. O cartão seguinte F3-P04 foi autorizado para consolidação documental; explicação independente permanece para a revisão final. Não foi enviada mensagem automática a outro chat.

Limitações mantidas: interrupção controlada, não desligamento abrupto do sistema; retomada exige snapshot igual; orçamento de retry fixo; recuperação explícita do caso de referência, sem automação de toda a quarentena; aviso HTTPX/TestClient pendente.

## Aceite VAL-F3-P03-001 e transição para P04

Em 02/11/2026 João encaminhou F3-P04 com ordem explícita de registrar
VAL-F3-P03-001, base técnica `702ede1` e evidências `d0cba49`. Esta é a autoridade
para registrar o aceite P03; não foi inferido do sucesso dos testes. P04 reúne
README, plano e [passagem final 21](21-f3-p04-consolidation.md), para decisão
de fechamento da F3. Conferência read-only de João e explicação independente
continuam identificadas nas respectivas pendências; nenhuma fase foi fechada
ou iniciada por esta atualização. Registros anteriores são históricos.
