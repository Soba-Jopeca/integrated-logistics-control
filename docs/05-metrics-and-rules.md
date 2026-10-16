# 05 — Métricas e regras propostas

Estado: definições iniciais para validação antes de implementar.
Toda consulta deve declarar período, instante de referência, fuso e atualização dos dados. Contar entregas distintas, evitando multiplicação por eventos ou documentos.

## Indicadores

| Métrica | Definição inicial | Tratamento de exceções |
|---|---|---|
| Entregas concluídas no prazo (%) | Entregas concluídas com horário efetivo ≤ prazo prometido / concluídas com ambos os horários válidos × 100 | Coorte pelo horário efetivo no período; nulos fora do denominador e exibidos separadamente; denominador zero retorna sem dado |
| Entregas aguardando comprovante | Entregas concluídas até o instante de referência sem documento recebido vinculado | Documento recebido mas rejeitado não é ausência; é pendência por divergência |
| Documentos com divergência | Documentos distintos com resultado vigente divergente/revisão no instante de referência | Documento com vários motivos conta uma vez; manter detalhamento dos motivos |
| Tempo entrega → comprovante | Mediana das horas entre conclusão e primeiro recebimento válido de comprovante, para concluídas no período | Excluir horários ausentes; intervalo negativo sinaliza revisão; mostrar quantidade elegível e quantidade excluída |

Prazo de transporte e prazo de regularização documental são conceitos diferentes. Nenhuma meta percentual ou SLA documental foi validado.

## Regras iniciais

- Comprovante recebido não implica comprovante aprovado.
- Documento aprovado precisa de referência existente e campos obrigatórios consistentes, definidos no contrato.
- Referência inexistente, campo ausente e valor divergente têm motivos distintos.
- Falha de parsing não deve criar valores por suposição.
- Ausência de comprovante não altera a entrega física para não entregue.
- Reprocessamento mantém o mesmo resultado lógico para a mesma versão da entrada e das regras.
- Toda revisão manual deve preservar resultado anterior, autor, data e motivo; a implementação desse histórico será dimensionada antes da interface.
- Revisão humana nunca deve ser apresentada como resultado automático do LLM.

## Cenários mínimos para validar

1. Entrega e comprovante consistentes.
2. Entrega concluída sem documento.
3. Documento recebido com referência inexistente.
4. Documento com campo obrigatório ausente.
5. Documento e evento repetidos.
6. Evento atrasado.
7. API indisponível ou JSON inválido.
8. Nenhuma entrega elegível para cálculo percentual.
9. Duas versões do documento para a mesma entrega sem duplicar o indicador de entregas.

## Pendências

Definir campos de comparação, regra de correção/cancelamento de eventos, seleção da versão vigente do documento e frequência de atualização antes de implementar. Validar manualmente um conjunto pequeno, com resultado esperado, antes de gerar volume.
