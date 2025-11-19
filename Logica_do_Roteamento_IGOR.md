# IGOR – Lógica de Roteamento e Fluxo de Atendimento (Fonte da Verdade)

Este documento descreve, em alto nível, **como o projeto IGOR funciona do ponto de vista técnico e conversacional**, com foco na lógica de **roteamento** entre agentes.

A ideia é que qualquer pessoa (humana ou IA) consiga entender o fluxo **sem abrir os workflows no n8n**, e, a partir daqui, consiga propor mudanças coerentes.

---

## 1. Visão geral do fluxo

### 1.1 Objetivo do sistema

O sistema IGOR responde mensagens de WhatsApp de leads do Instituto Dr. Igor, com foco em:

- acolher o contato inicial;
- qualificar o lead (objetivo, contexto, momento);
- esclarecer dúvidas de valor, formato e condições da consulta;
- conduzir, quando fizer sentido, até a decisão de consulta;
- **somente então** repassar para a equipe humana de agendamento.

Toda a inteligência de decisão sobre “quem deve falar agora” está concentrada em um **Orquestrador de Leads**.

### 1.2 Componentes principais (workflows n8n)

- `IGOR_01_Fluxo_Orquestrador`  
  Workflow principal. Recebe mensagens do WhatsApp, consolida histórico e decide qual agente executar:
  - Acolhimento,
  - Qualificação,
  - Objeções/Valor,
  - Localização,
  - Escalação/Compliance,
  - Nutrição,
  - Atualização de campos (Kommo),
  - Aguardando agendamento.

- `IGOR_02.3_ACOLHIMENTO`  
  Agente responsável por **capturar o nome** quando ele ainda não existe.

- `IGOR_02.1_QUALIFICACAO`  
  Agente responsável por **entender objetivo, momento e prontidão**, explicando a consulta e valor e perguntando disponibilidade antes de qualquer encaminhamento para agendamento.

- `IGOR_02.5_OBJECAO`  
  Agente responsável por **dúvidas e objeções de valor, convênio, tempo, distância**.

- `IGOR_02_Agente_Atualização de campos`  
  Agente técnico que, a partir de `updates` gerados pelo Orquestrador, atualiza campos no Kommo via Vector Store.

- `IGOR_02.2_AGENDAMENTO`  
  Agente de **Aguardando agendamento** – faz o handoff para atendimento humano:
  - muda status e pipeline no CRM para o pipeline de atendimento humano,
  - envia uma mensagem curta avisando que a equipe irá assumir,
  - a partir daí, o fluxo IA **se desliga** para aquele lead.

Além disso, existe o `default_prompt_6.0`, que é o **bloco base de identidade + tom + informações da clínica**. Ele é injetado em todos os agentes conversacionais (Acolhimento, Qualificação, Objeções, Aguardando agendamento etc.).

---

## 2. Fluxo técnico – do WhatsApp até a resposta

### 2.1 Entrada de mensagem

1. O WhatsApp envia um webhook para o Kommo, que aciona o endpoint do n8n configurado no workflow `IGOR_01_Fluxo_Orquestrador` (node `Webhook1`, path `wa/orchestrator`).
2. O node `Normalize Input`:
   - lê o payload do Kommo,
   - extrai:
     - `lead_id`,
     - `contact_id`,
     - `message` (texto ou informação de anexo),
     - `message_attachment_type`/`message_attachment_link` (voz, imagem, arquivo),
     - `pipeline_atendimento_ia`,
     - `pipeline_atendimento_humano`,
     - ids de campos de CRM (última mensagem, resposta IA etc.),
     - `authorization` (token Kommo),
   - normaliza tudo em um objeto `json` padrão.
3. `Atualizar data ultima mensagem` atualiza, no Kommo, o campo de “última mensagem” com a data da nova interação.
4. `Obter info` + `Lead info` buscam o lead completo no Kommo e parseiam `lead_info` (JSON com campos, nome, status, pipeline, etc.).
5. `Checar pipeline` verifica se o lead está no `pipeline_atendimento_ia`:
   - se **não** estiver, o fluxo desvia para um `No Operation` e termina (lead já está em atendimento humano ou outra etapa);
   - se estiver, o fluxo segue para o caminho IA.

### 2.2 Tratamento de mensagem (texto / áudio / imagem / arquivo)

Dependendo de `message_attachment_type`:

- Texto (`texto`):  
  `Switch Type` envia direto para `Edit Fields12`, que coloca o texto em `message`.

- Áudio (`voice`):  
  `Obter base64 para audio` baixa o áudio, `Transcreve Áudio` (OpenAI) converte para texto; `Edit Fields14` coloca a transcrição em `message`.

- Imagem (`picture`):  
  `Obter base64 para imagem` baixa a imagem, `Analisa Imagem` (OpenAI Vision) gera uma descrição; `Edit Fields16` coloca o texto em `message`.

- Arquivo (`file`):  
  `Obter arquivo` + `Extract from File` + `Message a model` processam o PDF/arquivo e geram texto (ramo ainda menos utilizado).

Todas as variações convergem em `Merge1`, que unifica as mensagens.

### 2.3 Histórico de mensagens (memória curta por lead)

Para cada lead:

1. `Listar Mensagens` (Redis) adiciona a nova `message` na lista associada ao `lead_id`.
2. `Wait` → `Puxar as Mensagens` recuperam a lista completa de mensagens do lead em Redis.
3. `If` verifica se a última mensagem já está na lista para evitar duplicidade.
4. `Merge mensagens` junta todas as mensagens em um único texto com quebras de linha (`mensagem`) e marca `isFluxoPrincipal = true`.
5. `Deleta Mensagem` limpa a lista no Redis (para não crescer indefinidamente).

Esse `mensagem` consolidado é o que o Orquestrador usa como “histórico textual” do lado do lead.

### 2.4 Enriquecimento de contexto e chamada do Orquestrador

1. `Status da pipeline` + `JSON Status` montam um mapa de status do pipeline de **atendimento humano** (para uso posterior no agendamento).
2. `Checar pipeline` garante que estamos no pipeline IA (já descrito).
3. `Default prompt` carrega o `system_prompt` global da Alice (agora `default_prompt_6.0`).
4. `Demux p/ Exec Agents` monta o objeto que será enviado ao Orquestrador:
   - `mensagem` (texto consolidado das falas do lead),
   - `lead_info` (JSON completo do lead),
   - `prompt_atualizacao` (regra 1 de Atualização de campos),
   - status atual do lead (nome, status_id, pipeline_id etc.),
   - `default_prompt` (para os agentes conversacionais),
   - mapa de status/pipelines.
5. `ORCHESTRATOR` recebe:
   - `mensagem`,
   - `lead_info`,
   - `prompt_atualizacao`,
   - e, via `systemMessage`, o conteúdo de `orquestrador_5.0.md`.
   - Ele responde **apenas com JSON**:
     ```json
     {
       "next_agent": "<nome_do_agente>",
       "rationale": "<motivo>",
       "updates": [ { "field": "...", "value": "...", "tool": "..." } ]
     }
     ```
6. `Structured Output Parser` valida e normaliza esse JSON.

### 2.5 Execução dos agentes

- `Demux p/ Exec Agents` injeta `default_prompt` + contexto e entrega ao `Switch`, que distribui conforme `next_agent`:
  - `Acolhimento` → `Exec → Acolhimento` (`IGOR_02.3_ACOLHIMENTO`)
  - `Qualificação` → `Exec → Qualificação` (`IGOR_02.1_QUALIFICACAO`)
  - `Objeções/Valor` → `Exec → Objeções/Valor` (`IGOR_02.5_OBJECAO`)
  - `Localização` → `Exec → Localização`
  - `Escalação/Compliance` → `Exec → Escalação/Compliance`
  - `Nutrição` → `Exec → Nutrição`
  - `Atualização de campos` → `Exec → Atualização de campos` (`IGOR_02_Agente_Atualização de campos`)
  - `Aguardando agendamento` → `Exec → Aguardando agendamento` (`IGOR_02.2_AGENDAMENTO`)

Todos os agentes conversacionais (Acolhimento, Qualificação, Objeções, Localização, Nutrição, Escalação, Aguardando agendamento) recebem sempre:

- `default_prompt_6.0`  
  +  
- o prompt específico do agente (ex.: Qualificador V7).

### 2.6 Saída dos agentes (mensagem de volta ao lead)

Após um agente conversacional responder:

1. O workflow desse agente devolve um campo `output` com a mensagem final (ou mensagens concatenadas com quebras de linha).
2. No fluxo principal:
   - `Edit Fragmenta` move esse `output` para `messages`.
   - `Split \n` quebra o texto em mensagens menores, quando há linhas duplas.
   - `Split Out` gera um item por mensagem.
   - `Loop Over Items` envia cada mensagem:
     - `Atualizar resposta IA` grava o texto no campo de CRM “Resposta IA”.
     - `Enviar mensagem` chama a API `salesbot/run` do Kommo para que o WhatsApp envie a mensagem ao lead.
3. A próxima mensagem do lead volta ao Orquestrador, recomeçando o ciclo.

### 2.7 Caminho especial – Atualização de campos

Quando o Orquestrador retorna `"next_agent": "Atualização de campos"` com `updates`:

1. `Exec → Atualização de campos` chama o workflow `IGOR_02_Agente_Atualização de campos`.
2. O Orquestrador envia, via `When Executed by Another Workflow`, um objeto com:
   - `updates`: array de itens no formato `{ field, value, tool? }`,
   - contexto do lead (`link`, `lead_id`, `authorization` etc.).
3. `Split Out` abre o array `updates`, gerando um item por `{field, value}`.
4. `Loop Over Items` processa cada item individualmente.
5. `If` verifica se `field` é um caso simples de atualização direta:
   - `field.toLowerCase() === "nome"` → rota “Nome”,
   - `field.toLowerCase() === "cidade"` → rota “Cidade”.
6. Para esses casos:
   - **Atualiza nome**: faz PATCH direto no Kommo atualizando o nome do lead com `value`.
   - **Atualiza cidade**: faz PATCH direto no Kommo atualizando o campo customizado de cidade com `value`.
   - Depois, retorna para `Loop Over Items` para processar o próximo update.
7. Para todos os demais campos (ramo “false” do `If`):
   - o item vai para o `AI Agent`, que recebe:
     - o próprio `{field, value}`,
     - o `default_prompt` técnico do agente de atualização (`agente_atualizacao_campos_prompt_n8n.md`),
     - acesso ao Vector Store via `Postgres PGVector Store1` (modo “retrieve-as-tool”),
     - acesso à ferramenta `kommo_update_field` (HTTP tool).
   - O `AI Agent` decide:
     - qual campo corresponde a `field` (usando o Vector Store),
     - se o tipo/valor são coerentes,
     - se deve chamar `kommo_update_field` com `field_id` e `value` normalizado.
8. Ao final do processamento de todos os updates:
   - `Edit Fields1` define `output = "Campos atualizados"`,
   - `Return` devolve esse resultado ao fluxo principal.
9. De volta ao Orquestrador, o fluxo pode:
   - buscar `lead_info` atualizado (`Obter info atualizado` + `Lead info atualizado`),
   - e reavaliar o roteamento com o estado novo.

### 2.8 Caminho de desligamento – Agendamento

Quando o Orquestrador retorna `"next_agent": "Aguardando agendamento"`:

1. `Exec → Aguardando agendamento` chama o workflow `IGOR_02.2_AGENDAMENTO`.
2. Esse workflow:
   - consulta os status do pipeline humano (`Status da pipeline` + `JSON Status`);
   - `Checar Qualificado ou Atendimento IA` garante que o lead está em um dos status preparados para agendar;
   - `Alterar Status AGUARDANDO AGENDAMENTO` atualiza o status do lead no Kommo;
   - `AI Agent` (Agente Aguardando agendamento) envia uma mensagem curta avisando que a equipe humana vai assumir pelo WhatsApp;
   - `Alterar Status e Pipeline` atualiza:
     - `status_id` para `ESCALADO`,
     - `pipeline_id` para `pipeline_atendimento_humano`.
3. Na próxima vez que esse lead enviar mensagem:
   - o Orquestrador, logo no início (`Checar pipeline`), vê que o `pipeline_id` já não é o de atendimento IA;
   - ele desvia para um `No Operation` e não executa mais nenhum agente IA.

**Conclusão:** cair em `Aguardando agendamento` significa **desligar o fluxo IA** e entregar o caso para o time humano.

---

## 3. Roteamento do Orquestrador (regra de decisão)

O Orquestrador é configurado pelo `orquestrador_5.0.md`. De forma resumida:

### 3.1 Entradas

- `mensagem`: histórico consolidado de falas do lead (texto).
- `lead_info`: JSON completo com dados do lead (nome, status, pipeline, campos personalizados etc.).
- `prompt_atualizacao`: regras específicas para detectar quando a mensagem atual é resposta direta a uma pergunta anterior da IA, devendo disparar Atualização de campos.

### 3.2 Ordem de prioridade

Quando decide `next_agent`, o Orquestrador segue esta ordem mental:

1. **Escalação/Compliance**
2. **Atualização de campos** (quando `prompt_atualizacao` pedir)
3. **Acolhimento**
4. **Qualificação**
5. **Aguardando agendamento**
6. **Objeções/Valor**
7. **Nutrição**

### 3.3 Regras principais

- **Escalação/Compliance**  
  Se houver risco, tema médico sensível, queixa séria ou pedido explícito de humano/médico → sempre priorizar Escalação/Compliance.

- **Atualização de campos**  
  Só considerada quando `prompt_atualizacao` estiver preenchido e indicar campos a serem atualizados a partir da mensagem (nome, cidade, objetivo, etc.).

- **Acolhimento**  
  Se `lead_info.name` for vazio ou um placeholder técnico (ex.: “Lead #…”, “Novo lead”), o fluxo deve **sempre** passar por Acolhimento antes de qualquer outra coisa.

- **Qualificação**  
  Usada quando:
  - já existe nome real,
  - não é caso de Escalação/Compliance,
  - não é momento de Atualização de campos como intenção principal,
  - ainda é cedo para Aguardando agendamento,
  - e não é situação típica de Objeções/Valor ou Nutrição.

- **Aguardando agendamento**  
  Só pode ser escolhido quando **todas** as condições abaixo forem verdadeiras:
  1. O lead tem nome real e já foi qualificado (ex.: `lead_info.qualificado = true` ou campos coerentes em `lead_info`).  
  2. A `mensagem` mostra que a pessoa **já recebeu explicação da consulta com valor e condições** (trechos como “R$ 700”, “consulta com bioimpedância e retorno”, “atendimento particular”).  
  3. A `mensagem` também contém **informação de disponibilidade básica** (período do dia, dias da semana ou frases como “qualquer horário serve”).  
  4. A mensagem atual indica **prontidão clara para marcar**, com frases como:
     - “quero marcar”, “quero agendar”, “quero marcar o quanto antes”,
     - “pode marcar”, “pode agendar”, “vamos agendar”,
     - perguntas diretas de dia/horário (“tem vaga amanhã?”, “tem horário na sexta à tarde?”).
  5. Preferencialmente, a iniciativa de marcar vem da pessoa (não apenas uma resposta neutra a uma pergunta da IA).

  Se qualquer ponto acima **não** estiver presente, o Orquestrador **não deve** escolher Aguardando agendamento, mesmo que a pessoa demonstre interesse.  
  Em vez disso, ele mantém o fluxo em Qualificação (ou Objeções/Valor, se o foco for preço/condições).

- **Objeções/Valor**  
  Se a mensagem trouxer dúvida ou objeção clara sobre preço, convênio, formas de pagamento, tempo ou distância, o Orquestrador deve escolher Objeções/Valor.

- **Nutrição**  
  Se a pessoa demonstrar claramente que não quer avançar agora (“só pesquisando”, “talvez depois”, “não quero marcar agora”), o Orquestrador escolhe Nutrição para um fechamento empático.

---

## 4. Lógica conversacional dos agentes principais

### 4.1 Acolhimento

- Objetivo único: **descobrir o nome real** da pessoa.
- Usa `default_prompt_6.0` + prompt específico:
  - abre a conversa de forma cordial,
  - pede o nome em 1 frase,
  - se a pessoa não responder com o nome, responde o que ela trouxe e pede o nome de novo com outra frase.
- Não entra em explicação de consulta, valor ou agendamento.

### 4.2 Qualificação (V7, meio-termo)

- Entra em cena quando:
  - já existe nome real,
  - lead passou pelo Acolhimento (quando necessário),
  - e o Orquestrador entende que é hora de aprofundar objetivo/momento.

- Seu papel:
  - entender objetivo principal,
  - entender rapidamente histórico/tentativas,
  - perceber momento (urgência, insegurança, só pesquisando),
  - explicar a consulta com valor,  
  - perguntar disponibilidade simples (dia/turno),
  - e conduzir a pessoa até a decisão: faz sentido seguir para consulta agora ou não.

- Regras importantes:
  - Para lead quente/urgente: no máximo **duas mensagens** de rapport/exploração antes de ir para:
    1. explicação da consulta + valor,
    2. pergunta de disponibilidade.
  - Quando a pessoa pergunta “como funciona a consulta” ou dá sinais de avaliação séria, o Qualificador **tem obrigação** de:
    - explicar a consulta como avaliação completa (~1h30, bioimpedância no presencial, IMC no online, retorno em 30 dias),
    - incluir sempre o valor R$ 700 e o fato de ser particular,
    - só então seguir com disponibilidade e decisão.
  - Quando a pessoa apenas escolhe formato (“prefiro presencial”, “prefiro online”), o Qualificador:
    - valida a escolha em 1 frase,
    - em seguida pergunta, de forma direta e leve, se faz sentido já organizar a consulta agora ou se ela quer tirar mais alguma dúvida.

### 4.3 Objeções/Valor

- Entra quando:
  - há dúvida ou objeção clara sobre preço, convênio, formas de pagamento, distância ou tempo.
- Responsabilidade:
  - acolher a preocupação,
  - reforçar de forma simples o que está incluído na consulta,
  - explicar:
    - valor (R$ 700),
    - que é particular,
    - formas de pagamento (crédito/débito),
    - e, se a pessoa perguntar, desconto de 5% à vista;
  - checar suavemente se a pessoa vê valor em seguir agora ou prefere pensar.
- Não reabre qualificação nem faz promessas de condições não definidas.

### 4.4 Atualização de campos (Kommo)

- Agente técnico, **não conversa com o paciente**.
- Recebe pares `{field, value}` em `updates` e decide:
  - qual campo (field_id) corresponde,
  - se o valor é compatível,
  - se é seguro atualizar.
- Só chama `kommo_update_field` quando há correspondência clara; em dúvida, **não atualiza**.

### 4.5 Aguardando agendamento

- É acionado apenas quando o Orquestrador decide que o lead está pronto para agendar (seguindo as regras rígidas).
- Responsabilidades:
  - avisar, em 1–2 frases, que a partir dali a equipe humana vai assumir a conversa pelo WhatsApp para combinar dia/horário;
  - não marcar horário, não discutir valor, não reabrir qualificação.
- Workflow técnico:
  - muda status para “AGUARDANDO AGENDAMENTO”,
  - em seguida, muda status para “ESCALADO” e pipeline para atendimento humano.
- A partir desse ponto, o Orquestrador não responde mais; todo o contato passa para o time humano.

---

## 5. Obrigações e deveres do fluxo

De forma consolidada, o fluxo IGOR deve sempre respeitar:

1. **Acolhimento antes de qualquer conversa séria**, se o lead ainda não tiver nome real.  
2. **Explicação da consulta + valor antes de qualquer agendamento**:
   - é obrigatório que o lead saiba:
     - que a consulta é completa e inclui retorno,
     - que o pacote (consulta + bioimpedância presencial + retorno) custa R$ 700,
     - que o atendimento é particular,
     - e a diferença entre presencial e online.
3. **Pergunta de disponibilidade básica (dia/turno) antes de escalar para agendamento**:
   - o Qualificador deve sempre perguntar se é melhor manhã/tarde/noite / semana/fim de semana antes do Orquestrador considerar “Aguardando agendamento”.
4. **Só desligar o fluxo IA quando as condições de agendamento forem satisfeitas**:
   - valor e condições explicados,
   - disponibilidade conhecida,
   - lead verbalizando decisão de marcar,
   - status/pipeline atualizados para o pipeline humano.
5. **Não pular etapas por causa de frases ambíguas**:
   - “quero consultar”, “quero ver como funciona”, “pode ser” etc. não são, sozinhos, motivos para ir direto para agendamento.
6. **Não criar novas regras fora deste documento**:
   - qualquer nova regra de roteamento ou comportamento deve ser refletida aqui, para manter o documento como fonte da verdade.

---

## 6. Como usar este documento para evoluir o fluxo

Quando alguém quiser alterar o fluxo (humano ou IA), deve:

1. **Ler este documento primeiro** para entender:
   - papéis dos agentes,
   - regras do Orquestrador,
   - efeitos de cada decisão (especialmente Aguardando agendamento).
2. **Editar prompts e workflows respeitando estas regras**:
   - default_prompt (identidade, tom, clínica),
   - orquestrador_5.0 (roteamento),
   - prompts de agentes (Qualificação V7, Objeções, Acolhimento, Agendamento).
3. **Garantir que qualquer mudança crítica** (ex.: critérios de agendamento, formas de pagamento, valores) seja refletida neste documento.

Se este documento estiver atualizado, será possível:

- entender a lógica do projeto sem abrir o n8n,
- e fazer alterações coerentes apenas ajustando prompts e parâmetros, sem quebrar a jornada do lead.
