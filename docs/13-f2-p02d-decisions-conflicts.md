# F2-P02D - Decisoes de conclusao e conflitos

Data: 19/10/2026. Branch: feat/f2-p02d-decisions-conflicts.
Entrada autorizada: 4959edfc5df5cf5c25381a3766e5f4cdbe167c1b.
Referencias: contratos 06 e modelo 07 nessa entrada.
Estado: preparacao publicada com restricao central bloqueada para edicao
de Joao. Nenhuma execucao de 0003 ou teste novo comprovada nesta preparacao.
F2 aberta, R03 parcial, F3-F6 bloqueadas. Validacao central ao final.

## 1. Entrada observada no Windows de Joao

Branch criada a partir de 4959edf; apenas .vscode nao rastreada.
Conexao SQLAlchemy/psycopg: PASS, ilc_app/ilc, PostgreSQL 18.6,
127.0.0.1:55432, UTC, cinco privilegios administrativos false,
rolconnlimit=5. Banco descartavel ilc_f2p02b_test na revisao
0002_documents, quinze tabelas e btree_gist 1.8: PASS.
Sentinela anterior __p02c_preservation__ preservada: PASS.

## 2. Estrutura preparada

Revisao 0003_decisions_conflicts, down_revision=0002_documents.
Nenhum arquivo Python ou SQL de 0001/0002 reescrito.
Quatro tabelas novas no schema ilc:

| Tabela | Grao |
|---|---|
| completion_decisions | Uma escolha de evento DELIVERED para uma entrega |
| conflicts | Um conflito, com entrega opcional na abertura |
| conflict_evidence | Uma entrada preservada como original ou alternativa |
| conflict_resolutions | Uma decisao auditada sobre um conflito |

Nova UNIQUE auxiliar uq_events_key_input em events sustenta FK de evidencia.
Nao altera eventos existentes. A UNIQUE de evento/entrega/tipo introduzida
por 0002 e reutilizada, sem ser removida por 0003.
Nenhuma dependencia ou extensao nova; lock e configuracao mantidos.

## 3. Garantias do banco

| Regra | Restricao |
|---|---|
| Conclusao da mesma entrega e tipo DELIVERED | FK composta event_key/delivery_key/event_type e CHECK de tipo |
| Ordem de escolha explicita | Numero positivo unico por entrega; raiz 1; antecessor com numero imediatamente anterior |
| Sem ciclos, saltos ou ramificacoes | FK composta de antecessor, entrega, numero e horario; UNIQUE de sucessor |
| Cronologia da cadeia | Horario anterior real pela FK e menor ou igual ao atual |
| Autoria, horario, tipo e motivo | NOT NULL, CHECK nao vazio e horario finito; autor de sistema explicito tambem na escolha provisoria |
| Conflito sem entrega encontrada | conflicts.delivery_key aceita NULL; nenhuma entrega ficticia |
| Evidencia vinculada a entrada real | FK de input_key; evento/documento opcionais com FK composta para a mesma entrada |
| Alternativas preservadas | Entradas distintas por conflito; conjunto com ORIGINAL e ALTERNATIVE exigido por trigger deferido |
| Entrega conhecida coerente | Triggers rejeitam evidencia aceita de outra entrega e resolucao divergente do contexto |
| Vínculo tardio auditavel | Entrega opcional na resolucao; vinculo original nao e reescrito; uma entrega ja registrada em resolucao nao pode ser trocada ou apagada por revisao |
| Escolha na resolucao | FK da decisao/entrega; decisao nao pode ser futura em relacao a resolucao |
| Resolucao encadeada | Numero unico por conflito, antecessor imediatamente anterior do mesmo conflito, horario nao regressivo e sem ciclos |
| Evidencias finalizadas | Novas evidencias bloqueadas apos primeira resolucao; escrita serializada por lock do conflito |
| Historico imutavel | UPDATE/DELETE bloqueados nas quatro tabelas |

Conflito e suas duas evidencias sao inseridos na mesma transacao.
Os testes forcam SET CONSTRAINTS ALL IMMEDIATE para validar o estado final.
Conflito aberto nao exige resolucao nem decisao de conclusao ficticia.
Resolucao pode registrar uma referencia ainda desconhecida sem inventar
entrega; a interpretacao operacional do texto da decisao cabe a aplicacao.

## 4. Fronteira com a aplicacao e limitacoes

- Nao ha deteccao nem resolucao automatica de conflitos.
- A primeira conclusao aceita deve ser escolhida pela rotina futura com
  base em events.acceptance_sequence; o banco armazena e ordena escolhas,
  mas nao calcula a escolha provisoria nem a situacao fisica atual.
- Tipos de conflito e texto de decisao sao nao vazios, sem catalogo fechado
  novo inventado para o contrato. Sua semantica sera validada na aplicacao.
- O banco nao compara hashes/conteudos normalizados para provar conflito
  de identidade, nem interpreta se uma evidencia e original ou alternativa.
- Referencias opcionais a objetos aceitos sao coerentes quando fornecidas.
  Uma entrada nao aceita pode permanecer apenas como input_key.
- A escolha precisa ser DELIVERED da mesma entrega, mas exigir que esteja
  entre as alternativas de um conflito especifico, justificar a escolha,
  verificar permissoes reais do autor e acionar reavaliacao sao regras futuras.
- Nao ha calculo de M1-M4, bloqueio operacional de novas aprovacoes durante
  conflito, parser, gerador, API ou ETL.
- A FK da cadeia impede ciclos e saltos. Atribuir numeros exige coordenacao
  da aplicacao; concorrencia pode causar rejeicao recuperavel por UNIQUE.
- Lock por conflito implementado; ensaio de duas sessoes simultaneas ainda
  nao executado. Nao afirmar concorrencia testada a partir de casos sequenciais.
- Imutabilidade protegida para DML; ilc_app e proprietario e pode alterar DDL.
  Nao representa separacao de papeis de producao.
- Limitacoes anteriores de 0002 permanecem, inclusive novos motivos em
  avaliacoes historicas ainda dependentes da camada de aplicacao.

## 5. Pratica central de Joao

Arquivo migrations/versions/0003_decisions_conflicts.py,
funcao add_completion_event_link. Substituir somente o NotImplementedError
por op.create_foreign_key com:

- Nome: fk_completion_event_delivery.
- Origem: completion_decisions; referencia: events.
- Colunas locais e referenciadas: event_key, delivery_key, event_type.
- source_schema="ilc", referent_schema="ilc", ondelete="RESTRICT".

Preservar o nome da funcao e sua chamada no upgrade.
O bloqueio impede executar a revisao antes da pratica orientada.
Caso valido: DELIVERED da entrega da decisao. Rejeitados: evento de outro
tipo ou evento pertencente a outra entrega. Joao executara os testes e
explicara o que o banco aceitou/rejeitou; nao inferir aprendizagem da saida.

## 6. Testes e preservacao preparados

56 casos novos preparados (contagem estatica, ainda nao executados):
catalogo/FK central; escolhas e resolucoes validas; entrega desconhecida;
vinculo tardio; referencia de outra entrega/entrada; metadados vazios;
antecessor inexistente/de outro conflito; saltos, ciclos e ramificacoes;
cronologia; evidencias distintas; preservacao de alternativas e historico;
bloqueio de evidencia posterior a resolucao.
Esperado conjunto completo: 91 anteriores + 56 novos = 147 casos.
A contagem efetiva e os resultados devem ser confirmados pelo pytest.

As suites anteriores mantem seus 91 casos e expectativas de negocio.
Mudancas necessarias: aceitar a nova revisao, conferir catalogo de dezenove
tabelas quando aplicavel e limitar contagens as origens mock_a/mock_b das
proprias fixtures. A sentinela persistente nao deve aumentar essas contagens.
Nao foram removidas as assercoes de integridade ou ajustados SQLSTATEs.

scripts/decision_migration_probe.py --initialize insere uma fixture minima
persistente nas quinze tabelas anteriores, sob __p02d_preservation__.
Ela e sintetica, feita a mao; referencia de arquivo e checksum sao ilustrativos,
sem alegar arquivo efetivamente extraido. Nao e gerador nem parser.
A inicializacao so e permitida em 0002 e falha sem sobrescrever se ja existir.
As consultas subsequentes calculam SHA256 sobre todas as linhas das quinze
tabelas, ordenadas e serializadas. Guardar a primeira impressao digital;
--expect-sha256 exige igualdade depois da subida, descida e nova subida.
Nenhuma linha, URL com credenciais ou segredo e impressa pelo verificador.
As suites usam transacoes com rollback, preservando a impressao digital.
Executar sem outros escritores no banco descartavel durante o ciclo.

| Etapa | Catalogo esperado | Dados anteriores |
|---|---|---|
| Entrada | 0002_documents, quinze tabelas, btree_gist 1.8 | Sentinelas e SHA256 inicial |
| Subida | 0003_decisions_conflicts, dezenove tabelas | Mesmo SHA256 |
| Descida apenas de 0003 | 0002_documents, quinze tabelas; extensao mantida | Mesmo SHA256; 91 casos anteriores |
| Nova subida | 0003_decisions_conflicts, dezenove tabelas | Mesmo SHA256; suite completa |

O downgrade remove apenas quatro tabelas novas, seus triggers/funcoes e
uq_events_key_input. Nao remove extensao, schema ilc, dados documentais,
banco ou cluster. Dados proprios de 0003 sao apagados; nova subida recria
suas estruturas vazias, nao restaura seus dados.

## 7. Comandos previstos - nao sao evidencia de execucao

Depois de implementar a restricao e obter Ruff aprovado:

```powershell
.\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect documents
.\.venv\Scripts\python.exe -m scripts.decision_migration_probe --database ilc_f2p02b_test --initialize
$env:ILC_TEST_DATABASE = 'ilc_f2p02b_test'
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py tests/integration/test_document_migration.py
.\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade 0003_decisions_conflicts
.\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
.\.venv\Scripts\python.exe -m pytest -q tests/integration
.\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test downgrade 0002_documents
.\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect documents
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py tests/integration/test_document_migration.py
.\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade 0003_decisions_conflicts
.\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
.\.venv\Scripts\python.exe -m pytest -q tests/integration
Remove-Item Env:ILC_TEST_DATABASE
.\.venv\Scripts\python.exe scripts/check_db_connection.py
```

Executar em blocos controlados, interromper em qualquer falha, nao executar
o downgrade se a suite falhar. Apos cada etapa, executar ambos os probes;
no novo, informar --expect-sha256 com o valor efetivamente observado na
inicializacao. Nao copiar um hash de exemplo.

## 8. Fontes e evidencia da preparacao

Fontes oficiais consultadas em 19/10/2026 antes de preparar a revisao:
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://www.postgresql.org/docs/18/sql-createtrigger.html
- https://alembic.sqlalchemy.org/en/latest/ops.html

Sintaxe Python conferida via AST pelo assistente. Nenhum PostgreSQL, Ruff
ou teste de integracao executado no ambiente do assistente nesta preparacao.
Os resultados locais devem ser registrados separadamente apos recebidos.
Assistente preparou estrutura, testes e documentacao; pratica central e
execucao de Joao ainda pendentes. Sem atribuicao de explicacoes nao dadas.

## 9. Pendencias e passagem

Implementar FK central; executar Ruff, inicializacao de sentinela e regressao;
observar ciclo reversivel e comparar catalogo/conteudo; interpretar caso valido
e rejeitado; registrar resultados e incidentes; publicar commit final e retornar
ao gerente. Esta preparacao nao e aceite nem fechamento de F2-P02D ou F2.
