/**
 * CHUNKING INTELIGENTE - Agente Dr. Igor
 *
 * Divide respostas longas em chunks de até 160 caracteres,
 * mantendo contexto semântico (não quebra palavras/frases).
 *
 * INSTALAÇÃO:
 * 1. Delete o nó "Edit Fragmenta" existente
 * 2. Crie um Code Node na mesma posição
 * 3. Renomeie para "Split into 160-char Chunks"
 * 4. Cole este código completo
 * 5. Language: JavaScript
 * 6. Mode: Run Once for All Items
 *
 * INPUT: Recebe $input.first().json.output (dos agentes Exec → Agente)
 * OUTPUT: Array de chunks com metadata (campo 'messages' compatível com o fluxo)
 */

// ==================== FUNÇÃO DE CHUNKING ====================

function splitIntoChunks(text, maxLength = 160) {
    const chunks = [];
  
    // Validações
    if (!text || typeof text !== 'string') return [''];
    if (text.length <= maxLength) return [text];
  
    // Estratégia 1: Dividir por parágrafos
    const paragraphs = text.split(/\n\n+/);
  
    for (const paragraph of paragraphs) {
      const trimmed = paragraph.trim();
  
      // Parágrafo cabe inteiro
      if (trimmed.length <= maxLength) {
        chunks.push(trimmed);
        continue;
      }
  
      // Estratégia 2: Dividir por frases
      const sentences = trimmed.match(/[^.!?]+[.!?]+/g) || [trimmed];
      let currentChunk = '';
  
      for (const sentence of sentences) {
        const trimmedSentence = sentence.trim();
  
        // Frase muito longa: dividir por palavras
        if (trimmedSentence.length > maxLength) {
          if (currentChunk.trim()) {
            chunks.push(currentChunk.trim());
            currentChunk = '';
          }
  
          // Estratégia 3: Dividir por palavras
          let remaining = trimmedSentence;
          while (remaining.length > 0) {
            if (remaining.length <= maxLength) {
              chunks.push(remaining.trim());
              break;
            }
  
            const lastSpace = remaining.lastIndexOf(' ', maxLength);
            const breakPoint = lastSpace > maxLength * 0.7 ? lastSpace : maxLength;
  
            chunks.push(remaining.substring(0, breakPoint).trim());
            remaining = remaining.substring(breakPoint).trim();
          }
        } else {
          // Frase normal: tentar juntar com chunk atual
          const potential = currentChunk ? currentChunk + ' ' + trimmedSentence : trimmedSentence;
  
          if (potential.length <= maxLength) {
            currentChunk = potential;
          } else {
            if (currentChunk.trim()) chunks.push(currentChunk.trim());
            currentChunk = trimmedSentence;
          }
        }
      }
  
      if (currentChunk.trim()) chunks.push(currentChunk.trim());
    }
  
    return chunks.filter(chunk => chunk.length > 0);
  }
  
  // ==================== EXECUÇÃO ====================
  
  // Pegar resposta do agente (vem diretamente dos Exec → Agente)
  // Os agentes retornam { output: "mensagem..." }
  const agentResponse = $input.first().json.output
                     || $input.first().json.text
                     || '';
  
  // Dividir em chunks
  const chunks = splitIntoChunks(agentResponse, 160);
  
  // Log para debug (visível nas execuções do n8n)
  console.log(`📦 ${chunks.length} chunk(s) criado(s)`);
  chunks.forEach((chunk, i) => {
    console.log(`   [${i}] ${chunk.length} chars: "${chunk.substring(0, 40)}..."`);
  });
  
  // ==================== RETORNO ====================
  
  // Retornar chunks com metadata
  return chunks.map((chunk, index) => ({
    json: {
      messages: chunk,                        // ← Campo usado pelo workflow atual
      chunk: chunk,                           // ← Alternativo
      chunkIndex: index,                      // ← Usado pelo IF Node
      totalChunks: chunks.length,
      isFirstChunk: index === 0,
      isLastChunk: index === chunks.length - 1
    }
  }));
  