# IGOR_FINAL

Automação de atendimento comercial com agentes de IA para o Instituto Dr. Igor (nutrólogo), orquestrada em n8n. Este repositório documenta a lógica do fluxo e a arquitetura técnica do projeto.

## Conteúdo
- `Logica_do_Fluxo.md` — visão funcional, jornada do usuário, regras de roteamento e objetivos dos agentes.
- `Arquitetura_Tecnica.md` — integrações (WhatsApp/CRM/LLM), memória, fila, RAG (PGVector) e componentes n8n.
- `docs/fluxo.mmd` — diagrama Mermaid do fluxo de ponta a ponta.

## Diagrama (Mermaid)
O diagrama completo está em `docs/fluxo.mmd`. Também incluído abaixo para visualização rápida no GitHub.

```mermaid
flowchart TD
  %% Entrada e Normalização
  W["Webhook POST /wa/orchestrator"] --> N["Normalize Input"]
  N --> T{Tipo de mensagem}
  T -->|texto| M[Mensagem]
  T -->|áudio| A1[Obter base64 áudio] --> A2[Transcrever áudio]
  T -->|imagem| I1[Obter base64 imagem] --> I2[Analisar imagem]
  M --> J[Unificar entrada]
  A2 --> J
  I2 --> J

  %% Enriquecimento e Estado
  J --> E["Obter info do lead + Status da pipeline"]
  E --> U[Atualizar data da última mensagem]
  U --> O["ORCHESTRATOR (LLM)"]

  %% Decisão do Orquestrador
  subgraph Agentes
    ACOLH[IGOR_02.3_ACOLHIMENTO]\nPedir nome e acolher
    QUALI[IGOR_02.1_QUALIFICACAO]\nQualificar e apresentar valor
    AGENDA[IGOR_02.2_AGENDAMENTO]\nPronto para marcar → humano
    OBJ[IGOR_02.5_OBJECAO]\nTratar objeções/valores
    ESC[IGOR_02.4_ESCALACAO]\nTransferir por compliance/risco
    NUTRI[IGOR_02.6_NUTRICAO]\nEncerrar sem pressão
    UPDATE[IGOR_02_Agente_Atualização de campos]\nRAG + atualização no CRM
  end

  O -->|sem nome| ACOLH
  O -->|dados para atualizar| UPDATE
  O -->|pronto para marcar| AGENDA
  O -->|objeções| OBJ
  O -->|compliance/transferir| ESC
  O -->|senão| QUALI
  O -.->|sem prontidão| NUTRI

  %% Resposta, Fragmentação e Envio
  ACOLH --> R
  QUALI --> R
  AGENDA --> R
  OBJ --> R
  ESC --> R
  NUTRI --> R
  UPDATE --> R

  subgraph Entrega
    R["Fragmentar resposta → Enviar via WhatsApp"] --> MEM[Atualizar memória (Postgres)]
  end

  MEM --> L{Novas mensagens?}
  L -->|sim| W
  L -->|não| F((Fim))

  %% Observações
  note over O
    Redis controla fila e ordem de mensagens
    para evitar concorrência/respostas duplicadas.
  end
```

## Como testar (alto nível)
- Envie um POST para o webhook do Orquestrador com uma mensagem simulada de WhatsApp.
- Observe o roteamento a depender do contexto:
  - Sem nome → Acolhimento
  - Pronto para marcar → Aguardando agendamento (transferência humana)
  - Objeções → Objeções/Valores
  - Dados explícitos (ex.: objetivo) → Atualização de campos
- Verifique envio ao WhatsApp, atualização no CRM e memória de conversa.

## Próximos passos (opcionais)
- Adicionar exemplos de payloads (curl) por cenário.
- Exportar prompts completos por agente para versionamento em `docs/prompts/`.
- Incluir diagrama de sequência com mensagens/estados.

