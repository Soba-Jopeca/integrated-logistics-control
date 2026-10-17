# 08 — Consolidação F1 e proposta analítica

Data: 16/10/2026.
Passo: F1-P04.
Estado: em revisão; F1 aberta.
Implementação analítica: somente na F5.

## 1. Precedência e estado

Base mestre e Adendo v2 definem escopo e governança.
Validações centrais liberam cada passo.

Contrato: documento 06, commit 58a1ec3.
Modelo: documento 07, commit 8339239.
Proteção Git: commit 54fc765.

P01, P02, H01 e P03 aceitos conforme encaminhamento humano.
P04 ainda depende de validação.
Nenhum aceite documental comprova execução de software.
F2–F6 permanecem bloqueadas.

## 2. Arquitetura consolidada

CSV/API → origem preservada e staging → operacional PostgreSQL
→ conferência → Streamlit e camada SQL analítica → Power BI.

PDF/XML → armazenamento controlado → extração → conferência.

Auditoria transversal: origem, checksum, recebimento original,
tentativas, run_id, contagens e erros.

Camadas são responsabilidades lógicas, sem exigir cópias integrais.
Contrato e modelo não são implementação física.

Versões e compatibilidade serão verificadas na F2 antes da instalação.
Avaliação formal de IA pertence à F4, com baseline determinístico,
hardware/licença medidos, conjunto rotulado separado dos exemplos
do prompt, duas versões de prompt, schema, qualidade por campo/categoria,
invenções, falhas, latência e fallback.
Inviabilidade produz relatório, sem integração fictícia.

## 3. Modelo analítico proposto

### Fatos

| Fato | Grão e chave lógica | Conteúdo |
|---|---|---|
| F_ENTREGA_REFERENCIA | Uma delivery_key por reference_key | Conclusão selecionada, prazo, primeiro recebimento válido, situação física, regularidade, conflito e flags de elegibilidade |
| F_DOCUMENTO_REFERENCIA | Uma document_key vigente por reference_key | Família, entrega, avaliação selecionada, resultado, processamento e bloqueadores |
| F_AVALIACAO_HISTORICA | Uma evaluation_key | Resultado imutável, documento, versão das regras e horário |
| P_AVALIACAO_MOTIVO | Uma avaliação + código + campo afetado | Detalhamento de motivos; não é base direta para contar documentos |

reference_key identifica instante de corte e versão da publicação.
Publicações diferentes não são somadas como se fossem entidades distintas.

F_ENTREGA_REFERENCIA cobre entregas conhecidas até o corte.
F_DOCUMENTO_REFERENCIA cobre versões vigentes aceitas até o corte.
Fatos históricos e fotografias de referência têm finalidades distintas.

### Dimensões

| Dimensão | Chave e atributos |
|---|---|
| D_ENTREGA | delivery_key única; delivery_id e referência do pedido |
| D_DOCUMENTO | document_key única; document_id, family_key e version |
| D_DATA | date_key única; data local, mês e ano |
| D_REFERENCIA | reference_key única; corte UTC, publicação, regras e atualização |
| D_ORIGEM | source_system único; descrição |
| D_RESULTADO | result_key única; NOT_EVALUATED, APPROVED, REVIEW_REQUIRED |
| D_MOTIVO | reason_code único; descrição |
| D_REGRAS | rules_key única; versão das regras |

Datas desempenham papéis distintos: conclusão, prazo, recebimento
e avaliação. Timestamps UTC completos permanecem nos fatos.
No Power BI, usar dimensões por papel ou relações inativas explícitas,
evitando caminhos ambíguos.

Atributos mutáveis que alterem a interpretação histórica são preservados
na publicação ou recebem versionamento; não sobrescrever retrospectivamente
resultados de fotografias anteriores.

### Relações

- D_ENTREGA 1:N F_ENTREGA_REFERENCIA.
- D_ENTREGA 1:N F_DOCUMENTO_REFERENCIA.
- D_DOCUMENTO 1:N F_DOCUMENTO_REFERENCIA.
- D_DOCUMENTO 1:N F_AVALIACAO_HISTORICA.
- D_REFERENCIA 1:N para cada fato de referência.
- D_RESULTADO 1:N para fatos documentais/avaliações.
- D_ORIGEM 1:N para fatos de documentos e avaliações pela origem documental.
- Origem de evento não é presumida como origem da entrega.
- D_REGRAS 1:N para avaliações e publicações aplicáveis.
- F_AVALIACAO_HISTORICA 1:N P_AVALIACAO_MOTIVO.
- D_MOTIVO 1:N P_AVALIACAO_MOTIVO.

Filtros unidirecionais da dimensão para o fato.
Não relacionar diretamente os fatos de entrega e documento.
A relação da avaliação histórica com sua ponte de motivos é a exceção
explícita de detalhamento; não deve multiplicar métricas documentais.
Não criar filtro bidirecional automático.
Filtro por motivo em métricas documentais exige semijunção/conjunto
distinto explícito de avaliações, sem multiplicar documentos.
Campos dimensionais não aplicáveis usam membro desconhecido explícito;
timestamps ausentes permanecem nulos.

### Métricas

- M1 usa F_ENTREGA_REFERENCIA, uma referência selecionada,
  coorte por conclusão e flags de prazo válido/conflito.
- M2 usa F_ENTREGA_REFERENCIA e flag de existência de documento recebido.
- M3 usa F_DOCUMENTO_REFERENCIA, resultado REVIEW_REQUIRED.
- M4 usa intervalos elegíveis em F_ENTREGA_REFERENCIA.
- Percentuais e medianas são recalculados no contexto; não somar
  percentuais ou medianas previamente agregados.
- Não somar fotografias de cortes diferentes.
- Fatos são reduzidos ao grão antes de associar dimensões.
- Implementação SQL/DAX e reconciliação na mesma fixture pertencem à F5.

## 4. Matriz R01–R17

Definição documental não significa implementação comprovada.

| ID | Definição/artefato na F1 | Evidência futura exigida |
|---|---|---|
| R01 | Negócio, personas e decisões em 01; aceite P01 com aprendizagem autodeclarada | Sem alegação de explicação autoral independente |
| R02 | Contratos 06, relações/dicionário 07, proposta analítica 08 | Verificações visuais pendentes; integridade executável nas fases seguintes |
| R03 | Ambiente reproduzível previsto em 02/03/04 | F2: versões oficiais, isolamento, lock, .env.example, migração e rollback |
| R04 | Fixtures conceituais em 06/07 | F2: gerador com semente, pequenos casos esperados e volume configurável |
| R05 | API local simulada no escopo | F3: OpenAPI, paginação/cursor, timeout, HTTP/JSON inválidos e indisponibilidade |
| R06 | Origem/recebimentos/tentativas em 06/07 | F3: ingestão CSV/API, checksums, horários e contagens reconciliadas |
| R07 | Identidade, conflitos e histórico em 06/07 | F3: atraso, rollback, retomada, checkpoint pós-commit, quarentena e retry limitado |
| R08 | Campos e falhas de extração em 06 | F4: PDF textual/XML, ausência preservada e parsing rastreável |
| R09 | Conferência, motivos e vigência em 06/07 | F4: casos consistentes/divergentes, referência inválida e histórico executados |
| R10 | Experimento e limites definidos em 02/08 | F4: viabilidade medida, baseline, avaliação fixa, prompts e fallback ou relatório de inviabilidade |
| R11 | Jornada prevista em 02/03 | F5: busca/filtros, upload limitado, atualização visível e revisão auditável se incluída |
| R12 | Métricas 05 e fatos/dimensões 08 | F5: estrela implementada e quatro métricas SQL/DAX reconciliadas |
| R13 | Scheduler previsto em 03/04 | F6: histórico, sobreposição impedida e recuperação demonstrada |
| R14 | Estratégia de evidência prevista | Testes desde F2–F5; F6 consolida domínio/integração/E2E, Ruff/pytest e CI por PR com PostgreSQL isolado |
| R15 | Sintéticos, regras de upload/XML e .gitignore | F2–F6: segredos externos, menor privilégio, portas locais, SQL parametrizado, proteção de caminho/tipo/tamanho e logs sem segredos |
| R16 | Reprodução prevista em README/02 | F6: instalação limpa, dependências fixadas, migrações, backup/restauração e rollback de release |
| R17 | Arquitetura, decisões e roteiro previstos | F6: ADRs completos, demo, capturas, resultados sintéticos medidos e release |

AC01–AC11 do documento 02 são critérios resumidos de demonstração;
não substituem R01–R17.

## 5. Evidências e verificações

| Item | Estado observado |
|---|---|
| Contratos | Commit 92202af e ajustes 58a1ec3 publicados |
| Proteção inicial Git | 54fc765 publicado; regras verificadas |
| Modelo conceitual/lógico | 8339239 publicado |
| Fixtures A/B/C | Inspeção documental; sem execução |
| Três diagramas Mermaid | Conferência visual ainda pendente |
| Consolidação P04 | Aguardando aplicação, diff, commit e publicação |
| Software/banco/ETL | Não implementados na F1 |

O commit de P04 será registrado na passagem após sua criação.
Não inserir antecipadamente hash ou resultado de comando.

## 6. Participação, aprendizagem e tempo

João aplicou documentos, correções de relações e executou verificações,
commits e publicações apresentados nas evidências.

O assistente elaborou propostas e justificativas.
Decisões recomendadas foram adotadas por instrução de João.
Não houve explicação autoral independente registrada em P02/P03.
P01 foi aceito com aprendizagem autodeclarada.

Conceitos trabalhados:
grão, identidade, reenvio/conflito, estados independentes,
família/versão, vigência, extração/avaliação e recebimento/tentativa.

Tempo dedicado: não medido.
Não converter intervalo entre mensagens em esforço trabalhado.

## 7. Pendências e passagem

Antes de solicitar fechamento:
- Conferir visualmente os três diagramas.
- Revisar a consolidação e suas relações analíticas.
- Verificar diff e registrar commit/push.
- Registrar resultados observados e limitações.
- Levar artefatos e passagem ao gerente.
- Atualizar a fonte compartilhada na transição, após decisão central,
  sem presumir sincronização automática.

F1 continua aberta.
F2–F6 bloqueadas.
Nenhuma instalação, .env, ambiente virtual, banco ou ETL iniciado.
