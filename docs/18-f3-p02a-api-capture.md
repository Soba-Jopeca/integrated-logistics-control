# F3-P02A - Captura API com entrada preservada no PostgreSQL

> Estado consolidado em 02/11/2026: este cartão está aceito no escopo demonstrado,
> conforme o mandato humano F3-P04. Estados de preparação/submissão e instruções
> de edição provisória abaixo são históricos, não instruções para desfazer o código.
> A F3 permanece ABERTA. Ver [consolidação 21](21-f3-p04-consolidation.md)
> para comandos, dependências, pendências e limites atuais.


Data: 02/11/2026. Base: 48276192d078d8f07503cfcf0135c871287e2535.
Branch proposta: feat/f3-p02a-api-capture. P01 aceito como entrada pelo cartao
humano P02A. Explicacao independente adiada para revisao final por Joao.
Estado: estrutura preparada; ligacao central e verificacao PostgreSQL pendentes.
Nao declarar 13 registros persistidos antes da evidencia local.

## Lacuna concreta e decisao de armazenamento

Joao confirmou catalogo em ilc_f2p02b_test, ilc_app, 127.0.0.1:55432,
revisao 0003_decisions_conflicts. inputs possui referencia/checksum, sem corpo.
runs tem estado/horarios/erro, sem paginas ou contagens. Nenhuma tabela existente
armazena a resposta HTTP de captura; nao reutilizar orders.request_data para isso.

Migracao ADITIVA 0004_api_capture apos 0003: capture_pages guarda corpo bytea,
status HTTP, URL/cursor, origem, recebimento UTC, SHA256, snapshot, numero,
resultado e contagem da pagina; capture_items liga posicao original a input_key.
Ambas possuem triggers de imutabilidade. Foreign keys para runs/sources/inputs.
Sem alteracao das 19 tabelas anteriores ou de revisoes historicas.
Downgrade remove apenas as duas tabelas novas; DESTRUTIVO para evidencias de
captura ja gravadas, portanto nao executar depois da captura sem mandato.

Reutiliza sources, runs, inputs, receipts e attempts. Cada entrada aponta para
pg:ilc.capture_pages/PAGE_UUID; capture_items.item_index identifica items[N].
original_sha256 e o checksum dos bytes integrais da pagina referenciada,
NAO o hash de um item reserializado. Varias entradas da mesma pagina compartilham
referencia, checksum e received_at. O corpo completo permite recuperar todos
os campos e a posicao original, sem perder propriedades nao utilizadas.
API consultada solicita Accept-Encoding: identity e preserva iter_raw().

Inputs permanecem SEM normalizacao de negocio: normalized_sha256 e
normalizer_version null. Por exigencia de ck_inputs_normalization existente,
normalization_error recebe sentinela NOT_NORMALIZED_CAPTURE_ONLY_P02A.
Essa sentinela significa etapa nao solicitada, nao erro de parsing constatado.
Futura normalizacao devera respeitar a imutabilidade dos inputs; registrar
resultado derivado sem sobrescrever historico. Nao interpretar a sentinela
como qualidade de negocio nem contar automaticamente como rejeicao.
ACCEPTED em attempts significa captura aceita no stage API_CAPTURE_P02A,
nao aceitacao de evento de negocio, entrega ou aprovacao documental.

## Cliente e transacoes

GET /events, limite padrao 5 (1..100), timeout configuravel 0.1..30s,
trust_env=False, sem redirect/retry. URL literal loopback 127.0.0.1 e caminho
/events; nao aceita credenciais/query inicial. Maximo 1MiB por resposta e
10000 itens declarados. Snapshot SHA256 e total constantes, cursor sem ciclos,
termino explicito coerente. Nenhuma deduplicacao ou transformacao de entidade.
A validacao de source_system/event_id e apenas proveniencia minima para inputs.

Uma transacao confirma pagina+inputs+receipts+attempts+indices. Cursor em memoria
avanca somente apos retorno do commit. Nao existe checkpoint ou retomada.
Reexecucao cria NOVO run e novas entradas de captura: nao e prova de idempotencia
de negocio, que pertence a cartao posterior.
Run inicial RUNNING e gravado antes de pedir paginas. Final SUCCEEDED apenas
apos termino e reconciliacao; FAILED mesmo se houver paginas ja confirmadas.
Contagens finais sao consultadas do banco, nao apenas variaveis Python.
Se falhar o proprio acesso/finalizacao do banco, CLI retorna FAILED com contagens
UNKNOWN; nao afirmar rollback/commit desconhecido. RUNNING residual exige
investigacao explicita, sem promover automaticamente para sucesso.

Resposta HTTP incorreta e JSON/envelope invalidos ate o limite de tamanho
sao preservados como pagina com erro e zero entradas. Timeout/conexao sem
resposta completa nao inventam corpo ou status. Resposta acima do limite nao
e armazenada inteira; run falha como RESPONSE_TOO_LARGE. Paginas anteriores
confirmadas permanecem. SQL parametrizado; excecoes CLI sem credenciais.

## Pratica central de Joao

Preservar .vscode, .env e alteracoes locais. Na nova branch, scripts/api_capture.py,
funcao commit_page: substituir somente raise CaptureError("JOAO_LINK_NOT_IMPLEMENTED")
por bloco engine.begin() que chama write_page(connection, **page) e retorna
seu resultado. Essa e a ligacao entre a pagina lida e a persistencia transacional.
Enquanto nao preenchida, captura retorna FAILED explicitamente; nao ha sucesso ficticio.

## Comandos locais e evidencia requerida

Na raiz e venv, APENAS banco ilc_f2p02b_test explicitamente selecionado:

    python -m alembic -x database=ilc_f2p02b_test upgrade 0004_api_capture
    python -m alembic -x database=ilc_f2p02b_test current
    python -m ruff check scripts/api_capture.py scripts/check_api_capture.py migrations/versions/0004_api_capture.py tests/unit/test_api_capture.py tests/capture
    python -m pytest tests/unit/test_events_api.py tests/unit/test_api_failures.py tests/unit/test_api_capture.py -q

PowerShell, habilitacao explicita somente para testes de captura:

    $env:ILC_CAPTURE_TEST_DATABASE = 'ilc_f2p02b_test'
    python -m pytest tests/capture/test_api_capture_postgres.py -q -s
    Remove-Item Env:ILC_CAPTURE_TEST_DATABASE
    python -m scripts.check_api_capture --database ilc_f2p02b_test

Esse verificador cria servidor proprio em loopback/porta efemera, executa captura
normal (13, paginas 5/5/3), depois captura com HTTP503 apos a primeira pagina
(5 confirmados, segunda resposta preservada com erro). Encerra o proprio filho.
Executa SELECTs, recalcula hashes e compara TODOS os campos e ordem com fixture;
confere vinculos/recebimento/hash e estado do run. Compara contagens das tabelas
orders/deliveries/events antes/depois: devem permanecer iguais.
verification=PASS e o aceite da verificacao, nao sucesso do run HTTP503.
Persistem os dois runs de evidencia, sem limpeza de historico.

CLI normal (requer servidor manual python -m mock_api em outro terminal):

    python -m scripts.api_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --limit 5 --timeout 2

Falha HTTP controlada, sem alterar endpoint normal:

    python -m scripts.api_capture --database ilc_f2p02b_test --url http://127.0.0.1:8000/events --simulate-http-after-pages 1

Segundo comando retorna status FAILED, HTTP_ERROR e exit=1, preservando 5 itens;
a opcao troca a requisicao seguinte por /scenarios/http-503 somente no ensaio.
Parar servidor manual com Ctrl+C. Nao usar banco ilc ou alterar configuracao de
acesso. Nao executar os antigos probes de catalogo --expect head: eles descrevem
0003 historico e nao reconhecem 0004. Testes de outras etapas nao sao revalidados
por este recorte e nao devem ser confundidos com testes de captura.

SQL para consultar as evidencias (filtrar pelo run_id retornado):

    SELECT r.run_id,r.status,r.error_category,p.page_number,p.http_status,
           p.capture_status,p.item_count,p.response_sha256,p.received_at
    FROM ilc.runs r JOIN ilc.capture_pages p USING(run_id)
    WHERE r.stage='API_CAPTURE_P02A'
    ORDER BY r.started_at,p.page_number;

    SELECT p.run_id,p.page_number,c.item_index,i.declared_id,
           convert_from(p.response_body,'UTF8')::jsonb -> 'items' -> c.item_index AS recovered_event
    FROM ilc.capture_items c JOIN ilc.capture_pages p USING(page_key)
    JOIN ilc.inputs i USING(input_key)
    ORDER BY p.run_id,p.page_number,c.item_index;

## Evidencia disponivel antes da execucao Windows

Assistente, Linux/Python3.12, dependencias principais equivalentes ao recorte
anterior, sem alterar requirements/lock do repositorio.
63 testes sem banco passaram: 34 anteriores API/falhas + 29 captura.
Dois testes PostgreSQL pulados por ausencia de habilitacao/banco neste ambiente.
Ruff aprovado. Nenhuma migracao foi aplicada aqui; nenhuma persistencia real
PostgreSQL e declarada. Testes PostgreSQL preparados: captura normal e parcial
por HTTP real com recuperacao integral; rollback de pagina apos insercoes.
Joao deve executar ligacao, migracao e consultas para evidencia deste cartao.

## Passagem

Cartao P02A em andamento. Preparados: cliente/CLI, verificador HTTP+SQL,
migracao aditiva justificada, testes e documentacao. Pendentes: edicao central,
upgrade observado no banco de teste, testes PostgreSQL, SQL/contagens/hashes,
commit autoral e publicacao/evidencias ao gerente. Explicacao para revisao final.
Sem CSV, retry, checkpoint, retomada completa ou entidades de negocio.
P02A aguarda aceite central; nenhum proximo cartao liberado.

## Evidencia Windows recebida - 02/11/2026

Migracao observada: 0004_api_capture (head).
Joao implementou commit_page com engine.begin() e write_page.
Ruff aprovado; 65 testes passaram em 5.96s; tests_exit=0.
Aviso HTTPX/TestClient mantido como manutencao nao bloqueante.

Verificador HTTP real + consultas PostgreSQL: PASS, exit=0.
Run normal: capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c.
SUCCEEDED; 3 respostas/paginas; 13 itens declarados e 13 persistidos.
Todos os campos e ordem reconciliados com a fixture; hashes e vinculos conferidos.

Run com falha: capture-893c9641-87a5-4254-9af1-f09de9f97d7d.
FAILED, HTTP_ERROR; 2 respostas, 1 pagina capturada, 5 registros confirmados.
Corpo HTTP503 preservado: {"scenario":"http_503","error":"SIMULATED_UNAVAILABLE"}.

Testes PostgreSQL tambem passaram, incluindo rollback de pagina.
Contagens de orders/deliveries/events: (1,1,1) antes e depois.
PID filho 18852 encerrado; child_stopped=true.

Explicacao independente permanece adiada para revisao final.
P02A submetido para aceite central; nenhum proximo cartao liberado.


## Aceite central recebido com o cartao F3-P02B - 02/11/2026

P02A ACEITO no escopo de captura e rastreabilidade demonstrado em 2b4b72a.
Autoridade: cartao humano F3-P02B encaminhado neste chat, que determina
atualizar este registro com o aceite. Nao foi fornecido ID separado de
validacao; nenhum foi inventado. Registros anteriores de submissao sao historicos.

F3-P02B liberado para transformacao/carga de pedidos, entregas e eventos,
identidade, duplicatas, conflitos e rejeicoes com reconciliacao. Base tecnica
2b4b72a; capturas existentes devem ser preservadas. Explicacao independente
permanece adiada para revisao final. Sem liberacao de outros cartoes ou fases.
