# 05 — Métricas e regras propostas

Estado: definições documentais consolidadas para avaliação de F1-P04.
Implementação e reconciliação SQL/DAX pertencem à F5.

## Convenções

Declarar período [início, fim), instante de referência, fuso,
atualização e versão das regras.
Interpretar limites de período em America/Sao_Paulo e converter para UTC.
Contar no grão correto antes de agregar.

## Indicadores

| ID | Grão e definição | Exceções |
|---|---|---|
| M1 | Uma entrega: concluídas no período com efetivo <= prometido / concluídas com ambos válidos × 100 | Nulos e conflitos de conclusão excluídos e contados; zero elegíveis = sem dado |
| M2 | Uma entrega concluída até a referência sem documento recebido vinculado | Divergência ou falha de parsing em documento recebido vinculado não significa ausência; referência não resolvida não é vínculo |
| M3 | Uma versão documental vigente com avaliação selecionada REVIEW_REQUIRED na referência | Vários motivos contam uma vez; substituídas excluídas; não avaliadas separadas |
| M4 | Uma entrega concluída no período: mediana das horas entre conclusão e primeiro recebimento válido | Excluir e contar ausentes, intervalos negativos e conflitos de conclusão |

## Recebimento válido

Arquivo aceito estruturalmente, vinculado a entrega existente
e sem conflito de identidade. Não exige aprovação documental.

Usar received_at original, inclusive após resolução tardia do vínculo.
Uma versão posteriormente substituída pode ser o primeiro recebimento válido.
Não usar horário de extração, aprovação ou última tentativa.

## Estados, identidade e histórico

- Regularidade: ao menos uma versão vigente aprovada e nenhuma vigente pendente.
- Conflito de conclusão bloqueia regularidade dependente do horário.
- Recebido e extraído não significam aprovado.
- Situação documental não regride situação física.
- Reenvio idêntico não duplica; mesma identidade com outro conteúdo gera conflito.
- Conclusões alternativas preservadas; primeira aceita permanece provisória.
- M1/M4 excluem conclusão contestada; M2 mantém a entrega concluída.
- Revisões preservam resultado anterior, autor, horário e motivo.
- IA não aprova documentos nem inventa campos ausentes.
- Reavaliação só reproduz resultado sob mesmos dados de referência,
  entrada, extração e versão das regras; mudança desses insumos é rastreada.

## Referência histórica

Considerar somente dados, vínculos e decisões conhecidos até a referência.
Resolução posterior não deve aparecer como conhecida antes de ocorrer.
Usar intervalos de vigência e histórico de aceitação/decisão.

## Fixtures e verificação

As fixtures A/B e o cenário de conclusões conflitantes estão nos
documentos 06/07. São exemplos documentais, ainda não executados.
O modelo analítico proposto está no documento 08.

Campos de comparação, vigência e conflitos estão definidos em 06/07.
Correção/cancelamento automático de conclusão não integra a v1.
Frequência de atualização permanece pendente da fase operacional.
Nenhuma meta percentual ou SLA documental foi validado.
