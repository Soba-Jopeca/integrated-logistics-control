# F2-P02C - Estrutura documental e integridade de versoes

Data: 19/10/2026. Branch: feat/f2-p02c-documents.
Base autorizada: a6348f5c186546e5ef9e7316e84de8dbd35151b5.
Codigo anterior aceito: dc1cc8e361dfc6cba3809407f92b4a55d77b6d7c.
Referencias: contratos 06 e modelo 07 nessa base.
Estado: execucao local de 0002_documents e ciclo reversivel comprovados;
validacao central pendente. Commit final sera identificado na passagem.
F2 permanece aberta; R03 parcial. Sem parser, conferencia funcional,
gerador, API ou ETL. Decisoes de conclusao e conflitos ficam pendentes.

## 1. Entrada reconferida no Windows de Joao

- Git na base a6348f5; branch feat/f2-p02c-documents criada.
- .vscode nao rastreada preservada.
- Conexao ilc_app/ilc: PASS, servidor 18.6, 127.0.0.1:55432, UTC,
  cinco privilegios administrativos false, limite de cinco conexoes.
- Banco descartavel ilc_f2p02b_test, usuario ilc_app.
- Catalogo: 0001_core e oito tabelas, PASS.
- pg_available_extensions: btree_gist, default_version=1.8,
  installed_version ausente. Disponivel, ainda nao instalada.

## 2. Escopo e preservacao da base

Nova revisao 0002_documents, down_revision=0001_core.
Arquivo migrations/versions/0001_core.py e seu SQL preservados.
Sete tabelas novas no schema ilc:
document_families, document_versions, extractions, evaluations,
evaluation_reasons, document_validities e evaluation_validities.
Total esperado em head: quinze tabelas de dominio, alem de
public.alembic_version. Nao confundir schema ilc com banco ilc.

Uma UNIQUE auxiliar e acrescentada a events para permitir FK composta
de evento DELIVERED e entrega. E retirada no downgrade de 0002.
Nenhuma coluna ou dado das oito tabelas anteriores e removido.

btree_gist sera criada no schema dedicado ilc_gist apenas dentro do banco
descartavel. A criacao deliberadamente nao usa IF NOT EXISTS: se a extensao
ja existir, a migracao deve falhar sem adotar objetos alheios.
O downgrade remove apenas a extensao e schema que esta revisao criou.
O modulo ja consta dos binarios instalados; nenhum pacote Python novo.
Extensao trusted permite instalacao pelo proprietario do banco sem SUPERUSER.

## 3. Garantias estruturais no banco

| Regra | Implementacao estrutural |
|---|---|
| Familia por origem | UNIQUE(source_system,document_family_id) |
| Versao por origem e familia | UNIQUE(source_system,document_id), UNIQUE(family_key,version) |
| Mesma origem/entrega da familia | FK composta family_key/source_system/delivery_key |
| Antecessora da mesma familia e incremento unitario | predecessor_version gerada como version-1; FK composta de antecessora/familia/versao |
| Sem saltos, ciclos ou ramificacoes documentais | Versao positiva, antecessora condicional, incremento por FK, UNIQUE da sucessora |
| Entrada e tentativa de aceitacao coerentes | FKs compostas de input_key/origem/tipo DOCUMENT e tentativa/input_key |
| Arquivo preservado | Hash hexadecimal minusculo, referencia, tamanho positivo, envelope e versao imutaveis |
| Extracao vinculada a documento e tentativa | FKs compostas para documento/input_key e tentativa/input_key |
| Avaliacao e extracao da mesma versao | FK composta implementada por Joao: extraction_key/document_key |
| Avaliacao e conclusao da mesma entrega | FK composta para evento, entrega e tipo DELIVERED |
| Revisao da mesma versao sem ciclos | FK de avaliacao anterior/documento/numero e numero anterior estritamente menor |
| Revisao manual auditavel | Autor e justificativa obrigatorios quando is_manual=true |
| Resultados e motivos | APPROVED sem motivos bloqueadores; REVIEW_REQUIRED exige motivo, por triggers deferidos |
| Sem aprovacao estrutural sem extracao/conclusao | CHECK de referencias e trigger exigindo extracao EXTRACTED |
| Motivo unico mesmo com campo nulo | UNIQUE NULLS NOT DISTINCT(evaluation_key,code,affected_field) |
| Vigencias sem sobreposicao | EXCLUDE USING gist por familia/documento e tstzrange [inicio,fim) |
| No maximo um intervalo aberto | Consequencia da exclusao de intervalos com fim ilimitado |
| Familia com primeira versao e uma vigente | Triggers de restricao deferidos conferem estado final da transacao |
| Troca atomica e antecessora vigente | Toda versao tem um intervalo desde accepted_at; fim da antecessora igual ao inicio da sucessora; ultima permanece aberta |
| Avaliacao conhecida ao selecionar vigencia | evaluated_at <= valid_from |
| Preservacao historica | UPDATE/DELETE bloqueados para familias, versoes, extracoes, avaliacoes e motivos; intervalos somente podem ser encerrados uma vez |

Um intervalo fechado nao pode ser reaberto, alterado ou apagado.
Intervalos adjacentes sao permitidos: [a,b) e [b,c).
Os triggers deferidos permitem encerrar a vigencia anterior e inserir a
nova na mesma transacao; o estado final deve permanecer consistente.
O teste forca SET CONSTRAINTS ALL IMMEDIATE para verificar essas regras.

## 4. Fronteira com a aplicacao e limitacoes

- Esta revisao armazena estruturas; nao executa parser nem calcula aprovacao.
  Pre-requisitos estruturais nao comprovam conferencia funcional.
- Validar os bytes, calcular checksum, proteger caminhos e rejeitar XML
  malicioso continuam para a fase documental autorizada.
- Comparar referencia, quantidade, unidade, recebedor e minuto UTC e
  tratar conflitos ainda depende da implementacao de regras futuras.
- Preservar received_at original e sincronizar a primeira chegada com
  a entrada continua responsabilidade da rotina de aceitacao futura.
- Coordenar lock/ordem de escrita, motivos e versao vigente e dever da
  aplicacao; o banco rejeita estados finais que violem as restricoes.
- As linhas de motivos sao imutaveis, mas acrescentar um novo motivo a
  avaliacao historica REVIEW_REQUIRED ainda deve ser proibido pela camada
  de aplicacao apos finalizacao. Essa imutabilidade do agregado inteiro
  nao e garantida nesta revisao apenas pelos triggers de linha.
- O numero da avaliacao ordena os vinculos anteriores e impede ciclos;
  validar a cronologia de uma revisao em relacao a outra e regra futura.
- Preservam-se snapshots de valores esperados na avaliacao. Sua copia
  correta a partir do contexto de negocio ainda depende da aplicacao.
- Extracao pode preservar ausencia ou valor invalido para revisao;
  nao se inventa quantidade nem se transforma valor negativo em zero.
- EXCLUDE e uma garantia do PostgreSQL, inclusive frente a concorrencia;
  um ensaio de duas sessoes simultaneas nao foi executado nesta preparacao.
- ilc_app e proprietario do banco; pode alterar DDL e contornar protecoes
  como qualquer proprietario. Nao equivale a separacao de papeis de producao.
- Avaliacoes, motivos e vigencias nao implementam conflitos nem decisoes
  de conclusao; esses dominios permanecem para a divisao seguinte.

## 5. Pratica central de Joao

Em migrations/versions/0002_documents.py, funcao
add_evaluation_extraction_link, substituir o NotImplementedError por uma
chamada op.create_foreign_key, com os argumentos:

- Nome: fk_evaluations_extraction_document.
- Tabela de origem: evaluations; tabela referenciada: extractions.
- Colunas locais: extraction_key, document_key.
- Colunas referenciadas: extraction_key, document_key.
- source_schema=ilc; referent_schema=ilc; ondelete=RESTRICT.

Nao alterar a definicao da funcao nem sua chamada no upgrade.
O teste de catalogo verifica as duas colunas, e um teste negativo usa
extracao de outro documento para exigir rejeicao por essa FK.
A preparacao inicial ficou bloqueada ate a edicao local de Joao.
A edicao orientada foi executada e o vinculo composto passou nos testes.
Edicao e execucao devem ser registradas pelas saidas, sem inferir
compreensao autoral independente. Explicacoes fornecidas pelo assistente
devem manter essa atribuicao.

## 6. Catalogo esperado e verificacoes preparadas

| Momento | Revisao | Tabelas de dominio | Extensao |
|---|---|---|---|
| Antes | 0001_core | Oito anteriores | Ausente |
| Upgrade | 0002_documents | Oito anteriores + sete documentais | btree_gist instalada |
| Downgrade apenas de 0002 | 0001_core | Oito anteriores | Removida |
| Novo upgrade | 0002_documents | Quinze | Reinstalada |

Os 30 casos anteriores sao preservados. Apenas o reconhecimento da revisao
e do catalogo foi estendido: agora aceitam o nucleo presente em 0002.
O catalogo completo de quinze tabelas e conferido independentemente pelo
inspetor e teste documental. Nenhuma expectativa de negocio dos 30 casos
foi relaxada. O caso ON DELETE RESTRICT continua esperando 23001.

Novos casos: identidade por origem, versao por familia, antecessora de
outra familia, salto/ramificacao, vinculos de entrada/tentativa, formato
do arquivo, primeira versao/vigencia atomicas, imutabilidade, extracao
de outra versao, revisao manual, motivos e intervalos abertos/fechados.
Fixtures sao pequenas, escritas a mao e revertidas por transacao.
Nao representam um gerador ou conferencia funcional implementados.

Um registro sintetico em ilc.sources sera usado como sentinela no banco
descartavel para comprovar preservacao de dado do nucleo no downgrade.
Fonte: __p02c_preservation__. O script nao altera registro preexistente
com outro conteudo e nao se conecta ao banco ilc para escrita.

Comandos previstos, executar em blocos controlados e parar em falha:

    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect core
    .\.venv\Scripts\python.exe -m scripts.document_migration_probe --database ilc_f2p02b_test --initialize
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade head
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
    $env:ILC_TEST_DATABASE = 'ilc_f2p02b_test'
    .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py tests/integration/test_document_migration.py
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test downgrade 0001_core
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect core
    .\.venv\Scripts\python.exe -m scripts.document_migration_probe --database ilc_f2p02b_test
    .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py
    .\.venv\Scripts\python.exe -m alembic -x database=ilc_f2p02b_test upgrade head
    .\.venv\Scripts\python.exe -m scripts.inspect_migration --database ilc_f2p02b_test --expect head
    .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_core_migration.py tests/integration/test_document_migration.py
    .\.venv\Scripts\python.exe -m scripts.document_migration_probe --database ilc_f2p02b_test
    Remove-Item Env:ILC_TEST_DATABASE
    .\.venv\Scripts\python.exe scripts/check_db_connection.py

Rollback de 0002 remove apenas suas tabelas, triggers, funcoes, UNIQUE
auxiliar e extensao, preservando 0001 e a sentinela. Nao apaga banco ou
cluster e nao restaura dados documentais apagados; o novo upgrade recria
estrutura documental vazia.

## 7. Evidencias, publicacao e proximo passo

Nesta preparacao: sintaxe Python conferida pelo assistente.
Ambiente do assistente sem PostgreSQL, Alembic ou Ruff: nao foram
executados DDL, testes de banco ou lint aqui. Os resultados observados no
Windows de Joao estao registrados na secao 8; nao decorrem da preparacao.
Registrar resultados, incidentes corrigidos, catalogo esperado/observado,
Ruff e commits na devolucao. Sem declaracao de fase fechada.

Fontes oficiais consultadas antes da preparacao:
- https://www.postgresql.org/docs/18/btree-gist.html
- https://www.postgresql.org/docs/18/rangetypes.html
- https://www.postgresql.org/docs/18/ddl-constraints.html
- https://alembic.sqlalchemy.org/en/latest/tutorial.html
- https://www.postgresql.org/docs/18/errcodes-appendix.html

Proximo passo somente conforme cartao central vigente; retornar ao gerente
antes de iniciar a divisao de decisoes de conclusao e conflitos.

## 8. Execucao observada no Windows - 19/10/2026

### Catalogo esperado versus observado

| Etapa | Esperado | Observado |
|---|---|---|
| Inicio | 0001_core, oito tabelas, sem extensao instalada | PASS |
| Primeira subida | 0002_documents, quinze tabelas, btree_gist 1.8 | PASS |
| Descida somente de 0002 | 0001_core, oito tabelas; extensao e schema auxiliar removidos | PASS |
| Nova subida | 0002_documents, quinze tabelas; btree_gist 1.8 reinstalada | PASS |
| Preservacao do nucleo | Sentinela inicial presente apos subida, descida e nova subida | PASS |
| Conexao anterior | ilc_app/ilc acessivel em 127.0.0.1:55432 | PASS |

Arquivo e SQL de 0001_core: git diff --exit-code sem alteracoes,
com mensagem local 0001_core preservada: PASS antes da execucao.

### Qualidade e resultados

- Joao substituiu a funcao de bloqueio pela FK composta orientada:
  fk_evaluations_extraction_document, extraction_key/document_key,
  de evaluations para extractions, ambas no schema ilc, ON DELETE RESTRICT.
- Sintaxe Python: PASS. Ruff, apos organizacao e formatacao: All checks passed!
- Antes da suite, o assistente corrigiu somente a expectativa do caso de
  APPROVED com extraction_key nulo: o trigger BEFORE ja rejeita essa entrada
  por ck_evaluation_successful_extraction, antes do CHECK da tabela.
  Nenhuma restricao foi removida e nenhum DDL foi alterado nesse ajuste.
- Primeira suite completa: 91 passed in 7.65s.
- Apos downgrade para 0001_core: regressao dos 30 anteriores,
  30 passed in 1.62s.
- Apos segundo upgrade: mesma suite completa, 91 passed in 5.22s.
- Sao 91 casos distintos: 30 do nucleo e 61 documentais. Reexecucoes nao
  aumentam o numero de casos distintos.
- As duracoes acima foram reportadas pelo pytest.
- A sentinela persistiu em todas as verificacoes do ciclo.
- Verificador final de ilc: PASS, servidor 18.6, UTC, ilc_app/ilc,
  cinco privilegios administrativos false, limite de cinco conexoes.
- Alvo das migracoes e fixtures: apenas ilc_f2p02b_test.
  O banco ilc nao recebeu esta migracao.

### Participacao e explicacoes de referencia

Joao editou a FK composta com orientacao do assistente e executou
sintaxe, Ruff, inspecoes, suites e ciclo de migracao.
O assistente preparou estrutura, testes, ajustes e documentacao.
Compreensao autoral independente nao e inferida da execucao.

Explicacoes do assistente:
- A FK composta exige que a extracao exista e pertenca ao mesmo document_key
  da avaliacao. Uma FK apenas por extraction_key nao garantiria isso.
- Vigencias [a,b) e [b,c) podem ser adjacentes; intervalos que compartilham
  qualquer ponto para a mesma familia/documento sao rejeitados por EXCLUDE.
- O downgrade para 0001_core removeu a parte documental, seus objetos
  auxiliares e extensao. Preservou o nucleo, sua sentinela, banco e cluster.
  O novo upgrade recriou estrutura documental vazia.

### Passagem e limites mantidos

F2-P02C: execucao e verificacao local comprovadas; aguarda validacao central.
Codigo editado e formatado localmente deve integrar o commit de fechamento
identificado na devolucao; o commit inicial era preparacao bloqueada.
Mantidas as limitacoes da secao 4, incluindo adicao de motivos a agregados
historicos ainda dependente da aplicacao e ausencia de ensaio concorrente
com duas sessoes. Nao foi implementada conferencia funcional.
Decisoes de conclusao, conflitos, gerador, API e ETL nao iniciados.
F2 aberta e R03 parcial. Aguardar decisao central antes do proximo cartao.

Fonte complementar consultada na revisao dos testes:
https://www.postgresql.org/docs/18/trigger-definition.html
