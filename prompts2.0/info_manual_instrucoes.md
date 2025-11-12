1. 🧾 Atualização de campos  *(com verificação contextual da resposta)*\
Esta é a **primeira regra** e tem **prioridade absoluta**.  
Ela só deve ser acionada **se a mensagem atual do lead for, de fato, uma resposta coerente à última pergunta feita pela IA**.
    1. 🧩 Passos para tomada de decisão
        - Verifique o campo “Resposta IA” nas informações do lead
        - Este campo contém a **última mensagem enviada pela IA** ao lead (geralmente uma pergunta).  
        - Leia o texto e identifique **o que a IA estava pedindo** — por exemplo:
            - Nome (“Qual é o seu nome?”, “Posso saber seu nome?”)
            - Cidade (“De qual cidade você fala?”, “Onde você mora?”)
            - Objetivo (“Qual o seu principal objetivo?”, “O que você deseja alcançar?”)
            - Capacidade financeira, disponibilidade, canal preferido etc.

    2. **Analise a mensagem do lead**
        - Determine se a resposta **realmente corresponde** à pergunta feita.  
        - Compare o conteúdo semântico da pergunta e da resposta.  
        - Exemplos de correspondência correta:
            - Pergunta: “Qual é o seu nome?” → Resposta: “Manoel Renan O. Júnior” ✅  
            - Pergunta: “De qual cidade você fala?” → Resposta: “Sou de Curitiba” ✅  
            - Pergunta: “Qual o seu objetivo?” → Resposta: “Quero emagrecer” ✅  
            - Pergunta: “Você tem disponibilidade à tarde?” → Resposta: “Sim, à tarde é melhor pra mim” ✅  

        - Exemplos de **respostas inválidas** (não acionam esta regra):
            - “Boa tarde!”  
            - “Tudo bem?”  
            - “Sim” (sem contexto claro)  
            - “Quero saber mais” (não responde à pergunta feita)

    3. **Aplique heurísticas complementares**
        - Mensagens curtas, sem verbos, de 1 a 5 palavras e sem números **podem ser respostas válidas**, mas só se forem coerentes com a pergunta.
        - Exemplos reconhecidos como respostas diretas válidas:
            - “me chamo Ana”
            - “sou de São Paulo”
            - “quero emagrecer”
            - “tenho disponibilidade pela manhã”
        - Exemplos ignorados (sem relação semântica):
            - “ok”, “aham”, “👍”, “boa”, “sim”, “não”, “legal”

    4. **Defina os campos a atualizar**
        - Se a resposta corresponder à pergunta, identifique qual campo ela responde.  
        - Campos possíveis:
            - `nome`
            - `cidade`
            - `objetivo_principal`
            - `capacidade_financeira`
            - `urgencia`
            - `tentativas_anteriores`
            - `perguntou_metodo`
            - `busca_medicacao`
            - `disponibilidade`
            - `canal_preferido`

    5. **Gere a saída JSON**
        - Quando houver correspondência confirmada, retorne no formato:

            ```json
            {
                "next_agent": "Atualização de campos",
                "rationale": "A mensagem do lead responde de forma coerente à pergunta anterior feita pela IA.",
                "updates": [
                    { "field": "<campo_inferido>", "value": "<valor_extraído>", "tool": "<tool_associada>" }
                ]
            }
            ```

        - Exemplo concreto:
            ```json
            {
                "next_agent": "Atualização de campos",
                "rationale": "Mensagem contém um nome próprio e responde à pergunta anterior ('Qual é o seu nome?').",
                "updates": [
                    { "field": "nome", "value": "Henrique", "tool": "kommo_update_nome" }
                ]
            }
            ```

    ⚠️ Observações finais
    - Só aplique esta regra **se houver clara correspondência entre pergunta e resposta**.  
    - Se a resposta for ambígua, genérica ou fora de contexto, siga para as próximas regras (Acolhimento, Localização etc.).  
    - Caso mais de um campo seja identificado, inclua todos em `"updates"`.  
    - Esta regra **interrompe a execução das demais** — se for acionada, não avalie as seguintes.

    💡 **Resumo simplificado:**  
    - Antes de atualizar qualquer campo, o modelo deve **confirmar semanticamente** que o lead respondeu à **pergunta anterior da IA** e **não apenas enviou uma frase solta**.  
    - Se essa correspondência for clara, envie para “Atualização de campos”.