# F2-P04 - Consolidacao verificavel da F2

Preparacao: 19/10/2026. Verificacao final: 20/10/2026.
Branch de consolidacao: docs/f2-p04-consolidation.
Entrada aceita: 33ba8d02931883cc31d0312049587abae444e9ef.
Autoridade: cartao F2-P04 encaminhado por Joao, com P01, P02A-D e P03
aceitos centralmente com limitacoes. Nao foram fornecidos IDs adicionais
de validacao; nenhum foi inventado.

**Estado central em 20/10/2026: F2 FECHADA COM LIMITACOES — VAL-F2-P04-001.**
R03/R04 aceitos no escopo demonstrado. F3 pronta para receber cartao, ainda
nao iniciada; F4-F6 bloqueadas. PR #2 permanece sem merge.
Registros de fase aberta abaixo sao historicos, anteriores a esta decisao.

## 1. Escopo consolidado e proveniencia

Esta consolidacao organiza README, plano e passagem. Nao altera codigo,
lock, configuracao de banco, migracoes, testes ou fixtures da entrada aceita.
O README distingue componentes executaveis de funcionalidades futuras e
reune os comandos observados de ambiente, conexao, migracao e geracao.

| Passo | Commit tecnico publicado | Evidencia e limite |
|---|---|---|
| P01 | acbff3da02cc06753c755b8ce549ead698e151c8 | Venv, lock/hashes, pip check e reproducao no mesmo Windows/Python usando cache |
| P02A | 2c0ab8bf9cca9e6221cabf60c1ff1b8735db2742 | PostgreSQL dedicado, loopback/SCRAM, ilc_app e conexao SQLAlchemy/psycopg |
| P02B | dc1cc8e361dfc6cba3809407f92b4a55d77b6d7c | 0001_core; oito tabelas; 30 casos; passagem a6348f5 |
| P02C | 4959edfc5df5cf5c25381a3766e5f4cdbe167c1b | 0002_documents; sete tabelas adicionais; 91 casos; nucleo preservado |
| P02D | 35dd157dcb44932eebf948cc85cd4c2ba98b064a | 0003_decisions_conflicts; quatro tabelas adicionais; 147 casos e sentinelas |
| P03 | 33ba8d02931883cc31d0312049587abae444e9ef | Gerador/verificador; 24 testes e 11 subtestes; duas geracoes identicas |

Registros completos, comandos, incidentes e fontes oficiais:
[09 ambiente](09-f2-p01-environment.md), [10 PostgreSQL](10-f2-p02a-postgresql.md),
[11 nucleo](11-f2-p02b-core-migration.md), [12 documentos](12-f2-p02c-document-migration.md),
[13 decisoes/conflitos](13-f2-p02d-decisions-conflicts.md) e
[14 gerador](14-f2-p03-synthetic-generator.md).
Esses documentos preservam estados de cada momento; esta passagem e o cartao
central atual prevalecem na leitura de pendencias ja executadas/aceitas.
Fechamento F1 permanece em [08](08-f1-consolidation-and-analytical-model.md).

## 2. Estado local/remoto recuperado e PR

Ultima saida local recebida, ao terminar P03: HEAD 33ba8d0, branch
feat/f2-p03-synthetic-generator sincronizada com origin; apenas .vscode
nao rastreada. Em P04, Joao confirmou a branch de consolidacao e o HEAD
f2d1d11cbbe35a6d2773ae15257896a2270517bf sincronizado com origin; apenas
.vscode nao rastreada. Resultado 0/2 em relacao a origin/main naquele momento.
Nenhum acesso ao Windows do usuario e presumido pelo assistente.

Remoto conferido na preparacao:

- main: 9f6720a60b29dbfd42fb6c509abff3fe583b7363.
- Entrada aceita: 33ba8d02931883cc31d0312049587abae444e9ef.
- Base historica comum: 161a874678159055b3a6e347c84664ca958667f4.
- A linha aceita possui 29 commits exclusivos e main um commit exclusivo.
- O commit exclusivo de main e o squash de F1, Docs/data contracts (#1).
- Comparacao direta dos conteudos: 61 caminhos diferentes entre main e a
  entrada aceita; nenhum arquivo de main ausente na entrada aceita.
- Os arquivos compartilhados com conteudo diferente sao .gitignore, README,
  plano 04 e consolidacao 08; correspondem a protecao adicional e registros
  posteriores, incluindo o fechamento documental autorizado da F1.
- Comparacao de historias divergentes nao equivale a conflito textual provado.

Para evitar reescrever a linha tecnica ou duplicar a F1 por cherry-pick,
a branch de consolidacao parte de main e recebe a arvore de conteudo aceita
de 33ba8d0, mais somente README, plano 04 e este documento 15.
O commit tem main como pai; a proveniencia tecnica integral esta registrada
acima. Branches/commits originais da F1 e F2 permanecem publicados.
Nao foi executado merge, rebase, reset, force-push ou descarte de alteracoes.

O PR deve apontar docs/f2-p04-consolidation para main e ficar em rascunho
durante a verificacao. URL, estado de conflitos reportado pelo GitHub e
commit inicial estao registrados na secao 9; reconferir ao final.
Se main avancar, reconferir o diff antes de qualquer integracao futura.
Preparar PR nao significa integrar, fechar F2 ou liberar F3.

## 3. Ambiente e configuracao aceitos

| Componente | Versao/configuracao observada |
|---|---|
| Sistema/Python/Git | Windows 11 x64; Python 3.13.14; Git 2.55.0.windows.5 |
| Ferramentas | pip 26.1.2; pip-tools 7.6.2; pytest 9.1.1; Ruff 0.17.1 |
| Conexao/migracao | SQLAlchemy 2.0.55; psycopg e psycopg-binary 3.3.6; Alembic 1.20.0; python-dotenv 1.2.4 |
| Servidor | PostgreSQL 18.6; 127.0.0.1:55432; UTC; SCRAM; max_connections=20; shared_buffers=64MB |
| Usuario | ilc_app, LOGIN, rolconnlimit=5; cinco privilegios administrativos false |
| Banco de conexao | ilc, proprietario ilc_app, sem aplicacao das migracoes nesta F2 |
| Banco de ensaios | ilc_f2p02b_test, revisao 0003, 19 tabelas e btree_gist 1.8 |

Lock utilizado: requirements.lock, SHA256 observado:

    704A34566E7C001AC45D2FB1ED0CA625F20E0792A47FEA3E89A21C6950F2EFBF

Segredos apenas no .env local ignorado; .venv tambem ignorada.
.env.example contem senha vazia e variaveis documentadas.
Gerados volumosos em data/generated/ ignorados; .vscode preservada fora do PR.
Nao imprimir senha, conteudo de .env ou URL com credenciais na verificacao.
Ser proprietario sem SUPERUSER nao representa restricao apenas a DML:
ilc_app pode alterar DDL e contornar triggers como proprietario.

## 4. Requisitos e limites de evidencia

| Requisito | Estado para decisao central |
|---|---|
| R01 | Negocio documentado e aceito na F1; sem alegar explicacao independente nao registrada |
| R02 | Contratos/modelos aceitos; integridade estrutural das revisoes exercitada na F2 |
| R03 | Aceito no escopo demonstrado por VAL-F2-P04-001: ambiente/lock/conexao/migracoes reversiveis no ambiente local; limites de portabilidade preservados |
| R04 | Aceito no escopo demonstrado por VAL-F2-P04-001: gerador, fixtures e reproducao de entradas; nao comprova ingestao ou conferencia funcional |
| R05 | API/OpenAPI/paginacao/falhas: F3, nao implementado |
| R06 | Ingestao CSV/API e reconciliacao: F3, nao implementado |
| R07 | Idempotencia, conflitos, retomada e quarentena operacionais: F3, nao implementado; existem estruturas e entradas de teste |
| R08 | PDF/XML real e parsing protegido: F4, nao implementado |
| R09 | Conferencia funcional e reavaliacao: F4, nao implementado; estrutura nao equivale a regra de negocio executada |
| R10 | Experimento IA e viabilidade: F4, nao executado |
| R11 | Aplicacao de consulta/upload: F5, nao implementado |
| R12 | Metricas SQL/DAX e Power BI: F5, nao implementado |
| R13 | Scheduler e recuperacao operacional: F6, nao implementado |
| R14 | Testes e Ruff observados por passo; revalidacao conjunta P04 aprovada em 20/10/2026; CI/PostgreSQL isolado/E2E permanecem para F6 |
| R15 | Parcial: configuracao externa, sinteticidade, loopback, SQL parametrizado e logs sanitizados; protecoes de upload/XML e papeis de producao futuros |
| R16 | Instalacao limpa, backup/restauracao e rollback de release: F6, nao demonstrados |
| R17 | Evidencias e arquitetura disponiveis; demo completa, capturas de produto e release: F6, nao concluidos |

Nao transformar teste de fixture/estrutura em evidencia de ingestion,
aprovacao documental ou ganho operacional real.

## 5. Garantias do banco versus aplicacao futura

| Garantia estrutural exercitada | Responsabilidade futura ou limite |
|---|---|
| Unicidade por origem e vinculos coerentes | Detectar duplicacao/conflito comparando conteudo, preservar chegadas e reconciliar contagens |
| Familia/versao, antecessora, vigencia e historico | Aceitar arquivo/envelope, validar bytes, checksum e caminho; coordenar troca atomica |
| Extracao/avaliacao da mesma versao | Executar parser e regras; preservar ausencias; calcular snapshots corretos e resultados |
| Motivos de REVIEW_REQUIRED e imutabilidade das linhas | Bloquear adicao de novos motivos a avaliacao historica finalizada; agregado inteiro ainda nao selado por 0002 |
| Exclusao de intervalos sobrepostos | Coordenar transacoes/retry/locks; ensaio de duas sessoes simultaneas ainda nao executado |
| Cadeias de revisao sem ciclos | Atribuir sequencia e validar cronologia/semantica de revisao conforme regras futuras |
| Escolha DELIVERED da mesma entrega e resolucoes auditadas | Selecionar provisoria pela aceitacao persistida, escolher alternativa pertinente e acionar reavaliacao; sem resolucao automatica |
| Evidencias de conflito imutaveis e seladas apos resolucao | Detectar conflito, provar semantica original/alternativa e autorizar autores reais |
| Recebimentos/tentativas rastreaveis | Manter primeiro received_at, checkpoint apos commit, retomada e recuperacao operacional |

P03 produz referencias JSON sinteticas, nao PDFs/XML reais. O media_type
no envelope descreve o formato pretendido; nenhum file_sha256 de PDF real
e inventado. As expectativas permanecem EXPECTED_NOT_EXECUTED.
Volume adicional 25 observado; teto 10000 nao ensaiado. Escrita em memoria;
diretorios existentes recusados. Resultado nao prova vazao de pipeline.

## 6. Evidencias anteriores aceitas

- P01: isolamento, imports, pip check e reproducao com lock/hashes em nova
  venv no mesmo Windows/Python/cache; nao instalacao limpa de sistema.
- P02B: parada/reinicio da instancia exclusiva e conexao reconferida;
  ciclo 0001 com oito tabelas e 30 testes.
- P02C: ciclo 0002 para 0001 e nova subida, nucleo/sentinela preservados;
  91 casos (30 anteriores + 61 documentais).
- P02D: ciclo 0003 para 0002 e nova subida, 15 tabelas anteriores preservadas;
  147 casos (91 anteriores + 56 novos), suite final 9.55s.
- SHA256 das 15 tabelas anteriores preservado no ciclo P02D:

      1a730d96e2d525c4159990e2429c74c4c65bce7e3f4ada9c50a1ed575249c615

- P03 Windows: 24 testes e 11 subtestes em 0.73s; Ruff aprovado.
- Duas geracoes seed=20261019/volume adicional=25: 33 entregas, 46 arquivos,
  todos os bytes/hashes iguais; SHA256 de SHA256SUMS:

      0bfc266949ab9488a357ef67a03a3f12a4b6dc46cdd6caa1969bca27d67f9a2c

- Fixture pequena: oito entregas/21 arquivos; SHA256 de SHA256SUMS:

      5e2d363aabb33506cbae02252037b32f742c08ebc3d43718f31b4ce8e27d7e50

As duracoes acima sao saidas do pytest nos passos anteriores, nao medicao
da consolidacao atual. Nao somar reexecucoes como casos novos.

## 7. Verificacao final P04 - observada em 20/10/2026

Commit local verificado: f2d1d11cbbe35a6d2773ae15257896a2270517bf.
Codigo identico a entrada aceita 33ba8d0; atualizacoes posteriores desta
passagem, README e plano sao somente documentais.

| Item | Esperado | Observado |
|---|---|---|
| Git local | Branch P04 sincronizada, .vscode preservada | PASS; HEAD f2d1d11, apenas .vscode nao rastreada |
| Ambiente | Python da venv e versoes aceitas; pip check | Python 3.13.14, versoes conferidas, No broken requirements found |
| Ruff check | Sem erros em scripts/migrations/tests | All checks passed! |
| Ruff format --check | Arquivos ja formatados | 21 files already formatted |
| Gerador | 24 testes, subtestes separados | 24 passed, 11 subtests passed in 0.84s |
| Catalogo descartavel | 0003, 19 tabelas, btree_gist 1.8 | PASS apos iniciar a instancia existente |
| Integracao | 147 testes aprovados, sem downgrade | 147 passed in 8.44s |
| Fixture pequena | Inventario, contagens e hashes coerentes | PASS |
| Sentinela anterior | Preservada em 0003 | Core sentinel preserved: PASS |
| Quinze tabelas anteriores | Mesmo SHA256 esperado | PASS; hash igual ao ciclo P02D |
| Conexao final | ilc_app/ilc, localhost:55432, UTC, sem privilegios administrativos | PASS; servidor 18.6, cinco flags false, limite 5 |
| PR | Revisavel para main, sem merge | PR #2 aberto em draft; estado remoto reconferido na passagem |

Versoes novamente impressas por Joao: pip 26.1.2, pip-tools 7.6.2,
SQLAlchemy 2.0.55, psycopg 3.3.6, Alembic 1.20.0, python-dotenv 1.2.4,
pytest 9.1.1 e Ruff 0.17.1. O SHA256 do lock registrado na secao 3 vem de
P01; a saida reenviada de P04 nao trouxe um novo valor Get-FileHash.
A equivalencia de blob do lock com a entrada aceita foi conferida remotamente.

Fixture final: oito pedidos/entregas, 13 eventos validos, seis envelopes
validos, um reenvio de cada tipo, uma alternativa de cada tipo, tres eventos
invalidos, dois envelopes invalidos, 28 chegadas e oito referencias documentais.
SHA256 de SHA256SUMS aprovado:

    5e2d363aabb33506cbae02252037b32f742c08ebc3d43718f31b4ce8e27d7e50

SHA256 das quinze tabelas anteriores novamente aprovado:

    1a730d96e2d525c4159990e2429c74c4c65bce7e3f4ada9c50a1ed575249c615

Nao houve downgrade, nova migracao ou geracao adicional para repetir
evidencias ja aceitas. O verificador da fixture nao executa conferencia
funcional; EXPECTED continua expectativa. Testes do gerador e integracao
sao conjuntos diferentes: 24 e 147 casos principais, sem somar subtestes
ou reexecucoes como novos casos.

### Ocorrencia de disponibilidade e recuperacao

A primeira tentativa de inspect_migration terminou com OperationalError.
Isso interrompeu o bloco antes da integracao, fixture e sentinelas.
A mensagem PowerShell "Banco descartavel fora de 0003" foi imprecisa:
OperationalError nao comprova revisao incorreta nem alteracao de credenciais.

Diagnostico posterior: pg_ctl status informou que nenhum servidor estava
executando. A instancia existente foi iniciada pelo pg_ctl no diretorio
dedicado C:\\ILC-PostgreSQL\\ilc-data-18. A partida emitiu aviso de possivel
outro servidor, aguardou e informou servidor iniciado. A conexao seguinte
retornou ilc_app/ilc, 18.6 e 127.0.0.1:55432; o catalogo permaneceu em 0003.
Nao foi executado initdb, instalacao, troca de usuario ou recriacao do banco.
A causa do processo parado e a origem do aviso nao foram isoladas.

Ambiente, Ruff e gerador ja aprovados nao foram repetidos sem necessidade.
Depois da recuperacao, Joao executou apenas as verificacoes pendentes,
todas aprovadas. Sem alteracao de codigo para resolver a indisponibilidade.

## 8. Historico - pendencias classificadas antes do fechamento

**Para decisao de fechamento P04:** verificacao local aprovada e registrada;
reconferir estado/URL do PR, publicar esta passagem e devolver ao gerente.
A indisponibilidade inicial foi recuperada e nao ha falha tecnica residual
observada no conjunto exigido. Aceite e fechamento continuam decisao central.
Nao fazer merge neste cartao mesmo com todos os checks locais aprovados.

**Limitacoes aceitas a preservar:** execucao local/cache, dono do banco,
ausencia de teste concorrente, motivo historico dependente da aplicacao,
referencias documentais sinteticas e interpretacao independente nao verificada.

**Futuro, sem implementacao neste cartao:** papeis/concorrencia operacionais,
ingestao/API/F3, parser/conferencia/F4, metricas/app/F5, CI/E2E/backup/F6.
Migrar ilc e integrar main exigem autorizacao especifica posterior.

**Manutencao local nao executada:** revisar .vscode se houver necessidade
futura; limpeza das extracoes/venv temporaria relatadas em 09/10 nao foi
comprovada. Nao apagar recursos para resolver pendencia documental.

Joao executa verificacoes e publica evidencias locais; assistente organiza
documentacao, revisa resultados e prepara PR. Explicacoes do assistente
mantem sua atribuicao, sem inventar aprendizagem ou execucao de Joao.

Estado submetido: F2 aberta, R03 parcial, F3-F6 bloqueadas. O gerente decide
aceite/ajustes e eventual fechamento; esta preparacao nao libera fase seguinte.


## 9. PR preparado e equivalencia tecnica conferida

PR: https://github.com/Soba-Jopeca/integrated-logistics-control/pull/2
Estado observado: open, draft=true, merged=false.
Commit inicial de consolidacao: 3fed963bd2792fd54b83391655e7fb7a6d2d6729.
Base: main em 9f6720a60b29dbfd42fb6c509abff3fe583b7363.
GitHub, apos calculo: mergeable=true, mergeable_state=clean.
Esse estado e uma fotografia do PR, nao autorizacao de merge.

PR inicial: um commit, 62 arquivos diferentes em relacao a main.
Comparacao direta das arvores confirmou que somente README, plano 04 e
novo documento 15 diferem da entrada aceita 33ba8d0. Nenhum arquivo da
entrada aceita ausente; codigo, testes, migracoes, lock e fixtures com os
mesmos blobs. Nenhum .env, .venv, .vscode ou data/generated rastreado.
Links internos dos tres documentos conferidos sem destino ausente.

O registro inicial desta secao descreve a preparacao do PR. A verificacao
posterior no Windows foi executada em 20/10/2026 e consta na secao 7;
resultados anteriores nao foram reciclados como verificacao P04.


## 10. Historico - passagem apos verificacao, anterior a decisao central

P04 tecnicamente verificado; submeter ao gerente para aceite/ajustes e
decisao de fechamento da F2. Nenhum merge autorizado ou executado.
A cabeca remota e a URL do PR serao identificadas na devolucao apos
publicar estes registros. O ultimo HEAD local observado e f2d1d11;
a sincronizacao das atualizacoes documentais posteriores deve ser feita
por fast-forward, sem presumir que ja ocorreu.

Joao executou as verificacoes e a recuperacao da instancia; assistente
preparou comandos, documentos e PR, e revisou as saidas recebidas.
Interpretacao independente nao foi verificada. Limites de motivos
historicos, concorrencia, papeis, portabilidade, documentos sinteticos
e funcionalidades futuras permanecem classificados nas secoes 4, 5 e 8.


## 11. Fechamento autorizado - VAL-F2-P04-001

**F2 FECHADA COM LIMITACOES em 20/10/2026.**
Autoridade: decisao central VAL-F2-P04-001, encaminhada expressamente por
Joao neste chat. R03/R04 aceitos no escopo demonstrado. Esta decisao
substitui os estados pendentes de fechamento nas secoes historicas acima.

| Fase | Estado central |
|---|---|
| F1 | Fechada documentalmente |
| F2 | Fechada com limitacoes |
| F3 | Aguarda passagem atualizada e primeiro cartao; pronta para recebe-lo, ainda nao iniciada |
| F4-F6 | Bloqueadas |

### Base, artefatos e evidencias

Base tecnica: 33ba8d02931883cc31d0312049587abae444e9ef.
Consolidacao anterior ao fechamento:
97a1637b46f099cf1c45112b3f2724d6aa87920e, sincronizada local/remoto por
fast-forward conforme saida de Joao; somente .vscode nao rastreada.
Atualizacao de fechamento: apenas README, plano 04 e este documento 15.
O commit publicado sera identificado na devolucao e no historico Git.

Evidencias aceitas ja registradas: ambiente/lock e reproducao local;
PostgreSQL dedicado e conexao segura; tres revisoes e ciclos reversiveis
no banco descartavel; 147 testes de integracao em 8.44s; 24 testes do
gerador e 11 subtestes em 0.84s; Ruff e 21 arquivos formatados; fixture,
sentinelas e hashes aprovados; duas geracoes reproduziveis de P03.
Nao houve repeticao de testes ou alteracao de codigo para este registro.
A decisao nao transforma expectativas de negocio em resultados executados.

### Limitacoes preservadas e responsabilidades futuras

- Reproducao de dependencias observada no mesmo Windows/Python/cache;
  instalacao limpa de sistema e portabilidade integral nao demonstradas.
- ilc_app e proprietario, sem equivaler a separacao de papeis de producao.
- Bloqueio de novos motivos em avaliacoes historicas finalizadas ainda
  depende da aplicacao; conferencia funcional nao implementada.
- Concorrencia de duas sessoes nao ensaiada; coordenacao operacional,
  locks/retry e regras de aceitacao ainda pertencem aos cartoes futuros.
- Documentos do gerador sao referencias JSON sinteticas, nao PDF/XML real.
  Volume maximo nao ensaiado; manifesto contem expectativas, nao aprovacoes.
- Banco ilc nao recebeu estas migracoes; ensaios ficaram em ilc_f2p02b_test.
- Backup/restauracao, CI/E2E, metricas, parser, API e ingestao nao entregues
  por este fechamento. Sem ganhos empresariais reais alegados.
- Participacao de Joao comprovada pelas edicoes/execucoes orientadas;
  explicacoes do assistente nao sao atribuidas como interpretacao independente.
- .vscode e configuracoes locais preservadas; limpezas historicas nao
  executadas continuam classificadas, sem apagar recursos neste registro.

### PR e proximo passo

PR #2: https://github.com/Soba-Jopeca/integrated-logistics-control/pull/2
Manter sem merge conforme autorizacao. O fechamento da fase e independente
da integracao a main; nao houve autorizacao de merge por esta decisao.

Fornecer esta passagem e o commit de fechamento para as fontes compartilhadas,
sem presumir atualizacao automatica. F3 pronta para receber o primeiro
cartao do gerente, ainda nao iniciada. F4-F6 bloqueadas. Nenhuma dependencia,
banco, API, ingestao ou parser novo iniciado por esta atualizacao.
