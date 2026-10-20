# F2-P04 - Consolidacao verificavel da F2

Data: 19/10/2026. Branch de consolidacao: docs/f2-p04-consolidation.
Entrada aceita: 33ba8d02931883cc31d0312049587abae444e9ef.
Autoridade: cartao F2-P04 encaminhado por Joao, com P01, P02A-D e P03
aceitos centralmente com limitacoes. Nao foram fornecidos IDs adicionais
de validacao; nenhum foi inventado.

**Estado: P04 em consolidacao, verificacao final pendente, F2 aberta.**
F3-F6 bloqueadas. PR para revisao, sem autorizacao de merge neste cartao.

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
nao rastreada. Estado P04 local ainda deve ser reconferido por Joao.
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
| R03 | Parcial no estado central atual; ambiente/lock/conexao/migracoes reversiveis comprovados no ambiente local, com limites de portabilidade |
| R04 | Gerador e fixtures apresentados e P03 aceito com limitacoes; consolidacao do requisito depende da decisao central de P04 |
| R05 | API/OpenAPI/paginacao/falhas: F3, nao implementado |
| R06 | Ingestao CSV/API e reconciliacao: F3, nao implementado |
| R07 | Idempotencia, conflitos, retomada e quarentena operacionais: F3, nao implementado; existem estruturas e entradas de teste |
| R08 | PDF/XML real e parsing protegido: F4, nao implementado |
| R09 | Conferencia funcional e reavaliacao: F4, nao implementado; estrutura nao equivale a regra de negocio executada |
| R10 | Experimento IA e viabilidade: F4, nao executado |
| R11 | Aplicacao de consulta/upload: F5, nao implementado |
| R12 | Metricas SQL/DAX e Power BI: F5, nao implementado |
| R13 | Scheduler e recuperacao operacional: F6, nao implementado |
| R14 | Testes e Ruff observados por passo; revalidacao conjunta P04 pendente; CI/PostgreSQL isolado/E2E permanecem para F6 |
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

## 7. Verificacao final P04 - ainda pendente

| Item | Esperado | Observado nesta preparacao |
|---|---|---|
| Git local | Branch P04, base/documentacao corretas; .vscode preservada | Aguardando saida de Joao |
| Ambiente | Venv aceita, pip check sem conflitos; versoes/lock reconferidos | Aguardando |
| Ruff check e format --check | Sem erros no conjunto scripts/migrations/tests | Aguardando |
| Testes do gerador | 24 testes; subtestes reportados separadamente | Aguardando |
| Catalogo descartavel | 0003_decisions_conflicts, 19 tabelas, btree_gist 1.8 | Aguardando |
| Integracao | 147 testes aprovados, sem downgrade | Aguardando |
| Fixture pequena | Inventario, contagens e hashes aprovados | Aguardando |
| Conexao anterior/sentinelas | PASS, sem segredos e sem alterar dados anteriores | Aguardando |
| PR | Rascunho revisavel para main, sem merge | PR #2 aberto em draft; verificacao inicial clean, conforme secao 9 |

Comandos de ambiente, conexao, migracoes e geracao no README foram
executados nos passos anteriores. Sua reuniao no README nao comprova
uma instalacao limpa nova. Em P04 usar venv e instancia existentes.
Nao instalar ou atualizar dependencias, iniciar banco novo ou repetir
downgrade para preencher esta tabela.

## 8. Pendencias classificadas e passagem

**Para decisao de fechamento P04:** receber verificacao final local;
conferir estado/URL do PR e diff; publicar registro observado e devolver ao
gerente. Falha de verificacao e bloqueadora ate revisao e correcao.
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

Esta atualizacao registra apenas a preparacao do PR. Verificacao final
no Windows ainda pendente; resultado anterior nao foi reciclado como P04.
