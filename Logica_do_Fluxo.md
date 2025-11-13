# IGOR_FINAL — Lógica do Fluxo de Atendimento IA

Este documento descreve a lógica operacional do fluxo de automação com agentes de IA de atendimento comercial do Instituto Dr. Igor (nutrólogo), conforme os workflows IGOR_* na instância n8n. O foco aqui é a jornada do usuário e o comportamento esperado do sistema.

## Objetivo Principal do Fluxo
- Qualificar e Conduzir o lead ao Agendamento de Consulta com o Dr. Igor. 
  - Independente da necessidade ou objetivo do paciente (emagrecimento, obesidade, estética, reposicao hormonal, tomar medicamentos e etc..) o objetivo é agendar a consulta com o Dr. Igor.
  - O Agente de IA irá atuar até o momento em que o usuário informar de forma clara qual data ou período ele deseja agendar, apos ele demonstrar de forma clara o desejo de agendar.
  Exemplos (não se limite à esses exemplos),
  O agente irá perguntar: "Você tem preferência de turno para realizar a consulta? Na Parte da manhã ou da tarde"
  ou
  O usuário irá informar ou perguntar se teria disponibilidade de horário em tal data, mesmo que o agente ainda nao tenha perguntado. 

  Apos essa interacao e o agente ter total clareza de que foi realizado a etapa final de seu objetivo, ele irá informar ao usuario que irá passar para a Equipe responsável que irá informar sobre as datas e os proximos passos.

## Premissas
- Atender leads via WhatsApp de forma empática e consultiva.
- Se adaptar as nuances e interacoes do usuário, nao seguindo um passo a passo rígido 
  - Obs: Necessário ter um passo a passo para que o agente tenha um norteamento.
- Apresentar valor e tratar objeções com clareza e direcionamento, quando necessário e sem forçar a barra.
- Atualizar campos no CRM conforme surgirem dados relevantes.
- Manter memória contextual entre mensagens e preservar a experiência.

## Visão Geral do Fluxo
- Ponto de entrada: webhook `wa/orchestrator` (IGOR_01_Fluxo_Orquestrador).
- Mensagens podem ser texto, áudio ou imagem (multimodal). O orquestrador normaliza a entrada:
  - Texto: segue direto para decisão.
  - Áudio: obtém base64 + transcreve (OpenAI Whisper).
  - Imagem: obtém base64 + faz análise de conteúdo (vision).
- Enriquecimento: o orquestrador consulta o CRM para:
  - Buscar informações do lead (ex.: nome, campos de qualificação, estágio/pipeline).
  - Atualizar metadados como “data da última mensagem”.
- Decisão: um agente “ORCHESTRATOR” (LLM) decide qual agente especialista deve responder com base na mensagem e no contexto do lead.
- Execução: o orquestrador dispara o sub-workflow do agente escolhido (executeWorkflow) e recebe a resposta estruturada.
- Entrega: a resposta é fragmentada em partes curtas e enviada ao WhatsApp. A memória de conversa é persistida para manter contexto.

## Agentes e Regras de Roteamento (prioridade)

1) Orquestrador
- As regras são decididas pelo orquestrador, que considera mensagem, lacunas de dados, estágio do lead e sinais de intenção.
- É essencial que o orquestrador consiga identificar possível duplicidade de intenção ou resposta do usuário para que ele responda ambas as perguntas/respostas.
Exemplo: 
  - O usuario pode enviar uma mensagem assim: "Tenho a intencao de emagrecer e queria saber qual o valor da consulta?"
    - Isso demanda ação de dois agentes, como que a IA poderia agir para nao errar?
- Evitar ambiguidade de perguntas e ambiguidade de respostas. Se resposta ambigua, confirmar a intencao do usuario.
Exempo de uma situacao que aconteceu:
  - O agente perguntou assim: "Voce gostaria de seguir para o agendamento ou gostaria de mais explicacoes sobre a consulta"
  - O usuario respondeu: "Pode ser"
    - A IA entendeu que ele queria seguir para o agendamento e se desligou, sendo que na verdade ele queria mais explicacoes sobre a consulta.

2) Atualização de campos (IGOR_02_Agente_Atualização de campos)
- Quando: a mensagem contém dados para atualizar no CRM (ex.: nome, cidade, objetivo, preferências, etc.).
- Objetivo: identificar o campo correto e atualizar o valor no CRM, com checagens e normalizações.
- Comportamento: o agente consulta uma base vetorial de metadados dos campos e escolhe o melhor candidato por similaridade (preferindo correspondência por slug), depois chama ferramentas de atualização no CRM.

3) Acolhimento (IGOR_02.3_ACOLHIMENTO)
- Quando: não há nome do lead registrado em `lead_info.name`.
- Objetivo: iniciar o atendimento e pedir o nome de forma cordial e personalizada.
- Resultado esperado: obter o nome e registrar no CRM (o orquestrador poderá acionar atualização de campos quando aplicável).

4) Qualificação (IGOR_02.1_QUALIFICACAO)
- Quando: o nome já foi identificado e há necessidade de aprofundar o entendimento.
- Objetivo: conduzir uma conversa consultiva, coletando dados essenciais (objetivo principal, investimento, disponibilidade, histórico, preferências) e apresentar valor quando necessário (personalização, abordagem científica, acompanhamento, resultados sustentáveis).
  - A qualificacao segue dois pilares: 
    - demonstracao clara de que deseja realizar uma consulta (IMPORTANTE lembrar que se o usuario iniciar a conversa falando: "ola, quero agendar uma consulta com Dr. Igor", nao significa que ele ja deseja ir para o agendamento. Portanto o agente deve interagir normal. Mas caso isso seja falado apos interacoes iniciais, aí sim, pode assumir que ele deseja avancar)
    - demonstrar que deseja seguir com o agendamento mesmo apos receber as informacoes de valores (ou seja, o usuario nao teve objecao ao valor e se teve e o agente conseguiu quebrar essa objecao, segue para os proximos passos. Caso mesmo apos tentar uma vez quebrar essa objecao o usuario informe que nao deseja seguir, o Agente deve agradecer de forma empatica.)

5) Aguardando agendamento (IGOR_02.2_AGENDAMENTO) - ITEM IMPORTANTISSIMO
ATUALMENTE É ASSIM (mas precisamos mudar):
- Quando: a mensagem indica prontidão para marcar (ex.: “quero agendar”, “pode marcar”, “vamos fechar”).
- Objetivo: informar que um atendente humano dará sequência ao agendamento com as informacoes de data e horário e proximos passos. E o Agente deve transferir/escalonar para a equipe.
MUDANÇA NECESSÁRIO:
- Quando: Deve seguir a logica do objetivo principal do fluxo informado no inicio desse documento.
- Objetivo (mantem): informar que um atendente humano dará sequência ao agendamento com as informacoes de data e horário e proximos passos. E o Agente deve transferir/escalonar para a equipe.

6) Objeções/Valores (IGOR_02.5_OBJECAO)
- Quando: há objeções explícitas (preço, formas de pagamento, tempo, convênio, distância) no contexto da conversa.
- Objetivo: orientar transparentemente, contextualizar valor versus custo, oferecer alternativas e reforçar diferenciais.

7) Escalação/Compliance (IGOR_02.4_ESCALACAO)
- Quando: há necessidade de transferência por regras de compliance, risco, sensibilidade do caso ou solicitação do lead.
- Objetivo: encerrar de forma cordial e transferir para um atendente humano.

8) Nutrição (IGOR_02.6_NUTRICAO)
- Quando: o lead não está pronto para avançar, mostra desinteresse momentâneo ou pede tempo para decidir.
- Objetivo: encerrar com empatia, reforçar valor e convidar a continuar acompanhando/conversando sem pressão.

9) Observação: o orquestrador também referencia “Localização”. Caso seja aplicável ao contexto, pode direcionar para rotinas que pedem/endereço/urbe, mas não há um workflow IGOR_* dedicado separado com esse nome.

## Jornada do Usuário — Exemplos
- Novo lead sem nome:
  - Orquestrador detecta ausência de `lead_info.name` → aciona Acolhimento → solicita nome.
  - Ao obter nome, segue para Qualificação nas próximas mensagens.

- Lead existente pedindo preço:
  - Orquestrador identifica intenção → aciona Objeções/Valores.
  - Resposta orienta sobre valor, diferenciais e próximos passos sem pressionar.

- Lead dizendo “quero marcar”: (PRECISAMOS ALTERAR)
  - Orquestrador identifica prontidão → aciona Aguardando agendamento.
  - Informa transferência para humano para finalizar o agendamento.

- Lead informando dados (ex.: “meu objetivo é emagrecimento”):
  - Orquestrador prioriza Atualização de campos para registrar no CRM.
  - Em seguida, retorna ao diálogo (ex.: Qualificação) já com contexto atualizado.

- Lead desinteressado agora, mas aberto no futuro:
  - Orquestrador aciona Nutrição.
  - Mensagem encerra de forma positiva, reforçando valor e abertura para retomar.

## Comportamentos Transversais
- Tom de voz: claro, respeitoso, empático e consultivo.
- Evitar repetição: não repetir informações já explicadas.
- Consistência: alinhar respostas ao estágio do lead e às informações do CRM.
- Gerar percepcao de valor e quebrar objecoes quando necessário

## Persistência, Memória e Entrega
- Memória de conversa: persistida em Postgres para manter histórico/contexto entre mensagens.
- Filas e espera: há controle de fila e espera para processar mensagens sequencialmente e evitar respostas duplicadas.
- Fragmentação de resposta: as mensagens do agente podem ser quebradas em partes menores para envio ao WhatsApp.
- Atualizações CRM: o fluxo atualiza “data da última mensagem”, busca/atualiza campos e verifica status da pipeline.

## Encerramento e Próximas Etapas
- Quando apropriado, o fluxo encerra com encaminhamento ao humano (agendamento/escalation) ou com mensagem de nutrição.
- Caso dados-chave faltem, o orquestrador volta a priorizar coleta/atualização de campos.

