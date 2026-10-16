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

## Premissas propostas

- Um pedido corresponde a uma entrega nesta primeira versão.
- Uma entrega pode ter vários eventos e vários documentos.
- Somente documento aprovado atende à regularidade documental.
- Documento extraído ainda não é documento aprovado.
- XML é um contrato simplificado próprio, sem alegar conformidade fiscal.
- Valores e volumes gerados não representam a operação real.
- Datas são armazenadas com referência temporal explícita; exibição em America/Sao_Paulo.

## Perguntas pendentes antes do contrato dos dados

1. Quais campos mínimos permitem conciliar um comprovante?
2. Qual evento define conclusão e como uma correção posterior é representada?
3. Qual tempo de atualização é útil à decisão operacional?
4. Quem resolve cada motivo de divergência?
5. Há prazo de regularização? Até validação, mostrar tempo decorrido sem classificá-lo como violação de SLA.

## Exercício do autor

Explicar com suas palavras: quem decide, o que decide, quais dados precisa e o que acontece se a informação estiver errada. Registrar ajustes neste documento antes de implementar regras.
