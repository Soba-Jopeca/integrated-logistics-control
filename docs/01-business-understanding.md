# 01 — Entendimento do negócio

Estado: proposta inicial para validação com o autor. Data: 16/10/2026.

## Pessoas, necessidades e decisões

| Pessoa simulada | Necessidade | Decisão apoiada |
|---|---|---|
| Analista operacional | Localizar pendências e entender seu motivo | Qual entrega investigar e qual informação solicitar |
| Coordenador | Entender volume e envelhecimento das pendências | Onde concentrar esforço de regularização |
| Responsável técnico | Distinguir problema operacional de falha de ingestão | Reprocessar dados ou encaminhar uma pendência ao negócio |

## Hipótese do problema

Informações distribuídas entre pedidos, eventos e comprovantes dificultam conciliar a situação física com a documental. Essa hipótese pertence ao cenário educacional; não é um diagnóstico da empresa.

## Fluxo operacional proposto

Pedido liberado → eventos de transporte → entrega registrada → comprovante recebido → extração → conferência → aprovação ou revisão.

O comprovante pode chegar antes ou depois do evento de entrega. Ausência de evento não prova ausência de entrega; a interface deve apresentar a informação disponível e sua atualização.

## Perguntas a responder

- Quais entregas registradas como concluídas ainda não têm comprovante?
- Quais documentos divergem dos dados da entrega e por quê?
- Há dados desatualizados ou falha no pipeline?
- Quais pendências estão há mais tempo sem regularização?
- Como as ocorrências textuais podem ser estruturadas com qualidade mensurável?

## Premissas consolidadas na F1

- Pedido representa solicitação; entrega representa execução.
- Na v1, um pedido admite zero ou uma entrega; cada entrega pertence a um pedido.
- Uma entrega admite vários eventos e famílias documentais.
- Cada família possui versões imutáveis e uma versão vigente.
- Regularidade exige ao menos uma versão vigente aprovada e nenhuma vigente pendente.
- Conflito de conclusão impede usar uma aprovação dependente do horário contestado.
- Entrega física e regularidade documental são independentes.
- Documento recebido ou extraído não é automaticamente aprovado.
- Ausência de evento não prova ausência de entrega.
- Referência desconhecida fica recuperável, sem criar vínculo fictício.
- Datas persistidas em UTC; exibição em America/Sao_Paulo.
- XML educacional, sem conformidade fiscal alegada.
- Dados e resultados são sintéticos; nenhum ganho empresarial real foi medido.

## Decisões detalhadas

Campos, estados, reenvios, conflitos e substituições:
[contratos](06-event-and-document-contracts.md).

Relações, chaves, histórico e grãos:
[modelo conceitual e lógico](07-conceptual-and-logical-model.md).

Na operação simulada, o analista investiga divergências e solicita correções;
o coordenador prioriza e encaminha casos sem resolução;
o responsável técnico trata ingestão, parsing e reprocessamento.
Esses papéis não representam uma estrutura empresarial real.

Frequência de atualização será definida e medida na operação.
Até lá, apresentar horário da última atualização, sem prometer latência.
Sem SLA documental validado: apresentar tempo decorrido.

## Participação e estado

F1-P01 aceito pela gestão com aprendizagem autodeclarada.
Respostas conceituais preparadas pelo assistente e adotadas por João;
explicação autoral independente não foi verificada.
F1 permanece aberta até avaliação central do conjunto.
