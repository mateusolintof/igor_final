   # 🤖 Guia de Implementação: Chunking Inteligente

**Workflow:** WA Orquestrador – Principal
**Agente Dr. Igor - Instituto Aguiar Neri**

---

## 🎯 Objetivo

Humanizar respostas longas dividindo-as em chunks de 160 caracteres com delay de 2s entre mensagens.

**Benefícios:**
- ✅ Parece digitação humana
- ✅ Primeiro chunk imediato
- ✅ Sem delay após último chunk (otimizado)
- ✅ Não quebra palavras/frases

---

## 📍 O Que Vai Mudar

### **ANTES:**
```
[Exec → Agente] → Edit Fragmenta → Split \n → Split Out → Loop Over Items → Atualizar resposta IA → Enviar mensagem → Wait6
```

### **DEPOIS:**
```
[Exec → Agente] → Code: Split into 160-char Chunks → Loop Over Items → IF (chunkIndex > 0?)
                                                                              ↓           ↓
                                                                          [TRUE]      [FALSE]
                                                                              ↓           ↓
                                                                           Wait6    (pula wait)
                                                                              ↓           ↓
                                                                     Atualizar resposta IA ←┘
                                                                              ↓
                                                                      Enviar mensagem
                                                                              ↓
                                                                   (volta ao Loop Over Items)
```

**Mudanças:**
- ❌ Deletar: `Edit Fragmenta`, `Split \n`, `Split Out`
- ✅ Criar: Code Node, IF Node
- ✅ Reorganizar: Wait6 vem ANTES do envio

---

## 🛠️ Implementação

### **PASSO 1: Deletar Nós Antigos**

Deletar os seguintes nós:
1. ❌ `Edit Fragmenta`
2. ❌ `Split \n`
3. ❌ `Split Out`

### **PASSO 2: Criar Code Node**

**1. Criar o nó:**
- Após todos os `Exec → Agente` (onde estava Edit Fragmenta)
- Tipo: **Code**
- Nome: `Split into 160-char Chunks`

**2. Configurar:**
- **Language:** JavaScript
- **Mode:** Run Once for All Items

**3. Código:**
Copiar todo o conteúdo de `chunking_code.js`

### **PASSO 3: Ajustar Loop Over Items**

**Configuração:**
- **Batch Size:** `1`
- **Options → Reset:** ✅ `true`

**Conexão:**
- Input: `Split into 160-char Chunks`

### **PASSO 4: Criar IF Node**

**1. Criar o nó:**
- Entre `Loop Over Items` e `Wait6`
- Tipo: **IF**
- Nome: `Skip Wait on First Chunk`

**2. Configurar condição:**

**Value 1:** `{{ $json.chunkIndex }}`
**Operation:** `Larger`
**Value 2:** `0`

**OU expressão:**
```javascript
{{ $json.chunkIndex > 0 }}
```

### **PASSO 5: Reorganizar Conexões**

**Conectar nesta ordem:**

1. **Loop Over Items:**
   - Saída `done` → `No Operation, do nothing3`
   - Saída `loop` → `Skip Wait on First Chunk` (IF)

2. **IF Node:**
   - Saída `TRUE` → `Wait6`
   - Saída `FALSE` → `Atualizar resposta IA`

3. **Wait6:**
   - Saída → `Atualizar resposta IA`

4. **Atualizar resposta IA:**
   - Saída → `Enviar mensagem`

5. **Enviar mensagem:**
   - Saída → `Loop Over Items` (fecha o loop)

### **PASSO 6: Configurar Wait6**

- **Amount:** `2`
- **Unit:** `Seconds`
- **Resume:** `After time interval`

---

## 🎨 Diagrama Visual

```
Split into 160-char Chunks (Code)
         ↓
         [Array de chunks com metadata]
         ↓
Loop Over Items (batch=1)
    ↓           ↓
 [done]      [loop]
    ↓           ↓
 [No Op]   IF (chunkIndex > 0?)
              ↓         ↓
           [TRUE]    [FALSE]
              ↓         ↓
           Wait6        |
           (2s)         |
              ↓         |
    Atualizar resposta IA ←┘
              ↓
       Enviar mensagem
              ↓
    (volta ao Loop Over Items)
```

**Timeline (3 chunks):**
```
t=0s:  Chunk 0 → enviado (pula wait)
t=0-2s: Wait
t=2s:  Chunk 1 → enviado
t=2-4s: Wait
t=4s:  Chunk 2 → enviado (último, não espera depois)
Total: 4s
```

---

## ✅ Checklist de Implementação

- [ ] Deletou `Edit Fragmenta`
- [ ] Deletou `Split \n`
- [ ] Deletou `Split Out`
- [ ] Criou Code Node `Split into 160-char Chunks`
- [ ] Colou código de `chunking_code.js`
- [ ] Configurou Code: JavaScript, Run Once for All Items
- [ ] Verificou Loop Over Items: batch size=1, reset=true
- [ ] Criou IF Node `Skip Wait on First Chunk`
- [ ] Configurou IF: `{{ $json.chunkIndex > 0 }}`
- [ ] Conectou Loop (loop) → IF
- [ ] Conectou Loop (done) → No Op
- [ ] Conectou IF (TRUE) → Wait6
- [ ] Conectou IF (FALSE) → Atualizar resposta IA
- [ ] Conectou Wait6 → Atualizar resposta IA
- [ ] Conectou Atualizar → Enviar
- [ ] Conectou Enviar → Loop (fecha loop)
- [ ] Configurou Wait6: 2 segundos

---

## 🧪 Testes

### Teste 1: Mensagem Curta
**Enviar:** "Boa tarde"
**Esperado:** 1 chunk, imediato, sem delay

### Teste 2: Mensagem Média
**Enviar:** Forçar agente a gerar ~300 caracteres
**Esperado:** 2 chunks, primeiro imediato, segundo após 2s

### Teste 3: Mensagem Longa
**Enviar:** Forçar agente a gerar ~500 caracteres
**Esperado:** 3-4 chunks, primeiro imediato, demais com 2s de intervalo

### Validações no WhatsApp
- ✅ Mensagens chegam em ordem
- ✅ Há delay de 2s entre elas
- ✅ Não há duplicação
- ✅ Último chunk não tem delay depois

---

## 🔍 Troubleshooting

### Chunks não sendo criados

**Debug no Code Node:**
```javascript
// Adicione no início (linha 90)
console.log('Input completo:', $input.first().json);
console.log('Valor de output:', agentResponse);
```

Verifique se `agentResponse` está capturando o campo correto.

### Delay não funciona

1. Verifique condição do IF: `{{ $json.chunkIndex > 0 }}`
2. Confirme Wait6 conectado na saída **TRUE** do IF
3. Confirme primeira mensagem vai direto (saída **FALSE**)

### Mensagens fora de ordem

1. Loop Over Items: Batch Size = `1`
2. Loop Over Items: Reset = `true`
3. Não executar em paralelo

### Loop infinito

1. Verificar conexão: Enviar mensagem → Loop Over Items
2. Não conectar de volta ao Code Node
3. Reset = true no Loop Over Items

---

## 📊 Fluxo de Dados

**INPUT (dos agentes):**
```json
{
  "output": "Mensagem do agente..."
}
```

**OUTPUT (do Code Node):**
```json
{
  "messages": "chunk de texto",    // ← Usado por Atualizar resposta IA
  "chunkIndex": 0,                 // ← Usado pelo IF Node
  "totalChunks": 3,
  "isFirstChunk": true,
  "isLastChunk": false
}
```

**Por que `messages`?**
- Nó `Atualizar resposta IA` usa: `{{ $json.messages }}`
- Code Node recebe `output` e retorna `messages`
- Substitui função do antigo `Edit Fragmenta`

---

## ⚡ Performance

| Cenário | Chunks | Tempo Total |
|---------|--------|-------------|
| Mensagem curta (< 160) | 1 | 0s |
| Mensagem média (~300) | 2 | 2s |
| Mensagem longa (~500) | 3-4 | 4-6s |

**Comparado com fluxo sem IF:**
- Economiza 2s por conversa (não espera após último chunk)
- Mais responsivo
- Melhor UX

---

**Versão:** 3.0 (Otimizada - Fluxo Definitivo)
**Data:** 25/10/2025
**Projeto:** Agente Dr. Igor

---

COMENTRIOS GEMINI 2.5 PRO

1. O Fluxo Ficará Mais Humanizado?
Sim, absolutamente. Este é o principal objetivo e benefício da alteração proposta. A humanização é alcançada de forma muito eficaz por três motivos:
Quebra de Mensagens (Chunking): Em vez de enviar um bloco de texto grande de uma só vez, o sistema passa a enviar pedaços menores (de 160 caracteres). Isso imita perfeitamente como uma pessoa real digita e envia mensagens no WhatsApp.
Pausa Simulado (Delay): A espera de 2 segundos entre o envio dos "chunks" simula o tempo que alguém levaria para digitar a próxima frase. Isso remove a sensação de ter recebido uma resposta instantânea e robótica.
Inteligência na Quebra: O guia menciona o uso de chunking_code.js, que (pelo nome) sugere uma quebra inteligente que não corta palavras ou frases no meio, tornando a leitura natural e fluida.
Em resumo, a experiência para o usuário final será muito mais agradável e natural, como se estivesse conversando com um atendente humano.
2. O Fluxo Ficará Mais Ágil?
Aqui a resposta precisa ser dividida em duas partes: a percepção de agilidade e o tempo de processamento real.
Percepção de Agilidade (Para o Usuário): SIM. A agilidade percebida pelo usuário irá melhorar drasticamente. O ponto mais genial da implementação é o nó IF que faz com que o primeiro "chunk" da resposta seja enviado imediatamente, sem espera. Para o usuário, a conversa começa no mesmo instante, o que dá uma sensação de responsividade e agilidade muito maior.
Agilidade Real (Tempo de Processamento do Servidor): NÃO DIRETAMENTE. É crucial entender que esta otimização não resolve o seu problema principal da IA demorar mais de 120 segundos para responder. Todo o processo de "chunking" descrito no guia acontece DEPOIS que o agente de IA já gerou a resposta completa.
[Agente IA gera o texto (Processo lento de >120s)] → [Chunking e envio humanizado (Processo rápido)]
Portanto, o seu script de teste (test_5_cenarios_iniciais.py) que espera pela resposta do webhook ainda sofrerá com o timeout, porque o webhook só responde depois que o processo lento da IA termina. A otimização melhora a entrega da mensagem, mas não a geração dela.
Minhas Observações
Excelente Melhoria de UX: A implementação proposta no guia é um padrão de mercado excelente para assistentes de chat. É uma melhoria fundamental que eleva a qualidade da interação a um nível muito mais profissional e agradável.
Foco no Problema Correto: O guia ataca com precisão o problema da "humanização" e da "percepção de velocidade". O fluxo proposto é inteligente, principalmente por pular o delay no primeiro envio e não esperar após o último.
A Causa Raiz da Lentidão Persiste: Para resolver o timeout de 120 segundos, você ainda precisa focar nas otimizações que discutimos anteriormente:
Verificar e otimizar o modelo da IA (usar gpt-4o).
Reduzir o tamanho do contexto (histórico) enviado em cada requisição.
Verificar a performance das consultas ao banco de dados e APIs externas (Kommo).
Considerar uma arquitetura assíncrona como solução definitiva.
Conclusão: Faça a implementação do GUIA_CHUNKING_HUMANIZACAO.md. Ela é excelente e necessária para a qualidade do seu produto. No entanto, saiba que ela não resolverá o problema de timeout que você está enfrentando. Trate isso como uma melhoria paralela e continue investigando os gargalos de performance na geração da resposta pela IA.
