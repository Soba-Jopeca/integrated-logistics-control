# 25 — F4-P04: consolidação para avaliação de fechamento

03/11/2026. **F4 ABERTA — CONSOLIDAÇÃO ENTREGUE PARA DECISÃO CENTRAL.**
P04 não concede aceite próprio nem fecha a fase. F5–F6 não liberadas.
Repositório: Soba-Jopeca/integrated-logistics-control.
Branch documental: docs/f4-p04-consolidation, criada da base
ce875cf525cebd61d23bb1fc1998bb4630a437e0. Sem merge ou alteração técnica.

## Autoridade e aceites registrados

Cartão humano F4-P04 encaminhado por João neste chat autoriza consolidar,
registrar **VAL-F4-P03-001** e reutilizar provas aprovadas.
João acrescentou: **“o que depender de mim pode executar que estamos sem tempo”**.
Isso delega a conferência Git/consulta existente deste cartão ao assistente;
não converte ações do assistente em prática ou explicação independente de João.
Não implica autorização para fechar fase, integrar IA ou iniciar F5.

| Passo | Aceite central recebido | Código | Evidência/passagem |
|---|---|---|---|
| F4-P01 | VAL-F4-P01-001 | 787f327 | docs/22; 80dec06 |
| F4-P02 | VAL-F4-P02-001 | b88f88a | docs/23; f34ec23 |
| F4-P03 | VAL-F4-P03-001 | harness 947cbbd; prompt 4623f35 | docs/24; bruto/relatório b1e2121; passagem ce875cf |
| F4-P04 | entregue para avaliação; sem ID de aceite inventado | somente documentação | presente passagem e SHA final de publicação |

Esses aceites têm o escopo e limites demonstrados. F1/F2/F3 conservam seus
fechamentos anteriores, inclusive VAL-F3-P04-001 com limitações. Nenhum estado
posterior foi inferido da memória ou do sucesso de testes.

## Decisão técnica consolidada

**Baseline determinístico é o padrão. IA permanece experimento isolado;
nenhuma aprovação documental é feita por IA.** O experimento mostrou execução
local e ganho nos dois textos irregulares, mas ambos os prompts inventaram
ADMIN no recebedor ausente após comando malicioso. V2 não melhorou a qualidade.
Schema válido não garante fidelidade; fallback estrutural não detectou esse erro.
Não integrar respostas LLM às regras, avaliações, estado físico ou banco.
R10 é atendido pelo experimento e decisão fundamentada, não por integração fictícia
nem alegação de inviabilidade de hardware após execução real bem-sucedida.

## R08–R10: esperado × observado

| Requisito/cenário | Esperado | Observado e fonte |
|---|---|---|
| R08: PDF textual e XML reais | cinco campos, UTC, origem/hash/bytes/run/parser rastreáveis | P01 23 testes em 0,29 s/exit0 e verificador SQL PASS/exit0; docs/22 |
| R08: campo ausente | null sem inferir | receiver_name=null em PDF/XML; missing_fields distinto de falha de parsing |
| R08: falhas | motivos próprios e histórico | NO_EXTRACTABLE_TEXT, PARSING_ERROR, XML_SECURITY_BLOCKED, FILE_MISSING, UNSUPPORTED_FORMAT |
| R08: reenvio | mesma versão/input, nova extração/tentativa | oito versões P01; 16 extrações reportadas nos oito pares |
| R08/R15: bytes | hash e preservação corretos | correção de CRLF em PDF; comparação byte a byte com HEAD e SHA256; sem relaxar strict=True |
| R09: consistente | aprovação só se coerente | A1 APPROVED; mesmo minuto UTC descarta segundos/frações, sem tolerância adicional |
| R09: divergência/ausência | motivos específicos | quantidade/unidade/horário VALUE_MISMATCH; receiver_name MISSING_REQUIRED_FIELD |
| R09: referência | sem vínculo fictício | envelope desconhecido INVALID_REFERENCE em tentativa; referência extraída diferente REFERENCE_MISMATCH em avaliação |
| R09: parsing e conclusão | não aprovar | PARSING_ERROR; NO_ELIGIBLE_COMPLETION ou COMPLETION_CONTESTED, ambos sob DELIVERY_NOT_CONFIRMED com detalhes distintos |
| R09: A/B | A aprovado não encobre B divergente | A1 regular → A1+B1 pendente → B2 corrigido/avaliado regular → A2 com parsing falho pendente |
| R09: substituição | vigência linear e avaliação própria | A1/B1 não vigentes; A2/B2 vigentes; ausência de aprovação herdada conferida antes de avaliar; salto B4 rejeitado |
| R09: histórico | avaliações anteriores preservadas | consulta read-only de João, exit0, avaliações 1/2 nas dez versões; zero sobreposições |
| R09: física independente | avaliação não altera entrega/eventos | physical_and_p01_preserved=true no recorte de snapshot do verificador; contestada continua DELIVERED |
| R10: viabilidade | tentativa local fundamentada | Windows/i7/16 GB, RAM livre 0,65→3,01→4,63GiB; Ollama 0.40.13/Qwen 1.5B Q4_K_M; smoke e 16 chamadas reais |
| R10: avaliação fixa | baseline/V1/V2, exemplo separado | oito documentos/40 campos; 24 linhas por método/caso; rótulos nunca enviados ao modelo |
| R10: ausências/invenção | medir sem ocultar falha | baseline12/12 ausências; V1/V2 11/12; ambos ADMIN em E04 |
| R10: falhas/fallback | rejeitar inválido e usar baseline explicitamente | testes controlados de schema/tipos/timeout/indisponibilidade/HTTP; zero fallbacks no ensaio real |
| R10: rastreabilidade | runtime/digest/prompts/opções/tempos/bruto | resultado bruto integral, sete hashes dos inputs conferidos e métricas recalculadas; docs/24 e report.md |

## Contagens e medições, sem somas indevidas

- P01: oito versões documentais e 16 extrações reportadas na prova; não é
  contagem global de todos os documentos do banco após P02.
- P02: dez versões documentais próprias, sete entregas sintéticas de referência,
  avaliações 1/2 preservadas (20 linhas na consulta sem motivos múltiplos
  nesses casos), zero sobreposições. Estado final A/B: dois comprovantes vigentes,
  um aprovado e um pendente; situação física DELIVERED, regular=false.
- Testes acumulados: P01 23; P02 40=23+17; P03 63=40+23 do harness.
  Última prova Windows P03: **63 passed in 1.12s, exit0**, Ruff aprovado.
  Não somar 23+40+63 como casos distintos nem misturar com os 98 da F3.
- IA: oito baseline e oito chamadas por prompt. Baseline30/40 campos (75%),
  6/8 documentos exatos; V1/V2 39/40 (97,5%), 7/8 documentos exatos.
  Por campo: baseline 6/8 em cada; prompts 8/8 nos quatro primeiros e 7/8 no nome.
- Texto irregular: baseline 0/10; V1/V2 10/10. Injeção: baseline 5/5; V1/V2 4/5.
  Demais categorias e contagens completas em report.md e results.json.
- Mediana cliente: baseline 0,00017435s; V1 5,1393s; V2 5,2786s.
  Janela started_at→finished_at 85,116038s. Smoke separado: API 6,1260437s,
  load 1,3286339s, sem tempo cliente válido pelo erro de envio do finally.
- Esforço humano por etapa e total **NÃO MEDIDO**. Duração de teste, inferência
  ou janela de execução não é esforço humano. Não atualizar prazo com estimativa
  fictícia ou reaproveitar 20–25h como medição.

## Conferência P04 delegada, somente leitura

No ambiente do assistente, o checkout anterior estava em df690e7 (preparação
local com árvore equivalente a 947cbbd) e tinha report.md/evidence não rastreados.
Foi preservado integralmente. Criado worktree separado docs/f4-p04-consolidation
na base ce875cf, sem reset, clean, stash ou sobrescrita da configuração local.
Fetch observou origin/feat/f4-p03-local-ai-experiment=ce875cf e comparação
base...origin **0 0**. Worktree documental inicialmente limpo.
Isso é conferência local/remota deste ambiente, não nova verificação do Windows.

Última prova Windows permanece a de João em 4623f35: HEAD=origin/0 0,
apenas .vscode/ não rastreado. Não presumir que o Windows já incorporou ce875cf
ou a presente publicação; sincronização documental não exige repetir provas.

Consulta existente, sem executar LLM/SQL ou carga: leitura de results.json
versionado confirmou run ai-20261103T080004Z-935939ad-9159-4653-8efb-24c92a0ca05e,
24 linhas, E04 baseline.receiver_name=null e V1/V2.receiver_name=ADMIN,
fallback=false. Sete hashes coincidem com arquivos efetivamente commitados,
inclusive V2 de4623f35. SHA256 bruto:
178051696580d361ef44fed92d638f3b912ce42ba6aceb352afcc1d9ee026c84.
4623f35 confirmado ancestral da base. Raw CRLF preservado por atributo -text.

Autoria P04: essas consultas e checagem Git foram executadas pelo assistente,
por delegação explícita. Nenhuma nova prática independente foi atribuída a João.
A edição central, execuções, consultas SQL e prompt das etapas P01–P03 continuam
com autoria/prática de João conforme provas anteriores. Explicação independente
segue adiada para revisão final, sem alegar conclusão.

## Comandos conferidos contra código, não reexecutados em P04

Os comandos abaixo são referência de reprodução dos passos aceitos; escritas
não fazem parte de P04. Mantido test_engine explícito para ilc_f2p02b_test,
DB_HOST 127.0.0.1/DB_PORT 55432/DB_USER ilc_app e DB_NAME ilc na configuração
existente; não imprimir credenciais ou mudar alvo. Revisão exigida 0006_reliability.

| Comando | Conferência estática |
|---|---|
| python -m scripts.document_extract --database ilc_f2p02b_test --file CAMINHO --envelope ENVELOPE_JSON | argumentos --database/--file/--envelope existem; CLI0 SUCCEEDED,1 falha; erro de uso argparse pode sair2 |
| python -m scripts.check_document_extraction --database ilc_f2p02b_test | argumento existe; saída final PASS após asserts; repetição cria novas tentativas/extrações, não executar em P04 |
| python -m scripts.check_document_validation --database ilc_f2p02b_test | argumento existe; semeia referências próprias e escreve avaliações; não executar em P04 |
| python -m experiments.local_ai.runner | módulo/main presentes; output-root padrão data/experiments/local_ai; 16 chamadas sequenciais/zero retry |
| python -m experiments.local_ai.runner --output-root CAMINHO | argumento existe; pasta UUID nova; output ignorado por padrão; não sobrescreve run anterior |
| python -m ruff check experiments/local_ai tests/ai | caminhos existem; Ruff executado em P03, não repetido por documentação |
| python -m pytest -q tests/ai tests/documents | caminhos e 63 casos anteriores; testes controlados não são medidas de LLM |

Verificação CLI por AST confirmou os conjuntos de argumentos acima. Leitura do
runner confirma versão 0.40.13/digest fixo, endpoint loopback sem proxy, schema,
opções e descarregamento no finally; erro de unload é reportado, não prova
observada de memória liberada. Não houve nova instalação/dependência/migração.
Comandos SQL read-only de22/23 conferidos estaticamente contra tabelas/joins;
a consulta do histórico P02 já foi executada por João e foi reutilizada.

## Limitações preservadas e fronteira de aceite

Case educacional sintético/local, não operação empresarial. Parsing de formato
fechado; XML educacional sem conformidade fiscal; sem OCR. Upload/UI não incluídos.
Quotas/arquivos sem prova concorrente, verificação de stream PDF após descompressão,
sem sandbox completo de memória/tempo e possível arquivo órfão após rollback.

P02 distingue referência não resolvida antes da avaliação por integridade
referencial; não inventa documento/entrega para criar avaliação. Reenvios foram
exercitados; replay integral P02 e conflito documental de identidade não tiveram
nova prova dedicada. Snapshot P02 não cobre todas as tabelas: consulta as tabelas
físicas após semente própria, além de versões/extrações P01. Sem resolver conflitos
automaticamente ou provar concorrência real.

IA: oito textos, uma execução, uma configuração, sem variância ou generalização
estatística; CPU solicitado sem telemetria de pico/backend. Datas por instante UTC
na extração, comparação de negócio por minuto UTC em P02. Semente/temperatura0
não garantem reprodução bit a bit entre plataformas. Timeout de socket não é
deadline global. Fallback estrutural não rejeita toda invenção semântica.
Exceções forçadas são testes controlados, não falhas reais do Ollama neste run.
Sem alegar economia, aplicação produtiva ou melhoria comprovada fora do conjunto.

P04 não repete regressão global, inferência, cargas, CI/E2E, instalação limpa,
backup/restauração ou testes operacionais de F6. Sem mudança de código ou regra.
Aceites P01/P02/P03 preservam essas limitações. R15 permanece transversal parcial.

## Devolução ao gerente

Feito: aceites registrados, R08–R10 consolidados, comandos conferidos,
relatório atualizado quanto à publicação do prompt; README/plano e histórico
alinhados. Evidências e commits relacionados acima; SHA documental final
acompanha a entrega, sem inventar hash auto-referente no conteúdo.

Aprendizagem: prática anterior observada de João e conferência P04 delegada
explicitamente discriminadas. Explicação independente adiada. Esforço não medido.
Pendência de governança: gerente decidir **fechamento da F4 ou ajustes**,
considerando os limites e a explicação independente adiada. Executor não fecha.
Próximo passo único: levar esta passagem e commit final ao chat 00. Sem envio
automático de mensagem, merge, integração de IA ou início de F5.
