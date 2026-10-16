# 04 — Plano de execução e aprendizagem

Data-base: 16/10/2026. Meta: demonstração em 21/10/2026.
Estimativa inicial: 20–25 horas orientadas, ainda sem medição. Rever a estimativa ao final de cada sessão.

## Método

Problema → conceito → implementação pelo autor → validação → revisão → registro Git.

João implementa a solução e explica as decisões. A orientação técnica prepara documentação, ensina conceitos e revisa evidências. Uma etapa só é concluída com resultado observado; disponibilidade de tempo não elimina a necessidade de compreensão.

## Agenda proposta

| Data | Foco | Conceito praticado | Evidência |
|---|---|---|---|
| 16/10 | Documentação inicial e validação do negócio | Requisito vs solução | Ajustes do autor nas premissas |
| 17/10 | Contratos, ambiente, primeira ingestão e ensaio de IA | Granularidade, chaves e viabilidade | Primeiro lote pequeno persistido |
| 18/10 | API e ETL | Idempotência, transações e eventos atrasados | Reexecução e falha controlada |
| 19/10 | Documentos e conferência | Extração vs validação de negócio | Casos aprovado, pendente e divergente |
| 20/10 | Aplicação, agendamento e experimento LLM | Fluxo do utilizador e observabilidade | Navegação e execução rastreável |
| 21/10 | Power BI, integração e apresentação | Semântica, evidência e comunicação | Demonstração reproduzível |

Se houver atraso, reduzir interface, volume e extensões antes de eliminar integridade, testes essenciais ou documentação de limitações. OCR/RAG não bloqueiam o núcleo.

## Próxima atividade concreta

1. Ler documentos 01 e 02.
2. Validar ou ajustar os utilizadores e as três situações principais.
3. Explicar por que entrega física e aprovação documental têm estados diferentes.
4. Clonar o repositório no computador do autor.
5. Criar branch para definir contratos dos dados, antes de escrever ETL.

## Exercícios por perspectiva

- Estratégia: qual decisão justifica cada dado e cada indicador?
- Engenharia: o que acontece se o lote repetir ou falhar pela metade?
- Analytics Engineering: qual é a granularidade e onde a métrica é definida?
- Análise: uma variação representa problema de negócio ou dado ausente?
- Liderança técnica: qual alternativa foi descartada, por quê e quando revisitá-la?

## Preparação da apresentação

Demonstrar um caso correto, um divergente e uma reexecução. Explicar o problema, a arquitetura, uma escolha com trade-off e uma limitação. Separar resultados simulados de impacto real. Registrar evidências e roteiro ao final, sem antecipar funcionalidades entregues.
