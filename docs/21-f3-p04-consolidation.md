# 21 — F3-P04: consolidação para avaliação de fechamento

Data: 02/11/2026. Projeto: Integrated Logistics Control — End to End.
Repositório: [Soba-Jopeca/integrated-logistics-control](https://github.com/Soba-Jopeca/integrated-logistics-control).

**Estado: F3 ABERTA. P04 entregue para avaliação central: SQL/Git demonstrados por João e comandos conferidos pelo assistente por delegação explícita de João.**
Esta consolidação não emite fechamento, não autoriza merge e não inicia F4.
A explicação independente permanece pendente para revisão final, como determinado
nos cartões. Não foi inferida aprendizagem independente pelos resultados dos testes.

## Autoridade, base e estado técnico

Cartão humano F3-P04 recebido neste chat autoriza registrar **VAL-F3-P03-001**
e consolidar P01/P02A/P02B/P03 aceitos. Código final demonstrado:
[`702ede1`](https://github.com/Soba-Jopeca/integrated-logistics-control/commit/702ede1).
Evidências e passagem anteriores:
[`d0cba49`](https://github.com/Soba-Jopeca/integrated-logistics-control/commit/d0cba49).
O aceite P03 limita-se ao comportamento demonstrado, com as limitações abaixo;
não equivale a fechamento da fase. Não inventar IDs adicionais para os demais aceites.

| Item | Estado/evidência |
|---|---|
| Branch atual | feat/f3-p03-reliability; manter essa branch para a atualização documental |
| HEAD antes de P04 | d0cba49 local/remoto, sincronização fast-forward informada por João |
| Código técnico | 702ede1, ancestral da consolidação |
| Revisão observada | 0006_reliability (head), Windows de João |
| Banco alvo | ilc_f2p02b_test; usuário ilc_app; 127.0.0.1:55432 |
| Migrações da F3 | 0004_api_capture, 0005_business_processing, 0006_reliability, aditivas e justificadas nos docs 18–20 |
| API | 127.0.0.1:8000 manual; verificadores usam portas efêmeras loopback |
| PR #2 | Consultado no início de P04: aberto, merged=false; não alterado |
| Alteração P04 | Somente documentação; nenhum código, fixture, lock ou esquema alterado |
| Evidência Git P04 | João sincronizou ee59574; HEAD/origin iguais, 0 0, sem alteração rastreada; .vscode/ preservado |

O SHA de publicação documental deve acompanhar a passagem ao gerente; ele é
descendente de d0cba49 e não modifica o código técnico testado em 702ede1.

## R05–R07: rastreabilidade de entrega e aceite

| Requisito / cartão | Comportamento observado | Código / evidências |
|---|---|---|
| R05 / P01 | OpenAPI; cursor/limite/ordem estáveis; páginas 5/5/3 e término null/false; 13 registros reconciliados; falhas reais de timeout, 503, JSON inválido e conexão | Código 8554901; evidência 4827619; docs 16–17; 34 testes Windows, 4,19 s, saída 0 |
| R06 / P02A | API → bytes/inputs preservados; origem, hash, recebimento e run_id; normal 13/3 páginas; falha HTTP após primeira página preserva 5 registros e corpo 503, run FAILED | Código 2b4b72a; aceite registrado em 60cc75f; doc 18; 65 testes, 5,96 s, saída 0 |
| R06/R07 / P02B | CSV de pedidos/entregas; normalização UTC; vínculo evento/entrega/input; duplicata vs conflito; inválidos com motivo recuperável; inicial e reexecução reconciliadas | Código 44fcbff; aceite registrado em 6e10e91; doc 19; 79 testes, 6,86 s, saída 0 |
| R07 / P03 | Checkpoint e página atômicos; rollback; retomada consistente; snapshot alterado recusado; retry limitado; rejeição recuperada; evento atrasado sem regredir conclusão | Código 702ede1; evidência d0cba49; doc 20; VAL-F3-P03-001 recebido com P04; 98 testes, 14,05 s, saída 0 |

Os totais de testes são suítes acumuladas com escopos diferentes; não somar
34+65+79+98 como testes distintos. A regressão final cobre o recorte F3, não
comprova todos os requisitos R01–R17, CI/E2E ou fechamento de fases posteriores.
R15 tem controles locais exercitados, sem alegar atendimento completo transversal.

## Grãos, contagens e preservação

| Escopo | Pedidos | Entregas | Eventos de domínio | Interpretação |
|---|---:|---:|---:|---|
| Fixture original após P02B | 8 | 8 | 13 | IDs originais; duas ambiguidades de conclusão e um conflito de identidade registrados |
| Sentinelas anteriores | 1 | 1 | 1 | Fonte __p02d_preservation__, entrega P02D-SENTINEL; não são a fixture de negócio |
| Global antes da recuperação P03 | 9 | 9 | 14 | Fixture + sentinelas |
| Acréscimo legítimo P03 | 1 | 1 | 2 | Referência ENT-UNKNOWN, evento recuperado e P03-LATE-TRANSIT em ENT-008 |
| Global após recuperação e reexecução | 10 | 10 | 16 | Mesmo total nas duas medições; histórico pode crescer sem duplicar domínio |

API: 13 registros capturados não são garantia genérica de 13 eventos novos.
A carga P02B processa 18 entradas: os 13 da captura mais cinco entradas
suplementares versionadas. O caso de referência desconhecida é a 19ª entrada,
fora da fixture original; o evento atrasado adicional é outro caso P03.

| Execução de negócio | Aceitos novos | Duplicados | Conflitos de identidade | Rejeitados | Total |
|---|---:|---:|---:|---:|---:|
| P02B inicial | 13 | 1 | 1 | 3 | 18 |
| P02B reexecução | 0 | 14 | 1 | 3 | 18 |
| P02B com referência desconhecida antes da recuperação | 0 | 14 | 1 | 4 | 19 |
| Recarga dos 18 em P03 | 0 | 14 | 1 | 3 | 18 |
| Caso de 19 entradas reexecutado após recuperação | 0 | 15 | 1 | 3 | 19 |

São estados PARTIAL por problemas previstos de dados. Os três casos de conflito
persistidos são EVENT_IDENTITY=1 e COMPLETION_AMBIGUITY=2; o conflito na tabela
acima é classificação por entrada, e não a soma desses casos persistidos.
Na recuperação explícita, referência e evento antes rejeitado são aceitos;
a tentativa original continua REJECTED e a nova tentativa é vinculada a ela.
O input e seu received_at são preservados, sem inventar novo receipt.

Captura aceita P02A: capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c.
Assinatura dos inputs dessa captura e sentinelas preservada no verificador:
`153cbf78785fdefe83848db9426a195083bdde8eae8a13a51f957ca49bf7aad0`.
Capturas/reexecuções adicionais têm seus próprios runs/inputs: não somar seus
registros à contagem de entidades de negócio e não apagar evidências para repetir.

## Configuração necessária e comandos conferidos no código

Na raiz do projeto Windows, ativar a venv existente. Não reinstalar pacotes em P04.

```powershell
Set-Location 'C:\Users\João\Projetos\integrated-logistics-control'
.\.venv\Scripts\Activate.ps1
python -m alembic -x database=ilc_f2p02b_test current
```

`.env` local e ignorado pelo Git: DB_HOST=127.0.0.1, DB_PORT=55432,
DB_NAME=ilc, DB_USER=ilc_app, DB_PASSWORD preenchido somente localmente,
DB_CONNECT_TIMEOUT=5; LOG_LEVEL=INFO. `test_engine` valida esses valores e
substitui o banco pelo argumento explícito ilc_f2p02b_test. Não alterar DB_NAME,
não imprimir URL/credenciais e não apontar cargas/migrações para ilc.

Os comandos de escrita a seguir são runbook de comportamentos já demonstrados;
**não executá-los de novo em P04**. A prática deste cartão é somente leitura.

### API / OpenAPI / captura / carga

Terminal 1: `python -m mock_api`. Terminal 2, venv ativa:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/events?limit=5' | ConvertTo-Json -Depth 8
Invoke-RestMethod 'http://127.0.0.1:8000/openapi.json' | ConvertTo-Json -Depth 20
python -m scripts.api_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --limit 5 --timeout 2
python -m scripts.business_load --database ilc_f2p02b_test --capture-run capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c
```

A carga usa o capture-run informado, não o run novo emitido pela linha anterior.
Para transformar uma captura nova, substituir conscientemente o argumento pelo
run_id SUCCEEDED retornado. A CLI P02A preserva entrada, mas não tem retomada.
O snapshot do endpoint é fixado na partida; dataset_id identifica os bytes.
Ordenação (source_system,event_id,posição original) não é a ordem de aceitação
de negócio. O consumidor segue next_cursor até null/has_more=false.

### Interrupção / rollback / retomada

```powershell
$raw = python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --stop-after-pages 1
$interruptExit = $LASTEXITCODE
$stopped = $raw | ConvertFrom-Json
if ($interruptExit -ne 1 -or $stopped.error_category -ne 'SIMULATED_INTERRUPT_AFTER_COMMIT') { throw 'Interrupcao inesperada.' }
python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --resume-run $stopped.capture_run_id --fail-before-commit-page 2
Write-Output "rollback_exit=$LASTEXITCODE"
python -m scripts.reliable_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --resume-run $stopped.capture_run_id
Write-Output "resume_exit=$LASTEXITCODE"
```

Esperado: interrupção PARTIAL/1 página/5 registros; rollback pré-commit mantém
1/5; retomada SUCCEEDED/3/13. A sondagem do snapshot é uma requisição extra,
sem criar página de captura. Captura completa retomada faz zero requisições.
Encerrar servidor manual com Ctrl+C; verificadores encerram somente seus filhos.

### Códigos de saída e verificadores

| CLI | Saída e significado |
|---|---|
| api_capture | 0 SUCCEEDED; 1 FAILED, mesmo havendo páginas anteriores confirmadas |
| reliable_capture | 0 SUCCEEDED; 1 PARTIAL/FAILED ou erro de configuração |
| business_load | 0 SUCCEEDED; 2 PARTIAL/DATA_QUALITY_ISSUES; 1 FAILED |
| check_api_failures / check_api_capture / check_business_load / check_reliability | 0 PASS da verificação; 1 FAIL da verificação |
| pytest / Ruff | 0 aprovado; não zero exige investigar; não interpretar todo não zero como a mesma categoria |

Comandos dos verificadores já executados (escrevem runs quando envolvem banco;
não repetir em P04):

```powershell
python -m scripts.check_api_failures
python -m scripts.check_api_capture --database ilc_f2p02b_test
python -m scripts.check_business_load --database ilc_f2p02b_test --capture-run capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c
python -m scripts.check_reliability --database ilc_f2p02b_test --original-capture capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c
```

Erros de uso do argparse (argumento ausente/inválido) também podem sair com código 2,
antes de executar a operação. Distinguir pela mensagem de uso e ausência de relatório,
especialmente do código 2 com relatório PARTIAL na carga.

PASS atesta o resultado esperado, inclusive erro deliberado; não converte
runs FAILED/PARTIAL em SUCCEEDED. Política de retry: até três tentativas,
backoff 0,1 e 0,2 s, apenas HTTP 408/429/500/502/503/504 e
ConnectError/ConnectTimeout/ReadTimeout. JSON, contrato e rejeição de negócio
não recebem retry automático. Não há retry ilimitado nem retomada com snapshot novo.

## Prática P04 — consultar evidência existente, sem escrita

Após sincronizar o commit documental, executar este bloco no PowerShell:

```powershell
@'
import json
from sqlalchemy import text
from scripts.migration_config import test_engine

engine = test_engine("ilc_f2p02b_test")
run_id = "capture-p03-02e5146c-2341-4cd9-846a-49922afd3f2a"
try:
    with engine.begin() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        identity = connection.execute(text(
            "SELECT current_database(),current_user,inet_server_addr()::text,inet_server_port()"
        )).one()
        revision = connection.execute(text(
            "SELECT version_num FROM public.alembic_version"
        )).scalar_one()
        state = connection.execute(text("""
            SELECT r.run_id,r.status,r.error_category,c.last_page,c.records,
                   c.complete,c.next_cursor,c.dataset_id,c.api_total,
                   (SELECT count(*) FROM ilc.capture_pages p WHERE p.run_id=r.run_id) AS stored_pages,
                   (SELECT count(*) FROM ilc.capture_items i
                    JOIN ilc.capture_pages p USING(page_key) WHERE p.run_id=r.run_id) AS stored_items
            FROM ilc.runs r JOIN ilc.capture_checkpoints c ON c.capture_run_id=r.run_id
            WHERE r.run_id=:run
        """), {"run": run_id}).mappings().one()
        history = connection.execute(text("""
            SELECT page_number,records,complete,invocation_run_id
            FROM ilc.capture_checkpoint_history
            WHERE capture_run_id=:run ORDER BY page_number
        """), {"run": run_id}).mappings().all()
        print("CONEXAO:", tuple(identity))
        print("REVISAO:", revision)
        print("EXECUCAO_CHECKPOINT:", json.dumps(dict(state), default=str))
        print("HISTORICO:", json.dumps([dict(row) for row in history], default=str))
finally:
    engine.dispose()
'@ | python -
Write-Output "query_exit=$LASTEXITCODE"
```

Esperado: banco/usuário/porta ilc_f2p02b_test/ilc_app/55432; revisão 0006;
SUCCEEDED; last_page=3, records=13, complete=true, next_cursor=null;
stored_pages=3 e stored_items=13; histórico de três páginas com records 5/10/13.
O histórico demonstra confirmação na mesma transação; não afirmar que gravar
um log HTTP isolado confirma uma página. João executou em P04 a consulta reduzida de run/checkpoint: SUCCEEDED, 3/13, complete=True e next_cursor=None. As colunas stored_pages/stored_items e histórico não foram impressas nessa consulta adicional; sua reconciliação já foi comprovada no verificador P03 aprovado.

### Consulta das rejeições — SQL somente leitura

Executar em sessão SQL conectada ao mesmo banco, sem colar SQL diretamente
no PowerShell. Para usar Python, colocar a consulta em text(...) e executar
na conexão read-only do bloco anterior. Substituir o filtro por run_id observado
para investigar outra execução.

```sql
SELECT a.run_id,i.input_key,i.declared_id,p.outcome,p.reason,
       i.original_reference,p.normalized_payload,
       convert_from(s.original_bytes,'UTF8') AS supplement_json,
       convert_from(cp.response_body,'UTF8')::jsonb -> 'items' -> ci.item_index AS captured_json
FROM ilc.event_processing_results p
JOIN ilc.attempts a USING(attempt_id,input_key)
JOIN ilc.inputs i USING(input_key)
LEFT JOIN ilc.supplement_payloads s USING(input_key)
LEFT JOIN ilc.capture_items ci USING(input_key)
LEFT JOIN ilc.capture_pages cp USING(page_key)
WHERE a.run_id='business-2ae56df8-d97f-4931-abdb-0dd8b1555960'
  AND p.outcome='REJECTED'
ORDER BY i.declared_id;
```

Esperado nesse run histórico: quatro rejeições (dois INVALID_EVENT_CONTRACT,
um MISSING_REQUIRED_FIELD, um INVALID_REFERENCE). Reprocessamento posterior
não altera esse histórico. Conteúdo recuperável via supplement_json ou captured_json;
normalized_payload pode ser nulo quando a validação falha.

```sql
SELECT l.previous_attempt_id,old.outcome AS previous_outcome,
       l.new_attempt_id,new.outcome AS new_outcome,l.reason
FROM ilc.reprocessing_links l
JOIN ilc.attempts old ON old.attempt_id=l.previous_attempt_id
JOIN ilc.attempts new ON new.attempt_id=l.new_attempt_id
WHERE l.previous_attempt_id='8e22fc1a-3e32-49c1-ada9-8cca7376185b';
```

Esperado: tentativa antiga REJECTED e novas ACCEPTED/DUPLICATE; regressão pode
ter acrescentado novas tentativas legítimas, portanto não fixar duas linhas globais.
Estas consultas foram conferidas contra o esquema/código; a consulta read-only
P04 de run/checkpoint foi executada por João, sem repetir carga ou testes. As
consultas adicionais de rejeições acima não foram repetidas em P04.

### Conferência de Git e comandos por João

```powershell
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'Fetch falhou.' }
git merge --ff-only origin/feat/f3-p03-reliability
if ($LASTEXITCODE -ne 0) { throw 'Preservar alteracoes e investigar sincronizacao.' }
git status --short --branch
git branch --show-current
git log -2 --oneline
git rev-list --left-right --count HEAD...origin/feat/f3-p03-reliability
git diff --check
```

Esperado: branch feat/f3-p03-reliability, HEAD igual ao remoto (0 0), sem
alterações rastreadas pendentes; `.vscode/` não rastreado permanece preservado.
João demonstrou Git/SQL e delegou expressamente ao assistente a checagem dos
comandos restantes. A conferência técnica abaixo atende a essa instrução humana;
não representa conferência autoral ou explicação independente de João.

## Evidência final reutilizada, autoria e esforço

Verificador P03: verification=PASS, verification_exit=0, http_children_stopped=true.
Captura da prova: capture-p03-02e5146c-2341-4cd9-846a-49922afd3f2a.
Rollback permaneceu 1/5; retomada 3/13; 503 com três corpos preservados;
timeout com três ReadTimeout; JSON inválido com uma requisição; mudança de
snapshot bloqueada. Recuperação aceitou referência/evento antes rejeitado;
evento atrasado 14h não alterou conclusão 17h/DELIVERED. IDs e esperado × observado
completos no [documento 20](20-f3-p03-reliability.md).

Última regressão Windows: **98 passed, 1 warning in 14.05s**, nenhum skip,
regression_exit=0; Ruff aprovado; diff check sem erro. Ensaios anteriores e sua
falha ConnectTimeout corrigida ficam preservados nos registros históricos.
P04 não repete testes por não alterar comportamento técnico.

| Participante | Contribuição observada |
|---|---|
| João / P01 | Implementou paginação e ligação do endpoint; iniciou API e percorreu páginas/falhas |
| João / P02A | Ligou persistência à transação e executou captura/consultas PostgreSQL |
| João / P02B | Implementou normalização UTC central e executou carga/reexecução/consultas |
| João / P03 | Ligou página e checkpoint à mesma transação; provocou interrupção e executou retomada, verificador e regressão |
| Assistente | Estrutura, clientes, testes, fixtures adicionais, comandos, revisão e registros de evidência |
| João / P04 | Consulta read-only de execução/checkpoint e Git concluídas; delegou a checagem documental restante ao assistente |
| Assistente / P04 | Comandos, configuração, saídas e SQL conferidos contra o código/esquema, conforme delegação humana |

Aprendizagem prática evidenciada pelas contribuições acima; explicação independente
não demonstrada e explicitamente adiada. Esforço humano da F3/P04 **não medido**;
não converter duração de testes em horas de trabalho. Tempo disponível medido é
somente o das execuções informadas (4,19 s/5,96 s/6,86 s/14,05 s em seus escopos).
A estimativa antiga de 20–25h e o alvo 21/10 não constituem esforço ou prazo comprovados.
Apresentação solicitada para 03/11 às 14h não amplia escopo nem autoriza fechar F3.

## Limitações e decisão pendente

- Case sintético/local; nenhum benefício ou integração empresarial real alegado.
- Interrupção controlada antes/depois do commit, sem desligamento abrupto do SO.
  Invocação abandonada pode permanecer RUNNING; reconciliação administrativa não demonstrada.
- Retomada exige snapshot idêntico; não recupera captura P02A antiga sem checkpoint.
- Retry com orçamento fixo; sem deadline global contra servidor que envia bytes indefinidamente.
- Recuperação explícita de uma referência legítima, sem reparo automático de toda a quarentena.
- Histórico de atraso preservado sem regredir conclusão; ensaios não cobrem todo cenário possível.
- Aviso HTTPX/TestClient mantido como manutenção; nenhuma dependência alterada para suprimi-lo.
- Lock existe, mas concorrência real de duas sessões não foi ensaiada.
- Instalação limpa, CI/E2E, backup/restauração e operação de produção não comprovados.
- Aprovação documental/IA/métricas/interface pertencem a fases posteriores e não foram iniciadas.

Feito: R05–R07 consolidados com commits, evidências e comandos; VAL-F3-P03-001
registrado; README/plano atualizados; histórico e sentinelas preservados.
Pendência: decisão central, incluindo tratamento da
explicação independente pendente antes de eventual fechamento. Sem bloquear ou
liberar fechamento por conta própria: essa decisão cabe ao gerente.

Próximo passo único: levar esta passagem ao chat 00 para decidir fechamento/ajustes.
Não há nova confirmação documental solicitada a João.
Não realizar merge, consolidar fases posteriores nem iniciar F4.

## Conferência P04 observada — 02/11/2026

João sincronizou d0cba49 → ee59574 por fast-forward, somente oito arquivos
Markdown. Branch feat/f3-p03-reliability com HEAD e origin em ee59574;
`git rev-list --left-right --count HEAD...origin/feat/f3-p03-reliability`
retornou **0 0**. `git diff --check` não imprimiu erro; única entrada de
status foi .vscode/ não rastreado, preservado. Alembic: **0006_reliability (head)**.

Na mesma venv, João consultou PostgreSQL com **SET TRANSACTION READ ONLY**.
Conexão observada: **('ilc_f2p02b_test', 'ilc_app', 55432)**.
Run consultado: **capture-p03-02e5146c-2341-4cd9-846a-49922afd3f2a**.
Resultado: **status SUCCEEDED, error_category None, last_page 3, records 13,
complete True, next_cursor None; query_exit=0**. Esperado e observado coincidiram.

A consulta adicional não imprimiu dataset_id, api_total, contagens auxiliares ou
histórico de checkpoints; não atribuir essas saídas a esta consulta. Sua prova
permanece no verificador HTTP/SQL P03 aceito. Não houve nova captura, carga,
migração ou repetição de testes no cartão P04; somente consulta da revisão atual.

Registro final desta rodada é documental, posterior a ee59574; não modifica o
código testado em 702ede1. A conferência dos demais comandos, que estava pendente
nesta rodada, foi posteriormente delegada por João e concluída pelo assistente,
como registrado abaixo. F3 continua ABERTA; F4 não iniciada.

## Checagem final delegada e submissão ao gerente

João instruiu explicitamente neste chat: **“faça este check por mim”**, por
restrição de tempo. Essa instrução substitui a solicitação de confirmação
documental autoral restante; não altera as evidências de prática já executadas
nem a pendência de explicação independente. A conferência a seguir foi feita
pelo assistente e não foi atribuída a João.

| Item conferido | Fonte técnica e resultado |
|---|---|
| 13 linhas de comandos em sete CLIs, incluindo repetições entre README e passagem | Argumentos comparados com add_argument nas CLIs de captura, carga, recuperação e quatro verificadores; nenhum parâmetro inexistente |
| API/OpenAPI/paginação | Launcher mock_api/__main__.py fixa 127.0.0.1:8000; app define /events, limite 1–100, cursor e término null/false; OpenAPI padrão /openapi.json |
| Banco/configuração | scripts/migration_config.py exige banco explícito ilc_f2p02b_test, host 127.0.0.1, porta 55432, usuário ilc_app e DB_NAME=ilc no arquivo; conferido contra o runbook |
| Interrupção e retomada | Argumentos --stop-after-pages, --fail-before-commit-page e --resume-run existem; CLI sai0 para SUCCEEDED e 1 para PARTIAL/FAILED |
| Captura e carga | api_capture sai0/1; business_load sai0/2/1 por SUCCEEDED/PARTIAL/FAILED; o exemplo de carga identifica explicitamente a captura aceita, não a captura nova da linha anterior |
| Consulta de execução/checkpoint e rejeições | Nomes, tipos e joins conferidos nas migrações 0001/0004/0005/0006; resultados históricos e campos recuperáveis coerentes com os registros aprovados |
| Detalhe corrigido no runbook | Erro de uso argparse pode sair 2 antes da operação; código 2 não deve ser classificado como PARTIAL sem o relatório correspondente |
| Evidências reutilizadas | Regressão 98 aprovada e consulta read-only/Git de João; nenhuma nova execução de testes, carga ou consulta PostgreSQL pelo assistente |

Não foi identificado parâmetro de comando inexistente ou divergência de alvo
de banco. A checagem SQL é estática contra esquema/código; não se apresenta como
nova execução PostgreSQL. A evidência executada continua sendo a de João e
dos verificadores aceitos, sem inventar a saída de consultas não repetidas.

Entrega P04: README/plano/passagem e registro VAL-F3-P03-001 publicados;
R05–R07 rastreáveis; contagens por fixture/sentinelas/recuperação separadas;
prática, autoria, limitações e esforço não medido registrados. Escopo somente
documental; código técnico 702ede1 preservado, sem merge, F4 não iniciada.

**Solicitação ao gerente:** avaliar P04 e decidir fechamento da F3 ou ajustes,
tratando explicitamente a explicação independente adiada. O executor não
declarou F3 FECHADA. Não foi enviada mensagem automática a outro chat.
