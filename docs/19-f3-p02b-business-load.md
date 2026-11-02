# F3-P02B - Transformacao e entidades de negocio

02/11/2026. Base tecnica 2b4b72a; aceite P02A registrado em 60cc75f.
Branch: feat/f3-p02b-business-load. Preparacao, nao aceite ou carga comprovada.
Captura selecionada por Joao no diagnostico: capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c.
Banco ilc_f2p02b_test, ilc_app; revisao inicial 0004_api_capture.
Unico dominio preexistente informado: sentinela P02D, fonte __p02d_preservation__.
Nao ha colisao com ORD-ENT-001..008 e ENT-001..008.

## Fontes e adaptacao CSV

Nao existem CSVs na base versionada ou no inventario local recebido.
Criados CSVs pequenos em tests/fixtures/reference_csv/v1 a partir dos JSONL
imutaveis da F2, sem modificar o manifesto original: oito pedidos e oito entregas.
adapter.json registra versao, caminhos/hashes dos JSONL, hashes CSV e contagens.
Conversao deterministica: ordem de linhas/propriedades do JSONL, cabecalho
pelas chaves da primeira linha, CSV UTF8 com newline LF, csv.DictWriter,
null -> vazio, request_data -> JSON com chaves ordenadas e separadores compactos.
.gitattributes fixa LF para novas fixtures, inclusive Windows.
Bytes CSV e proveniencia sao gravados em reference_imports por execucao.
Cada linha recebe resultado, valores entrantes, valores anteriores se houver
colisao e chave da entidade. Duplicatas nao atualizam entidades; conteudo
diferente e CONFLICT, nunca UPDATE silencioso. Erro SQL aborta a carga.

## Lacuna e migracao aditiva 0005

Os inputs de P02A sao imutaveis e possuem sentinela historica de normalizacao
nao executada. Nao podem ser atualizados para conter outro hash normalizado.
Nao existe armazenamento para arquivo CSV/referencia (input_type so EVENT/DOCUMENT).
Nova revisao 0005_business_processing cria:

- reference_imports: arquivo CSV integral, origem, hashes CSV/JSONL, horario/run.
- reference_results: classificacao e dados por linha, sem adulterar order/delivery.
- supplement_payloads: bytes e localizacao das entradas auxiliares da fixture.
- event_processing_results: resultado derivado imutavel por tentativa, hash/payload
  normalizado, motivo e vinculos com evento/conflito. FK composta com attempts/input.

Nao altera inputs, capture_pages, migracoes anteriores ou dados de P02A.
Triggers de imutabilidade nas quatro tabelas novas. Downgrade apaga essas
novas evidencias; NAO executar depois da carga sem mandato especifico.
Cliente de captura recebe somente compatibilidade de revisao: permite 0004 e
0005, pois suas tabelas nao mudaram. Dependencias/lock inalterados.

## Normalizacao e processamento

Event do contrato 06: rejeita campos desconhecidos, IDs vazios/espacos externos,
tipo invalido, horario sem fuso e obrigatorios ausentes. UTC com seis casas
fracionarias, notes ausente/null equivalentes, JSON ordenado e SHA256 do conteudo.
Versao event-business-v1. Entrada original nunca e sobrescrita.

Eventos normais sao lidos EXCLUSIVAMENTE das paginas da captura escolhida,
validando seus hashes, vinculos e correspondencia integral com a fixture.
A ordem de aceitacao de negocio e explicitamente a ordem da arrival_plan da F2
para os 13 eventos validos. Nao e a ordem lexical da API nem uma alegacao de
chegada real: os received_at reais de P02A permanecem intocados.
Isso preserva C_AB com A primeiro e C_BA com B primeiro, conforme contrato.
Somente depois entram arquivos auxiliares replay, conflito de identidade e
invalidos. Novos recebimentos de arquivos possuem horario real de importacao,
sem inventar os received_at sinteticos da arrival_plan.

Reprocessamento dos inputs capturados gera tentativa interna com receipt_key
null, sem nova chegada externa. Arquivos auxiliares importados de novo possuem
novos inputs/receipts de captura; isso nao duplica entidades de negocio.
Consolidacao das entradas fisicas equivalentes em uma entrada logica unica
nao e declarada concluida: resultados apontam explicitamente para evento original.

Mesma identidade e hash normalizado: DUPLICATE. Conteudo diferente: CONFLICT,
original preservado e alternativa recuperavel, usando conflicts/conflict_evidence.
Reenvio da mesma alternativa reutiliza o caso, sem duplicar conflito ou modificar
evidencia selada. Payload alternativo nao vira segundo evento aceito com mesmo ID.
Referencia desconhecida: REJECTED / INVALID_REFERENCE, normalizado preservado e
bytes recuperaveis; nenhuma entrega ficticia. Estruturalmente invalido:
REJECTED / MISSING_REQUIRED_FIELD ou INVALID_EVENT_CONTRACT.

Dois DELIVERED com IDs distintos continuam sendo dois eventos aceitos.
A primeira aceitacao persistida gera decisao PROVISIONAL. Outra conclusao em
horario diferente abre COMPLETION_AMBIGUITY com duas evidencias; nao troca a
decisao. Nenhuma aprovacao documental, metrica ou resolucao automatica.
Eventos atrasados permanecem no historico; ensaios completos ficam no cartao
seguinte. Nao alegar conclusao de toda confiabilidade ou independencia de ordem.

Carga de negocio inteira em uma transacao, com lock transacional deste loader
(lock_timeout 5s). Erro de infraestrutura: rollback e run FAILED registrado.
Rejeicoes/conflitos de dados sao classificados sem descartar registros: run PARTIAL,
CLI exit=2, nao SUCCEEDED. Verificador pode retornar PASS por observar precisamente
o PARTIAL esperado; isso nao converte dados conflitantes em sucesso de negocio.
Sem retry, checkpoint ou retomada; concorrencia externa completa nao demonstrada.

## Esperado antes da execucao Windows

| Execucao | Pedidos/entregas | Eventos inseridos | Duplicatas | Conflitos identidade | Rejeitados |
|---|---|---:|---:|---:|---:|
| Inicial, 18 entradas originais | 8/8 inseridos | 13 | 1 | 1 | 3 |
| Reexecucao das mesmas 18 | 8/8 duplicados | 0 | 14 | 1 | 3 |
| Caso adicional de referencia desconhecida, 19 | 8/8 duplicados | 0 | 14 | 1 | 4 |

Casos de conflito: um EVENT_IDENTITY e dois COMPLETION_AMBIGUITY. Os dois
ultimos nao sao subtraidos dos 13 eventos aceitos. Globais, incluindo sentinela:
9 pedidos, 9 entregas, 14 eventos. Escopo sintetico: 8/8/13.
Caso adicional tests/fixtures/business_cases/unresolved_event.jsonl e novo,
explicitamente separado da fixture original; ENT-UNKNOWN nunca deve ser criado.

O verificador detecta estado inicial ja carregado (8/8/13); nesse caso informa
primeira carga observada como reexecucao, sem fabricar 13 insercoes novas.
Se encontrar estado parcial inesperado, para sem apagar nada.
Assinatura dos inputs da captura e da sentinela antes/depois deve ser identica.

## Pratica central e comandos

Joao implementa utc_text em scripts/business_load.py, trocando o raise pendente
pela conversao value.astimezone(UTC), serializacao ISO com microseconds e Z.
Essa transformacao participa do hash e da comparacao de identidade.
Enquanto nao preenchida, os testes falham e a carga nao deve ser executada.

Na venv, banco explicitamente selecionado:

    python -m ruff format scripts/business_load.py
    python -m ruff check scripts/business_load.py scripts/check_business_load.py scripts/api_capture.py migrations/versions/0005_business_processing.py tests/unit/test_business_load.py tests/business
    python -m pytest tests/unit/test_business_load.py -q
    python -m alembic -x database=ilc_f2p02b_test upgrade 0005_business_processing
    python -m scripts.check_business_load --database ilc_f2p02b_test --capture-run capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c

O verificador executa as tres cargas e SELECTs, preservando seus runs.
Nao cria servidor: le somente a captura ja persistida, como determinado pelo cartao.
CLI unitario: python -m scripts.business_load --database ilc_f2p02b_test --capture-run RUN
Opcao --include-unresolved-case acrescenta a entrada adicional ao run.

Depois da evidencia inicial, habilitar teste PostgreSQL adicional:

    $env:ILC_BUSINESS_TEST_DATABASE = 'ilc_f2p02b_test'
    $env:ILC_BUSINESS_CAPTURE_RUN = 'capture-e0e5e158-49f3-4b8f-ba05-3397db8c7e3c'
    python -m pytest tests/business/test_business_load_postgres.py -q -s
    Remove-Item Env:ILC_BUSINESS_TEST_DATABASE,Env:ILC_BUSINESS_CAPTURE_RUN

SQL para Joao consultar:

    SELECT source_system,count(*) FROM ilc.orders GROUP BY source_system;
    SELECT source_system,count(*) FROM ilc.events GROUP BY source_system;
    SELECT a.run_id,p.outcome,p.reason,count(*)
    FROM ilc.event_processing_results p JOIN ilc.attempts a USING(attempt_id,input_key)
    GROUP BY a.run_id,p.outcome,p.reason ORDER BY a.run_id,p.outcome;
    SELECT conflict_type,count(*) FROM ilc.conflicts GROUP BY conflict_type;
    SELECT p.input_key,p.reason,p.normalized_payload,s.original_bytes
    FROM ilc.event_processing_results p LEFT JOIN ilc.supplement_payloads s USING(input_key)
    WHERE p.outcome='REJECTED';

## Verificacoes do assistente e passagem

Linux/Python3.12, sem PostgreSQL disponivel: com implementacao TEMPORARIA de
referencia de utc_text, 13 testes unitarios novos passaram; regressao de API,
falhas e captura mais negocio: 76 passed e um teste PostgreSQL pulado.
Isso NAO comprova migracao ou carga PostgreSQL. A linha de referencia foi retirada
para implementacao de Joao; os testes finais do pacote dependem dessa edicao.
Ruff check/format do codigo preparado passou. Nenhuma dependencia nova.

P02A aceito; P02B em implementacao. Pendentes: transformacao de Joao, migracao
0005 observada, carga inicial/reexecucao, conflito/rejeicoes/SQL e commit autoral,
evidencias publicadas e aceite central. Explicacao independente para revisao final.
Nenhuma fase posterior, aprovacao documental, metrica ou interface iniciada.
