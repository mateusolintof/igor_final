# IGOR_FINAL — Arquitetura Técnica e Componentes

Este documento descreve a arquitetura técnica, integrações e principais componentes dos workflows IGOR_* na instância n8n.

## Workflows Principais
- IGOR_01_Fluxo_Orquestrador (ativo)
- IGOR_02_Agente_Atualização de campos
- IGOR_02.1_QUALIFICACAO
- IGOR_02.2_AGENDAMENTO
- IGOR_02.3_ACOLHIMENTO
- IGOR_02.4_ESCALACAO
- IGOR_02.5_OBJECAO
- IGOR_02.6_NUTRICAO

Há ainda um workflow “Error” para registro de erros em planilha (fora do prefixo IGOR_).

## Topologia e Fluxo de Dados
- Entrada HTTP: Webhook do n8n com `path=wa/orchestrator` (método POST).
  - Recebe eventos/mensagens do WhatsApp (texto/áudio/imagem/anexos).
  - Normaliza e classifica o tipo de mensagem.
- Multimodal:
  - Áudio → HTTP para obter base64 → Transcrição (OpenAI Whisper).
  - Imagem → HTTP para obter base64 → Análise de imagem (vision) e, quando aplicável, extração de texto/arquivo.
- CRM/Backend:
  - “Obter info” e “Status da pipeline” (HTTP) para enriquecer contexto.
  - “Atualizar data última mensagem” (HTTP) para telemetria/CRM.
- Orquestração:
  - Agente LLM “ORCHESTRATOR” define o próximo agente com base em regras e contexto.
  - Disparo do sub-workflow correspondente via `executeWorkflow`.
- Saída WhatsApp:
  - Resposta do agente é fragmentada (split) e enviada via HTTP ao provedor de WhatsApp.
  - Memória de conversa é atualizada.

## Componentes Técnicos
- n8n Workflows e Nodes:
  - `webhook` (entrada), `httpRequest`/`httpRequestTool` (integrações externas), `if`/`switch` (controle), `executeWorkflow` (composição), `set`/`code` (transformação), `split*` (fragmentação), `wait` (orquestração temporal).
  - Redis (nodes `n8n-nodes-base.redis`): fila/lista de mensagens para leitura/remoção, evitando concorrência e mantendo ordem.
  - Memória de Conversa (Postgres): `@n8n/n8n-nodes-langchain.memoryPostgresChat` para manter contexto entre interações.
  - OpenAI LLM e Embeddings:
    - `@n8n/n8n-nodes-langchain.lmChatOpenAi` (chat), `@n8n/n8n-nodes-langchain.embeddingsOpenAi` (embeddings), `openAi` (transcribe/analyze, e vision conforme o caso).
  - Structured Output Parser: `@n8n/n8n-nodes-langchain.outputParserStructured` para normalizar saídas de agentes quando necessário.
  - Extração de Arquivos: `n8n-nodes-base.extractFromFile` (ex.: PDFs) quando presente.

## Agente de Atualização de Campos (RAG + Ações no CRM)
- Workflow: IGOR_02_Agente_Atualização de campos.
- Objetivo: mapear mensagens a “campos do CRM” e atualizar valores com segurança.
- Vector Store (PGVector):
  - Tabela: `n8n_vectors_fields`.
  - `mode=insert` para indexar metadados de campos (nome/ID/tipo/opções/descrições).
  - `mode=retrieve-as-tool` para uso como ferramenta de busca: retorna top-1 candidato por similaridade, instruindo o agente a preferir slug exato quando houver.
- Embeddings/LLM: OpenAI embeddings para vetorização e chat model para raciocínio/decisão.
- Integração CRM:
  - `httpRequestTool`/`httpRequest` chama endpoints de atualização (ex.: campo genérico via tool; “Atualiza nome”; “Atualiza cidade”).
- Controles:
  - `if`/`switch` garantem o fluxo correto e não duplicação de atualizações.

## Sub-Agentes e Diretrizes (resumo)
- Acolhimento: captar nome e dar boas-vindas com linguagem adequada.
- Qualificação: aprofundar objetivos, histórico, preferências e apresentar valor.
- Aguardando agendamento: sinaliza transferência para humano quando há prontidão.
- Objeções/Valores: trata preço, tempo, convênio, distância com transparência.
- Escalação/Compliance: transfere para humano por regras de segurança/compliance.
- Nutrição: encerra sem pressão, reforça valor e mantém porta aberta.

Cada agente recebe um `default_prompt` do orquestrador e opera com memória de conversa. O retorno ao orquestrador pode ser estruturado (ex.: mensagens + metadados/intenções), permitindo pós-processamento e envio.

## Observabilidade e Resiliência
- Workflow “Error” (gatilho `Error Trigger`) salva eventos de erro em uma planilha Google (sheet “Erro” de “ASX - Leads SDR”).
- Fila em Redis + waits evitam respostas duplicadas e controlam a ordem.
- Nós `noOp` e checagens (`if`/`switch`) tratam casos sem ação clara.

## Segurança e Configuração
- Segredos e chaves (LLM, WhatsApp, CRM) configurados no n8n (credenciais/conexões). Não expor em repositórios.
- Webhook de produção deve usar o `path=wa/orchestrator` do orquestrador (URL completa depende do ambiente n8n).
- Acesso de API (administrativo) requer `X-N8N-API-KEY` válido.

## Diferenciais do Projeto
- Orquestrador com regras explícitas + decisão LLM (multi-agentes).
- Suporte multimodal (texto/áudio/imagem) com transcrição e análise.
- Memória de conversa persistente (experiência contínua e contextualizada).
- RAG para mapeamento semântico de campos do CRM com PGVector.
- Fragmentação de mensagens para UX fluida no WhatsApp.
- Estrita priorização por contexto (ex.: atualizar campos antes de dialogar quando necessário).

## Como Exercitar/Testar (alto nível)
- Enviar POST ao webhook do orquestrador com payload de mensagem (texto/áudio/imagem) e identificar o comportamento esperado:
  - Sem nome → Acolhimento.
  - Pronto para marcar → Aguardando agendamento.
  - Objeções → Objeções/Valores.
  - Dados explícitos (ex.: “objetivo: emagrecimento”) → Atualização de campos.
- Verificar envios ao WhatsApp, atualização no CRM, e persistência de memória.

