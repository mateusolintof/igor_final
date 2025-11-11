# Guia de Parâmetros LLM (n8n)

Objetivo: respostas humanas, curtas e adaptativas, com mínima robotização. Estes parâmetros foram aplicados diretamente aos nós `OpenAI Chat Model` nos workflows IGOR_* via API do n8n.

## Conceitos-chave
- `temperature`: variação de estilo (0 = determinístico; 0.6–0.7 = mais natural).
- `frequencyPenalty`: reduz muletas e repetições.
- `presencePenalty`: incentiva tópicos novos (mantemos baixo).
- `topP`: amostragem por núcleo; 0.9–1.0 mantém vocabulário variado.
- `maxTokens`: principal freio de tamanho das respostas.

## Padrões por Agente
- Orquestrador (IGOR_01_Fluxo_Orquestrador)
  - temperature: 0.25
  - topP: 1.0
  - frequencyPenalty: 0.2
  - presencePenalty: 0.0
  - maxTokens: 120
- Acolhimento (IGOR_02.3_ACOLHIMENTO)
  - temperature: 0.5
  - topP: 0.95
  - frequencyPenalty: 0.5
  - presencePenalty: 0.2
  - maxTokens: 80
- Qualificação (IGOR_02.1_QUALIFICACAO)
  - temperature: 0.65
  - topP: 0.95
  - frequencyPenalty: 0.5
  - presencePenalty: 0.3
  - maxTokens: 140
- Objeções/Valores (IGOR_02.5_OBJECAO)
  - temperature: 0.7
  - topP: 0.9
  - frequencyPenalty: 0.6
  - presencePenalty: 0.2
  - maxTokens: 150
- Agendamento (IGOR_02.2_AGENDAMENTO)
  - temperature: 0.35
  - topP: 0.95
  - frequencyPenalty: 0.4
  - presencePenalty: 0.0
  - maxTokens: 100
- Escalação/Compliance (IGOR_02.4_ESCALACAO)
  - temperature: 0.3
  - topP: 0.95
  - frequencyPenalty: 0.4
  - presencePenalty: 0.0
  - maxTokens: 80
- Nutrição (IGOR_02.6_NUTRICAO)
  - temperature: 0.65
  - topP: 0.95
  - frequencyPenalty: 0.5
  - presencePenalty: 0.2
  - maxTokens: 150
- Atualização de Campos (IGOR_02_Agente_Atualização de campos)
  - temperature: 0.3
  - topP: 1.0
  - frequencyPenalty: 0.2
  - presencePenalty: 0.0
  - maxTokens: 100

## Ajuste fino rápido
- Respostas longas → reduza `maxTokens` em 20–30.
- Respostas frias/engessadas → +0.05–0.1 em `temperature` do agente específico.
- Repetições (“Perfeito…”, “Entendo…”) → +0.1 em `frequencyPenalty` no agente específico.

## Observações
- Mantivemos o mesmo modelo configurado em cada fluxo; os parâmetros acima foram setados em `parameters.options` do nó `OpenAI Chat Model`.
- Não alteramos nós de transcrição/análise ou outros tipos de LLM.
