# Guia de Testes Rápidos (Webhook Orquestrador)

Este guia ajuda a validar o comportamento do fluxo ponta a ponta (roteamento do Orquestrador + resposta dos agentes) com chamadas HTTP simples.

Observação importante
- Endpoints do webhook do n8n:
  - Produção: `https://flow.convert-saude.space/webhook/wa/orchestrator`
  - Teste (Editor): `https://flow.convert-saude.space/webhook-test/wa/orchestrator` (funciona apenas com o workflow executando no Editor do n8n)
- Use `Content-Type: application/json`.
- Os exemplos abaixo usam payloads mínimos esperados pelo Orquestrador: `mensagem` e, opcionalmente, `lead_info`.
- Resultado prático: a resposta é enviada ao WhatsApp pelo fluxo. Para depurar, observe a Execução no n8n e os nós “Switch/Execute Workflow/Enviar mensagem”.

## Variáveis úteis

```bash
WEBHOOK_URL="https://flow.convert-saude.space/webhook/wa/orchestrator"
```

---

## S1 — Primeira mensagem ambígua ("quero consultar")
Objetivo: garantir que NÃO roteia direto para Agendamento quando ainda não qualificado.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Oi, quero consultar"
  }'
```
Esperado: Orquestrador identifica ambiguidade e roteia para Acolhimento (se faltar nome) ou Qualificação (perguntar objetivo).

---

## S2 — Pergunta de preço no início
Objetivo: responder curto e seguir para objetivo (sem virar interrogatório).

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Quanto custa a consulta?"
  }'
```
Esperado: resposta objetiva (R$ 700) e, em seguida, pergunta única sobre objetivo principal.

---

## S3 — Objetivo claro (qualifica sem perguntar finanças)
Objetivo: marcar objetivo como claro sem interrogar finanças; seguir conversa natural.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Quero emagrecer 12kg e definir",
    "lead_info": {
      "name": "João"
    }
  }'
```
Esperado: Qualificação reconhece objetivo claro; segue conversa com tom humano e curto.

---

## S4 — Objeção de preço explícita
Objetivo: roteamento para Objeções/Valor com resposta curta (sem discurso).

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "R$ 700 está caro pra mim",
    "lead_info": {"name": "Ana", "objetivo": "definição corporal"}
  }'
```
Esperado: tratar objeção de forma breve e humana; sem empilhar perguntas.

---

## S5 — "Quero consultar" após qualificação (prontidão real)
Objetivo: diferenciar ambíguo vs. pronto quando já qualificado.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Quero consultar",
    "lead_info": {
      "name": "Carla",
      "objetivo": "emagrecimento",
      "qualificado": true
    }
  }'
```
Esperado: Orquestrador envia para Aguardando agendamento (transferência humana).

---

## S6 — Escalação (pedido de humano/tema sensível)
Objetivo: transferência cordial e curta.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Prefiro falar com um atendente humano agora"
  }'
```
Esperado: Escalação/Compliance com mensagem curta e educada.

---

## S7 — Nutrição (desinteresse no momento)
Objetivo: encerrar sem pressão, deixar porta aberta.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Estou só pesquisando por enquanto"
  }'
```
Esperado: Nutrição com 1–2 frases, convite leve para continuar quando quiser.

---

## S8 — Atualização de campo (cidade)
Objetivo: atualizar campo sem explicar backoffice.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "Sou de Salvador",
    "lead_info": {"name": "Marcos"}
  }'
```
Esperado: atualização de cidade no CRM (quando mapeado) e resposta curta mantendo o diálogo.

---

## S9 — Multimídia: Áudio
Objetivo: validar transcrição + resposta curta.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "(áudio)",
    "type": "audio",
    "audio_url": "https://exemplo.com/sample_audio.mp3",
    "lead_info": {"name": "Bianca"}
  }'
```
Observação: o fluxo baixa o arquivo e transcreve. Use uma URL acessível.

---

## S10 — Multimídia: Imagem
Objetivo: validar análise de imagem + resposta curta.

```bash
curl -sS -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{
    "mensagem": "(imagem)",
    "type": "image",
    "image_url": "https://exemplo.com/arquivo.jpg",
    "lead_info": {"name": "Paula"}
  }'
```
Observação: o fluxo baixa a imagem e analisa; use uma URL pública.

---

## Como validar
- No n8n, abra Executions e filtre pelo workflow do Orquestrador.
- Verifique:
  - Nó “Switch” → próximo agente coerente com o cenário.
  - Nó “Execute Workflow” do agente correto.
  - Nós “Enviar mensagem” com fragmentação curta (1–2 frases; 3–4 somente quando necessário).
- No WhatsApp, confirme que as mensagens chegam curtas, humanas e sem formalismo artificial.

## Dicas de ajuste fino
- Resposta ainda longa: reduza `maxTokens` do agente específico (-20/-30).
- Muito engessado: aumente `temperature` (+0.05/+0.1) do agente específico.
- Muletas repetidas: aumente `frequencyPenalty` (+0.1) do agente específico.
