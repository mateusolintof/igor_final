# IGOR_FINAL — Lógica do Fluxo de Atendimento IA (Versão Atualizada)

Este documento descreve a lógica operacional do fluxo de automação com agentes de IA de atendimento comercial do Instituto Dr. Igor (nutrólogo), conforme os workflows IGOR_* na instância n8n.  
O foco aqui é **a jornada do usuário** e o comportamento esperado do sistema, alinhados com os prompts e ajustes mais recentes (Orquestrador, Acolhimento, Qualificação, Objeções, Atualização de campos, Agendamento, Nutrição e Escalação/Compliance).

---

## 1. Objetivo Principal do Fluxo

- **Objetivo global:**  
  Qualificar e conduzir o lead ao **agendamento de consulta** com o Dr. Igor.

- **Independente do motivo do lead** (emagrecimento, obesidade, estética, reposição hormonal, uso de medicação, melhora de energia, etc.), o desfecho comercial desejado é sempre o mesmo:
  - **marcar consulta** com o Dr. Igor (presencial ou online, conforme cada caso).

- **Escopo do Agente de IA (do ponto de vista da jornada):**
  - O agente de IA conduz o lead até que:
    1. O lead tenha entendido **o que é a consulta** (incluindo o valor e o formato do atendimento), e  
    2. O lead tenha demonstrado **desejo real de marcar** depois de conhecer essas informações, e  
    3. Exista pelo menos uma noção de **preferência de dia/período** (por exemplo: manhã/tarde/noite, semana/final de semana, ou uma data específica).
  - A partir desse ponto, o fluxo aciona o Agente de Agendamento, que:
    - se “desliga” do diálogo comercial,
    - informa de forma clara que a conversa seguirá com a equipe humana,
    - e prepara o lead para receber opções de datas/horários e próximos passos.

---

## 2. Premissas

- Atender leads via WhatsApp de forma:
  - **empática**,  
  - **consultiva**,  
  - **clara** e **sem linguagem de robô**.

- O fluxo deve se adaptar às nuances e respostas do usuário:
  - **não** é para seguir um “roteiro duro”,
  - mas existe um **norte lógico** (nome → objetivo → valor → prontidão → disponibilidade → encaminhamento).

- Princípios de atuação:
  - Apresentar valor de forma concreta (consulta, retorno, bioimpedância, acompanhamento, personalização).
  - Tratar objeções com clareza e transparência, sem pressão e sem prometer o que não existe.
  - Atualizar campos no CRM sempre que houver dados relevantes, respeitando regras de segurança (melhor não atualizar do que gravar algo errado).
  - Manter memória contextual entre mensagens e preservar a experiência do lead como se fosse um único diálogo contínuo.

- Limite de escopo:
  - A IA **não receita**, **não discute diagnóstico** e não entra em temas médicos sensíveis; nessas situações, transfere para humano (Escalação/Compliance).

---

## 3. Visão Geral do Fluxo Técnico

1. **Ponto de entrada**
   - Webhook `wa/orchestrator` → workflow **IGOR_01_Fluxo_Orquestrador**.

2. **Normalização da entrada (multimodal)**
   - Texto: segue direto como `mensagem`.
   - Áudio:
     - download,
     - transcrição com modelo de voz (Whisper/OpenAI),
     - transcrição vira `mensagem`.
   - Imagem:
     - download,
     - análise (vision) se aplicável,
     - resumo vira `mensagem`.

3. **Enriquecimento com CRM (Kommo)**
   - Busca de `lead_info`:
     - nome,
     - campos customizados (objetivo, cidade, canal, etc.),
     - status/pipeline,
     - flags como “qualificado”, quando existirem.
   - Atualização de metadados:
     - ex.: “data da última mensagem”.

4. **Decisão de roteamento**
   - O **Orquestrador** (LLM) recebe:
     - `mensagem`,
     - `lead_info`,
     - `prompt_atualizacao` (quando houver).
   - Com base nas regras de roteamento, decide:
     - `"next_agent"` (Acolhimento, Qualificação, Objeções/Valor, Atualização de campos, Aguardando agendamento, Nutrição, Escalação/Compliance),
     - `"updates"` (quando houver dados para atualizar no CRM).

5. **Execução do agente**
   - O fluxo chama o sub-workflow correspondente (ex.: `IGOR_02.1_QUALIFICACAO`) via `Execute Workflow`.
   - O agente:
     - recebe o contexto,
     - gera a resposta ao paciente (mensagem WhatsApp),
     - quando aplicável, produz saídas para atualização de campos (encaminhadas ao Agente de Atualização de campos).

6. **Entrega ao WhatsApp e memória**
   - A resposta é fragmentada em mensagens curtas (natural, sem parecer parede de texto).
   - A memória da conversa (paciente e IA) é persistida em Postgres:
     - isso permite que os agentes conheçam o histórico nas próximas interações.

---

## 4. Agentes e Regras de Roteamento (Visão Atual)

A prioridade lógica é:

1. Escalação/Compliance  
2. Atualização de campos (quando `prompt_atualizacao` exigir)  
3. Acolhimento  
4. Qualificação  
5. Aguardando agendamento  
6. Objeções/Valor  
7. Nutrição  

### 4.1. Orquestrador

- Papel:
  - Ser o “cérebro” que conecta:
    - **intenção da mensagem atual**,
    - **estado do lead no CRM**,
    - **regras de atualização de campos**,
    - **estágio da jornada** (iniciante, em qualificação, pronto, em objeção, etc.).
- Responsabilidades principais:
  1. Entender se a mensagem é do paciente ou técnica do sistema.
  2. Verificar se o lead já tem **nome real** ou apenas placeholder.
  3. Verificar se existe instrução de **atualização de campos** (`prompt_atualizacao`) aplicável.
  4. Identificar situações de **risco/compliance** (colocadas sempre em primeiro lugar).
  5. Decidir qual agente vai atuar a seguir, com justificativa (`rationale`).
- Casos com **múltiplas intenções**:
  - Ex.: “Tenho intenção de emagrecer e queria saber o valor da consulta.”
  - O Orquestrador avalia:
    - se o lead já está ou não qualificado,
    - se já recebeu explicação de valor,
    - se é momento de:
      - aprofundar objetivo (Qualificação),
      - ou tratar objeção/dúvida de valor (Objeções/Valor),
      - ou ainda atualizar campos (se a mensagem trouxe dados objetivos).
  - A regra é sempre priorizar o **tópico mais crítico para avançar na jornada**, respeitando a ordem de prioridade geral.

- Ambiguidade:
  - Respostas como “pode ser”, “acho que sim”, “tanto faz” **não são tratadas como confirmação de agendamento**.
  - Nessas situações, o Orquestrador tende a reenviar para **Qualificação** para que o agente esclareça a intenção, em vez de pular direto para agendamento.

---

### 4.2. Agente de Atualização de campos (IGOR_02_Agente_Atualização de campos)

- **Quando entra:**
  - Quando `prompt_atualizacao` estiver ativo para aquela mensagem,
  - e quando a mensagem (ou o contexto) trouxer informação que preenche ou atualiza campos do CRM, como:
    - objetivo principal,
    - cidade,
    - canal de origem,
    - preferências específicas,
    - etc.

- **Objetivo:**
  - Identificar **com segurança** qual campo do CRM deve ser atualizado,
  - normalizar o valor conforme o tipo de campo (select, boolean, texto, número, data),
  - e acionar a ferramenta de atualização (`kommo_update_field`) apenas quando houver alta confiança.

- **Comportamento-chave:**
  - Usa uma base vetorial (PGVector) com metadados dos campos.
  - Prioriza:
    - match exato de slug,
    - depois aliases/nome muito próximo,
    - só então similaridade semântica forte.
  - Se o match for fraco ou ambíguo → **não atualiza**.
  - Em caso de dúvida, é preferível **não gravar** do que gravar errado.

---

### 4.3. Acolhimento (IGOR_02.3_ACOLHIMENTO)

- **Quando entra:**
  - Sempre que o lead ainda **não tiver um nome real**:
    - `lead_info.name` vazio, nulo ou ausente;
    - ou for placeholder técnico (ex.: “Lead #18460025”, “Novo lead”, “Contato”, só números, etc.).

- **Objetivo:**
  - Iniciar o atendimento de forma simples, cordial e humana.
  - Pedir ou confirmar o nome da pessoa.
  - Caso a pessoa já se apresente (“Oi, aqui é a Carla…”), o agente:
    - **não repete a pergunta**,
    - apenas reconhece o nome e segue a conversa.

- **Importante:**
  - Acolhimento não decide agendamento nem valor.
  - Ele prepara o terreno para que **Qualificação** possa entrar com mais contexto (nome real + leve aquecimento da relação).

---

### 4.4. Qualificação (IGOR_02.1_QUALIFICACAO)

- **Quando entra:**
  - Já existe um **nome real** registrado (de acordo com o critério do Orquestrador),
  - não é caso de Escalação/Compliance,
  - não é momento de Atualização de campos como intenção principal,
  - ainda **não** é momento de Aguardando agendamento (vide seção 4.5),
  - e não há uma objeção de valor dominante no momento.

- **Objetivo principal:**
  - Conduzir uma conversa consultiva que:
    - entenda **o objetivo principal** do lead (ex.: emagrecer 12 kg até o casamento),
    - conecte esse objetivo com o tipo de acompanhamento que o Dr. Igor oferece,
    - apresente o valor da consulta **na hora certa**,
    - valide se a pessoa realmente quer avançar para a consulta **depois de saber o valor**.

- **Pilares da qualificação:**
  1. **Intenção real de consulta**  
     - Se o lead iniciar a conversa dizendo:
       - “Oi, quero agendar uma consulta com o Dr. Igor”,
     - isso é tratado como **forma de abrir o contato**, não como prontidão final.
     - O agente conversa normalmente, entende objetivo, explica consulta e valor.
     - Só depois dessa etapa, quando o lead se mantém interessado, é que o fluxo caminha para agendamento.

  2. **Aceite após valor**  
     - O agente explica claramente a consulta (presencial/online), com:
       - o que acontece na consulta,
       - retorno,
       - bioimpedância (quando presencial),
       - valor e condição particular (sem convênio).
     - Se, **depois** disso, a pessoa demonstra que quer seguir (“quero marcar mesmo assim”, “faz sentido pra mim”, etc.), isso é entendido como prontidão real.

- **Explicação da consulta (sempre com valor e formato correto):**
  - Base fixa usada pelo Qualificador:
    - **Consulta + Bioimpedância + Retorno (30 dias): R$ 700,00.**
    - **Atendimento EXCLUSIVAMENTE PARTICULAR** (não atendemos convênios).
    - **Atendimento presencial:** em Feira de Santana e Euclides da Cunha.
    - **Atendimento online:** disponível para pacientes de qualquer cidade.
    - Pacientes de outras cidades **podem escolher presencial** se preferirem.
    - **Bioimpedância:** só nas consultas presenciais.
    - **Consultas online:** sem bioimpedância, mas incluem:
      - cálculo detalhado de IMC,
      - avaliação completa e personalizada a partir das informações do paciente.

  - **Regra de padrão:**  
    - O padrão assumido é **presencial**.  
    - O agente **não pergunta espontaneamente** “você prefere presencial ou online?”.  
    - Só fala em online quando:
      - o lead pergunta sobre atendimento online/distância,
      - ou o lead expressa claramente preferência por atendimento online.

  - **Quando o lead pede “me explica como funciona a consulta”:**
    - O agente deve:
      1. Explicar o que acontece na consulta (avaliação, bioimpedância se presencial, retorno).
      2. Informar **o valor** (R$ 700,00).
      3. Deixar claro que é **particular**.
      4. Deixar clara a diferença entre presencial x online em relação à bioimpedância.
      5. Finalizar com uma frase leve, abrindo espaço para dúvidas ou próximos passos.

- **Quando o lead diz “quero marcar” (dentro da Qualificação):**
  - O agente **não “confirma” a consulta** nem dá horário.
  - Em vez disso:
    - valida a decisão positivamente,
    - faz uma **pergunta simples sobre disponibilidade** (dia/turno), ex.:
      - “Você costuma ter mais disponibilidade de manhã, à tarde ou à noite?”
      - “Você se organiza melhor durante a semana ou no fim de semana?”
  - Essa informação de disponibilidade é importante para o Orquestrador entender que:
    - o lead já **quer marcar** e
    - já há uma ideia básica de **quando**.

---

### 4.5. Aguardando agendamento (IGOR_02.2_AGENDAMENTO)

> Este é um ponto crítico do fluxo.

- **Objetivo do agente de Agendamento:**
  - Avisar de forma clara e humanizada que:
    - a conversa seguirá com a equipe de agendamento,
    - a equipe vai enviar opções de datas/horários e próximos passos,
  - “Desligar” o agente de IA, de forma coerente com o contexto.

- **Quando o Orquestrador deve mandar para Aguardando agendamento:**

  1. **Condição estrutural:**
     - O lead tem **nome real** (não placeholder),  
     - há sinais de que o lead **já foi qualificado**, ou seja:
       - objetivo principal está claro e faz sentido com o serviço,
       - o lead já recebeu explicação da consulta **incluindo o valor**,  
       - não há objeção relevante de preço/convênio em aberto.

  2. **Condição de prontidão real:**
     - Após saber o valor, o lead demonstra de forma clara que **quer seguir com a consulta**, com frases como:
       - “quero marcar mesmo assim”,
       - “quero marcar o quanto antes”,
       - “faz sentido pra mim, quero sim”,
       - etc.

  3. **Condição de disponibilidade mínima (dia/turno):**
     - Já existe na conversa (ou em `lead_info`) alguma indicação de:
       - preferência de dia (semana/final de semana, terça, sexta, etc.),
       - ou preferência de turno (manhã, tarde, noite),
       - ou data/horário sugeridos pelo próprio lead.
     - Ex.: “consigo à tarde”, “depois do trabalho à noite”, “durante a semana”, “pode ser terça à tarde”.

- **Regra importante:**
  - Se o lead disser “quero marcar”, “quero marcar o quanto antes”, etc., mas **ainda não houver nenhuma indicação de disponibilidade** (dia/turno/dia-horário):
    - o Orquestrador **não** manda direto para Aguardando agendamento;
    - ele mantém o fluxo em **Qualificação**, para o agente fazer a tal pergunta simples sobre disponibilidade.
  - Somente depois que houver:
    - intenção clara de marcar **pós-valor**  
    - **e** pelo menos uma noção de disponibilidade,
    - o Orquestrador envia para **Aguardando agendamento**.

---

### 4.6. Objeções/Valores (IGOR_02.5_OBJECAO)

- **Quando entra:**
  - Quando, no contexto, surgem objeções ou dúvidas claras relacionadas a:
    - preço/valor,
    - formas de pagamento,
    - convênio/plano de saúde,
    - tempo,
    - distância ou logística.

- **Objetivo:**
  - Esclarecer de forma transparente,
  - contextualizar o valor da consulta e do acompanhamento,
  - reforçar diferenciais reais (sem exageros),
  - e verificar se o lead mantém interesse após entender o que está sendo oferecido.

- **Regras importantes:**
  - Não oferece desconto por conta própria.
  - Não promete parcelamentos, condições especiais ou convênios inexistentes.
  - Mantém tom empático:
    - se, mesmo após uma tentativa honesta de esclarecimento, o lead disser que não tem condição ou que não quer seguir, o agente:
      - agradece,
      - encerra com respeito,
      - pode encaminhar para Nutrição, se fizer sentido.

---

### 4.7. Escalação/Compliance (IGOR_02.4_ESCALACAO)

- **Quando entra:**
  - Quando há:
    - termos de risco (“passando mal”, “dor forte”, “reação séria”),
    - temas de diagnóstico/medicação/sintomas que fogem do escopo comercial,
    - queixa relevante sobre o atendimento,
    - pedido explícito para falar com humano ou com o médico.

- **Objetivo:**
  - Encerrar o uso da IA naquele contexto,
  - informar ao lead que será atendido por alguém da equipe,
  - encaminhar a demanda para a equipe humana.

- **Função na jornada:**
  - Proteger o paciente,
  - proteger o Instituto,
  - garantir que temas sensíveis sejam tratados diretamente por humanos.

---

### 4.8. Nutrição (IGOR_02.6_NUTRICAO)

- **Quando entra:**
  - Quando o lead demonstra de forma clara que **não está pronto para avançar agora**, sem que haja uma objeção específica a ser trabalhada naquele momento.
  - Exemplos:
    - “Só estou pesquisando por enquanto.”
    - “Talvez mais pra frente.”
    - “Ainda não decidi.”
    - “Vou pensar melhor antes.”

- **Objetivo:**
  - Encerrar a conversa de forma:
    - leve,
    - empática,
    - sem pressão,
  - reforçar:
    - valor do acompanhamento,
    - abertura para retomar contato no futuro.

---

### 4.9. Localização

- A lógica original citava um agente separado de “Localização”.  
- Na prática atual:
  - a localização (cidade) é tratada como **campo a ser capturado/atualizado** (via Qualificação + Atualização de campos),
  - não existe um agente separado dedicado apenas a isso.

---

## 5. Exemplos de Jornada do Usuário (Atualizados)

### 5.1. Novo lead sem nome

1. Lead envia primeira mensagem: “Oi, quero saber como funciona.”
2. `lead_info.name` é placeholder (ex.: “Lead #1846…”).
3. Orquestrador:
   - detecta ausência de nome real → envia para **Acolhimento**.
4. Acolhimento:
   - se apresenta brevemente,
   - pede o nome de forma simples.
5. Lead manda: “Sou a Carla.”
6. Orquestrador:
   - vê nome real,
   - encaminha para **Qualificação** nas próximas mensagens.

---

### 5.2. Lead existente pedindo preço

1. Lead já tem nome real e algum histórico.
2. Mensagem: “Queria saber o valor da consulta.”
3. Orquestrador:
   - identifica intenção de valor → **Objeções/Valor** (ou Qualificação + módulo de explicação, conforme contexto de objetivo).
4. Agente:
   - explica a consulta,
   - informa o valor,
   - reforça que é particular,
   - mostra de forma simples como o acompanhamento funciona.

---

### 5.3. Lead dizendo “quero marcar” (após conhecer o valor)

1. Lead passou por Qualificação,
2. Já entendeu consulta, formato e valor,
3. Diz: “Quero marcar o quanto antes.”
4. Se **não houver nenhuma informação de disponibilidade**:
   - Orquestrador manda para **Qualificação** novamente.
   - Qualificação:
     - valida,
     - pergunta: “Você costuma ter mais disponibilidade de manhã, à tarde ou à noite?”
5. Lead responde: “À tarde, durante a semana.”
6. Orquestrador:
   - já tem:
     - nome real,
     - qualificação,
     - aceitação após valor,
     - disponibilidade básica,
   - agora encaminha para **Aguardando agendamento**.
7. Agente de Aguardamento agendamento:
   - agradece,
   - explica que a equipe de agendamento vai assumir,
   - e “desliga” a IA de forma natural.

---

### 5.4. Lead informando dados (ex.: “meu objetivo é emagrecimento”)

1. Mensagem: “Meu objetivo é emagrecer uns 10 kg até o casamento.”
2. `prompt_atualizacao` orienta que objetivo principal deve ser extraído.
3. Orquestrador:
   - pode acionar **Atualização de campos** para registrar objetivo no CRM,
   - depois segue com **Qualificação** (para aprofundar contexto e apresentar valor).

---

### 5.5. Lead desinteressado agora, mas aberto no futuro

1. Depois de entender valor e funcionamento, lead diz:
   - “Por enquanto não vou conseguir, vou deixar pra depois.”
2. Orquestrador:
   - entende que não é objeção específica a ser trabalhada agora,
   - direciona para **Nutrição**.
3. Agente de Nutrição:
   - encerra de forma respeitosa,
   - reforça que a porta fica aberta,
   - pode sugerir continuar acompanhando os conteúdos do Instituto.

---

## 6. Comportamentos Transversais

- **Tom de voz:**
  - claro, respeitoso, empático e consultivo,
  - sem formalismo excessivo,
  - sem parecer texto de IA (frases curtas, diretas, cotidianos).

- **Evitar repetição:**
  - não repetir explicações extensas se o lead já demonstrou que entendeu,
  - evitar perguntar duas vezes a mesma coisa (nome, por exemplo).

- **Consistência com o CRM:**
  - usar as informações de `lead_info` para:
    - não perguntar o que já se sabe,
    - adaptar a conversa ao que já foi dito.

- **Percepção de valor:**
  - sempre que falar de preço, reforçar:
    - o que a consulta inclui,
    - o acompanhamento,
    - o benefício concreto para o objetivo do paciente.

---

## 7. Memória, Persistência e Entrega

- **Memória de conversa:**
  - Persistida em Postgres,
  - permite que os agentes atuais “leiam” o histórico recente e respondam com continuidade.

- **Filas e processamento:**
  - Há controle por lead (WhatsApp) para evitar concorrência de múltiplas mensagens; a lógica atual busca processar as mensagens desse lead em sequência.

- **Fragmentação da resposta:**
  - Respostas dos agentes podem ser quebradas em blocos pequenos, enviadas em sequência no WhatsApp para manter a leitura leve.

- **Atualizações de CRM:**
  - Além de atualizar campos de qualificação, o fluxo registra “data da última mensagem” e respeita o estágio do pipeline.

---

## 8. Encerramento e Próximas Etapas

- O fluxo pode encerrar de três grandes formas:

  1. **Encaminhamento para equipe de agendamento**  
     - Quando o lead está qualificado, viu valor, aceitou o preço, indicou disponibilidade e quer marcar.

  2. **Escalação/Compliance**  
     - Quando há risco, queixa séria ou tema médico sensível.

  3. **Nutrição**  
     - Quando o lead não está pronto para avançar agora, mas a relação pode ser mantida de forma leve.

- Sempre que dados-chave faltarem (nome, objetivo, entendimento de valor), o Orquestrador prioriza voltar para:
  - **Acolhimento** (nome),
  - **Qualificação** (objetivo e conexão com a consulta),
  - ou **Atualização de campos** (quando houver instruções específicas), mantendo o fluxo coerente com a jornada humana.

---