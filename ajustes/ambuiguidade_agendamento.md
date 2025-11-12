# ✏️ Correção: Ambiguidade "Quero Consultar" no Roteamento

**Data:** 26/10/2025
**Problema:** Gatilho "quero consultar" é ambíguo sem contexto
**Reportado por:** Usuário (observação crítica sobre NECESSIDADE vs OBJETIVO)
**Versão:** 1.2 do prompt.orquestrador.v2.md

---

## 🎯 Problema Identificado

### Ambiguidade Crítica

O gatilho `"quero consultar"` estava na lista de prontidão para agendamento, mas pode significar:

**Cenário A (primeira mensagem):**
```
Lead: "Oi, quero consultar"
```
❌ **NÃO** está pronto para agendar
✅ **ESTÁ** declarando intenção inicial
→ Deve rotear para: Acolhimento ou Qualificação

**Cenário B (após qualificação):**
```
[Após conversa]
Agente: "São R$ 700. Faz sentido?"
Lead: "Sim, quero consultar"
```
✅ **ESTÁ** pronto para agendar
→ Deve rotear para: Aguardando agendamento

---

## 💡 Diferenciação Conceitual

### NECESSIDADE (clínica) ≠ OBJETIVO (do contato)

**NECESSIDADE:**
- O que o lead quer resolver
- "Quero emagrecer", "Perder 15kg"
- Campo coletado: `objetivo_principal`
- Agente responsável: Qualificação

**OBJETIVO do contato:**
- Por que está entrando em contato AGORA
- "Quero agendar" (decisão) vs "Quero informações" (pesquisa)
- NÃO é campo, é ESTADO no funil
- Orquestrador decide roteamento baseado nisso

---

## 🔧 Correção Aplicada

### Antes (v2.0 - AMBÍGUO)

```xml
<quando_usar>
  Acione quando mensagem indicar prontidão para agendar:
  - "quero agendar" ✅
  - "pode marcar" ✅
  - "quero consultar" ⚠️ AMBÍGUO
  - "quando tem disponibilidade?" ⚠️ AMBÍGUO
  - "qualquer horário serve" ✅
</quando_usar>
```

**Problema:**
- "Quero consultar" na primeira mensagem rotearia para Agendamento
- Pularia qualificação completamente
- Lead não seria preparado para decisão

---

### Depois (v2.1 - CONTEXTUAL)

```xml
<quando_usar>
  <gatilhos_inequivocos>
    Frases que SEMPRE indicam prontidão:
    - "pode marcar" ✅
    - "vamos agendar" ✅
    - "tem vaga amanhã?" ✅
    - "qualquer horário serve" ✅
  </gatilhos_inequivocos>

  <gatilhos_contextuais>
    Frases AMBÍGUAS que precisam verificar estado:

    SE lead_info.qualificado = true:
    - "quero consultar" → É prontidão ✅
    - "quando tem disponibilidade?" → É prontidão ✅

    SENÃO (não qualificado):
    - "quero consultar" → Rotear para Qualificação
    - "quando tem disponibilidade?" → Rotear para Qualificação
  </gatilhos_contextuais>

  <gatilhos_pos_confirmacao>
    SE agente perguntou "Quer agendar?":
    - "sim" / "quero" / "pode ser" → É prontidão ✅
  </gatilhos_pos_confirmacao>
</quando_usar>

<quando_NAO_usar>
  ❌ "Quero consultar" na PRIMEIRA mensagem
     → Rotear para: Acolhimento ou Qualificação

  ❌ "Quando tem horário?" SEM contexto
     → Rotear para: Qualificação

  ❌ Lead com objeção ativa não resolvida
     → Rotear para: Objeções/Valor primeiro
</quando_NAO_usar>
```

---

## 📊 Categorias de Gatilhos

### ✅ INEQUÍVOCOS (sempre = prontidão)

| Frase | Por quê inequívoco |
|-------|-------------------|
| "pode marcar" | Verbo imperativo de ação |
| "vamos agendar" | Decisão explícita |
| "tem vaga amanhã?" | Pergunta sobre data concreta |
| "aceito, pode marcar" | Confirmação + ação |
| "qualquer horário serve" | Flexibilidade confirmada |

---

### ⚠️ AMBÍGUOS (contexto necessário)

| Frase | Ambiguidade | Como resolver |
|-------|-------------|---------------|
| "quero consultar" | Intenção OU prontidão | Verificar se `lead_info.qualificado = true` |
| "quando tem disponibilidade?" | Curiosidade OU decisão | Verificar se após aceitação de valor |
| "quero uma consulta" | Necessidade OU agendamento | Verificar campos essenciais coletados |
| "qual próximo passo?" | Pesquisa OU prontidão | Verificar se qualificação completa |

---

### ❌ FALSOS POSITIVOS (NUNCA são prontidão no início)

| Frase | Por quê NÃO é prontidão | Rotear para |
|-------|------------------------|-------------|
| "quero informações sobre consulta" | Pesquisa inicial | Qualificação |
| "quanto custa consulta?" | Coleta de informação | Qualificação |
| "vocês atendem?" | Dúvida genérica | Qualificação |
| "quero emagrecer" | Necessidade, não objetivo do contato | Qualificação |

---

## 🎓 Exemplos Práticos

### Exemplo 1: "Quero consultar" (1ª mensagem)

**Input:**
```
Lead (primeira msg): "Oi, quero consultar"
```

**Estado:** lead_info.nome = null, qualificado = false

**Análise orquestrador:**
```
- Detecta "quero consultar" (gatilho ambíguo)
- Verifica lead_info.qualificado → false
- Conclusão: É INTENÇÃO INICIAL, não prontidão
```

**Decisão correta:**
```json
{
  "next_agent": "Acolhimento",
  "rationale": "Primeira mensagem, precisa obter nome e qualificar."
}
```

---

### Exemplo 2: "Quero consultar" (após qualificação)

**Input:**
```
[Mensagem #10 da conversa]
Agente: "São R$ 700 por 3 consultas. Faz sentido?"
Lead: "Sim, quero consultar"
```

**Estado:** lead_info.nome = "João", objetivo = "Emagrecimento", qualificado = true

**Análise orquestrador:**
```
- Detecta "quero consultar" (gatilho ambíguo)
- Verifica lead_info.qualificado → true
- Verifica contexto: após apresentação de valor
- Conclusão: É PRONTIDÃO REAL
```

**Decisão correta:**
```json
{
  "next_agent": "Aguardando agendamento",
  "rationale": "Lead qualificado e confirmou prontidão."
}
```

---

### Exemplo 3: "Quando tem disponibilidade?" (início)

**Input:**
```
Lead: "Bom dia, quanto custa e quando tem disponibilidade?"
```

**Estado:** lead_info.qualificado = false

**Análise orquestrador:**
```
- Detecta "quando tem disponibilidade" (gatilho ambíguo)
- Verifica lead_info.qualificado → false
- Conclusão: É CURIOSIDADE/PESQUISA, não decisão
```

**Decisão correta:**
```json
{
  "next_agent": "Qualificação",
  "rationale": "Lead pesquisando, precisa qualificar antes de agendar."
}
```

**Resposta do agente Qualificação:**
```
"A consulta é R$ 700, com horários flexíveis de segunda a sexta.
Qual é o seu objetivo principal?"
[Continua qualificação...]
```

---

### Exemplo 4: "Quando tem disponibilidade?" (após aceitação)

**Input:**
```
[Após qualificação]
Agente: "Perfeito. Quer que eu separe um horário?"
Lead: "Sim! Quando tem disponibilidade?"
```

**Estado:** lead_info.qualificado = true

**Análise orquestrador:**
```
- Detecta "quando tem disponibilidade" (gatilho ambíguo)
- Verifica lead_info.qualificado → true
- Verifica contexto: após confirmação "Sim"
- Conclusão: É PRONTIDÃO REAL
```

**Decisão correta:**
```json
{
  "next_agent": "Aguardando agendamento",
  "rationale": "Lead confirmou e pergunta horários concretos."
}
```

---

## 🔍 Como Verificar "lead_info.qualificado"?

### Critérios Sugeridos

```javascript
lead_info.qualificado = (
  lead_info.nome != null &&
  lead_info.objetivo != null &&
  lead_info.capacidade_financeira != "objetou_fortemente" &&
  (
    lead_info.status == "QUALIFICADO" ||
    mensagens_trocadas >= 5
  )
)
```

**OU verificar status direto no CRM:**
```javascript
if (lead_info.status == "QUALIFICADO") {
  // Gatilhos ambíguos AGORA são prontidão
}
```

---

## 📋 Checklist de Implementação

Para implementar corretamente, o sistema deve:

- [ ] Diferenciar gatilhos inequívocos de ambíguos
- [ ] Verificar `lead_info.qualificado` antes de rotear gatilhos ambíguos
- [ ] Considerar contexto da mensagem anterior (perguntou "Quer agendar?")
- [ ] NÃO rotear "quero consultar" para Agendamento na primeira mensagem
- [ ] Permitir que lead passe por Qualificação antes de Agendamento

---

## 🎯 Impacto Esperado

### Antes da Correção

**Problema:**
```
Lead: "Oi, quero consultar"
Sistema: [Roteia para Agendamento]
Agente: "Perfeito! De qual cidade você é?"
Lead: "???" (esperava ser qualificado primeiro)
```

**Resultado:** Taxa de abandono alta, leads confusos

---

### Depois da Correção

**Solução:**
```
Lead: "Oi, quero consultar"
Sistema: [Detecta ambiguidade, verifica qualificado=false, roteia para Acolhimento]
Agente: "Boa tarde! Sou Alice. Qual é o seu nome?"
Lead: "João"
Agente: "Prazer, João! Qual é o seu objetivo principal?"
[Qualificação normal...]
Lead: "Sim, quero consultar então"
Sistema: [Agora detecta qualificado=true, roteia para Agendamento]
Agente: "Perfeito! De qual cidade você é?"
```

**Resultado:** Fluxo natural, lead preparado, taxa de conversão maior

---

## ✅ Arquivos Atualizados

- ✅ `prompt.orquestrador.v2.md` - Seção "Aguardando agendamento" reestruturada
- ✅ `ANALISE_ULTRATHINKING_ROTEAMENTO.md` - Análise detalhada (500+ linhas)
- ✅ `CORRECAO_AMBIGUIDADE_AGENDAMENTO.md` - Este documento (resumo)

---

## 📊 Métricas de Sucesso

**Indicadores de que correção funcionou:**

1. ✅ "Quero consultar" na 1ª msg vai para Acolhimento/Qualificação
2. ✅ "Quero consultar" após qualificação vai para Agendamento
3. ✅ Nenhum lead pula qualificação indevidamente
4. ✅ Taxa de agendamento aumenta (leads mais preparados)

**Métricas esperadas:**
- Taxa de abandono: -20% (menos confusão)
- Taxa de agendamento: +15-25% (leads mais qualificados)
- Mensagens até agendamento: -10% (roteamento correto)

---

**Versão:** 1.0
**Data:** 26/10/2025
**Crédito:** Observação crítica do usuário sobre ambiguidade e diferenciação NECESSIDADE vs OBJETIVO
