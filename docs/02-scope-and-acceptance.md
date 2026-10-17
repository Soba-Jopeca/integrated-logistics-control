# 02 — Escopo e critérios de aceite

Estado: planejado. Nenhum critério está comprovado nesta versão.

## Núcleo da demonstração

| ID | Entrega | Critério de aceite |
|---|---|---|
| AC01 | Dados sintéticos | Geração reproduzível com casos esperados conhecidos e sem dados pessoais reais |
| AC02 | Ingestão Python/SQL | Pedidos e eventos rastreáveis à origem; contagens de leitura e destino reconciliadas |
| AC03 | REST local | Consumir eventos com timeout; resposta inválida e indisponibilidade produzem falha observável |
| AC04 | Idempotência | Reprocessar a mesma entrada não duplica pedidos, eventos ou documentos |
| AC05 | Documentos | Extrair campos definidos de um PDF textual e de um XML educacional; campo ausente permanece ausente |
| AC06 | Conferência | Caso consistente aprovado; documento ausente identificado; referência inexistente e divergência explicadas |
| AC07 | Aplicação web | Consultar entrega e pendências, carregar documento e visualizar resultado/motivo |
| AC08 | Monitoramento | Execução com run_id, horários, status, contagens e erro; falha não aparece como sucesso |
| AC09 | Agendamento | Uma execução acionada pelo agendador local, com evidência do resultado |
| AC10 | Analytics | Uma página Power BI com quatro métricas reconciliadas com consultas SQL |
| AC11 | Reprodutibilidade | Outra execução possível pelo README, com versões e configuração documentadas |

## Experimento de IA

Avaliação técnica no início: modelo local, licença do modelo, espaço disponível, latência e qualidade. Não presumir que 16 GB de RAM asseguram desempenho adequado.

Se viável: conjunto fixo de ocorrências sintéticas com respostas esperadas, prompt versionado, resultado estruturado validado e registro de erros/latência. Campo ausente não deve ser inventado. Comparar pelo menos duas versões do prompt sem alterar o conjunto de avaliação.

O resultado da IA não autoriza aprovação documental. Falha ou indisponibilidade deve ficar explícita. Se inviável no prazo, registrar a limitação e manter a demonstração funcional; não apresentar simulação como chamada real a LLM.

## Extensões condicionais

OCR em imagem, após concluir o fluxo com PDF textual/XML. E-mails, RAG, banco vetorial, nuvem, autenticação de produção e integração real com ERP/WMS ficam fora da entrega inicial.

## Relação com a vaga

- Requisitos e negócio: documento 01 e critérios deste documento.
- Python web, ETL, REST e agendamento: AC02, AC03, AC07–AC09.
- Documentos e inconsistências: AC05–AC06.
- LLMs/prompts: experimento avaliado, com limitações explícitas.
- KPIs, Power BI e documentação: AC10–AC11 e documento 05.
- Git: CONTRIBUTING.md.
- Docker/Linux: opcionais para execução local; não alegar implementação antes de validar.
- Power Platform, comércio exterior e sustentação de dashboards existentes: não demonstrados diretamente por este case.

## Evidências necessárias

Registrar entrada, resultado esperado, resultado observado, comando/consulta e commit para cada validação relevante. Testar falhas e reexecução, além do caminho de sucesso. Nenhum teste de software ou de integração foi executado nesta etapa documental.

## Consolidação F1-P04

Os aceites AC01–AC11 acima são futuros aceites de software,
não comprovados pela documentação.
A matriz completa R01–R17 está no documento 08.

O experimento formal de IA pertence à F4.
Diagnóstico e compatibilidade do ambiente pertencem à F2.
Testes começam nas fases de implementação; CI é consolidada na F6.

Documento recebido vinculado com divergência ou falha de parsing
não é documento ausente. Referência ainda não resolvida permanece
pendente, sem vínculo presumido.

Contratos 06 e modelo 07 detalham identidade, estados e histórico.
A F1 permanece aberta até avaliação central do conjunto.