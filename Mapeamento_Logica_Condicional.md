1. Jornada do Usuário — Visão em “camadas”

1.1. Objetivo central do fluxo
	•	Único objetivo macro: conduzir o lead ao agendamento de consulta com o Dr. Igor.
	•	Independente do motivo (emagrecimento, obesidade, estética, reposição hormonal, remédios etc.), o desfecho alvo é sempre consulta.
	•	Papel do agente de IA:
	•	Atuar em todo o pré-atendimento até o momento em que:
	•	O usuário deixa clara a intenção de agendar e
	•	Explicita data ou período desejado (dia específico ou período tipo “manhã/tarde” / “essa semana”).
	•	Depois disso, encerra a parte automática e comunica a transferência para a equipe humana para datas/horários/fechamento.

Esse ponto é crítico: o fluxo não é só “perguntou se quer agendar → passar para humano”. Existe uma camada intermediária de pré-agendamento conversacional, que hoje está mal definida e você já marcou como importante.

⸻

1.2. Macroetapas da jornada

Organizando o que você já descreveu, a jornada pode ser vista assim:
	1.	Detecção e preparação do contexto
	•	Normalização de entrada (texto/áudio/imagem).
	•	Consulta CRM (lead_info, estágio, campos).
	•	Verificação de lacunas: nome, objetivo, dados básicos.
	2.	Boas-vindas / Acolhimento (quando necessário)
	•	Se não há nome, entra Acolhimento.
	•	Pede nome, cria base mínima de relacionamento.
	•	Possível atualização de campo via Agente de Atualização.
	3.	Qualificação consultiva
	•	Nome já identificado.
	•	Entender objetivo, contexto, histórico, disponibilidade, sensibilidade a valor.
	•	Mostrar valor da consulta, não só preço.
	4.	Tratamento de valores/objeções
	•	Quando o lead pede preço diretamente ou demonstra objeção.
	•	Explicação de valor, diferenciais, contexto.
	•	Tentativa única de quebra de objeção (por diretriz explícita sua).
	•	Se o lead, mesmo após isso, não quer seguir → Nutrição/encerramento empático.
	5.	Pré-agendamento (regra que precisa ser ajustada)
	•	Quando o lead demonstra intenção clara de agendar:
	•	Importante: dizer “quero agendar” na primeira mensagem NÃO significa ainda ir pro agendamento.
	•	Intenção válida para avançar só após interação inicial e esclarecimentos.
	•	Nesta etapa, o agente deve:
	•	Confirmar interesse real.
	•	Explorar janela de datas/turno/período.
	•	Quando o lead indica data/período objetivo:
	•	Encerrar atuação do agente.
	•	Transferir para equipe humana com contexto pronto.
	6.	Escalação por compliance/risco
	•	Quando há temas sensíveis, riscos, pedidos fora de escopo ou solicitação explícita por humano.
	•	Encerrar de forma cordial e transferir.
	7.	Nutrição
	•	Quando o lead não está pronto, precisa pensar, não aceita valor ou adia decisão.
	•	Encerra com convite aberto, reforçando valor sem pressão.

⸻

2. Análise dos Agentes e Lógica de Roteamento

2.1. Orquestrador (peça crítica)

Responsabilidade:
	•	Ler mensagem + contexto (CRM + memória).
	•	Decidir qual agente entra:
	•	Atualização de campos
	•	Acolhimento
	•	Qualificação
	•	Aguardando Agendamento
	•	Objeção
	•	Escalação
	•	Nutrição
	•	Lidar com:
	•	Mensagens de múltipla intenção.
	•	Respostas ambíguas.

Dois problemas que o próprio documento já aponta:
	1.	Mensagens com múltiplas intenções
Ex.: “Tenho a intenção de emagrecer e queria saber qual o valor da consulta?”
	•	Precisa acionar:
	•	Atualização de campos (objetivo: emagrecer).
	•	Objeção/Valores (preço).
Ponto importante: o orquestrador NÃO pode tratar isso como “escolher um único agente”.
Ele precisa assumir rotina de:
	•	Identificar TODAS as intenções relevantes.
	•	Definir ordem de tratamento:
	•	Exemplo desejável:
	•	Validar/acolher objetivo → registrar dado → responder sobre valores, já puxando esse objetivo para contextualizar a resposta.
	•	Gerar uma única resposta integrada, não duas respostas robóticas separadas.
	2.	Respostas ambíguas
Exemplo real:
	•	Pergunta: “Você gostaria de seguir para o agendamento ou gostaria de mais explicações sobre a consulta?”
	•	Resposta: “Pode ser”
	•	IA interpretou “seguir para agendamento” e se desligou.
	•	Na prática, a pessoa queria mais explicações.

Aqui a lógica ideal é:
	•	Sempre que a resposta do usuário for compatível com mais de uma interpretação:
	•	O agente deve:
	•	Assumir que NÃO tem certeza.
	•	Fazer pergunta de clarificação simples.
	•	Exemplo:
	•	“Quando você diz ‘pode ser’, você prefere que eu te explique um pouco mais sobre a consulta ou já podemos caminhar para o agendamento?”

Ou seja, o orquestrador precisa ter uma regra transversal de:

“Se a confiança na interpretação da intenção for baixa ou a resposta for vaga, priorizar CLAREZA sobre pressa em avançar”.

⸻

2.2. Atualização de campos
	•	Quando há dados úteis → chama esse agente.
	•	Atualiza CRM com base em vetores de metadados de campos.

Do ponto de vista de lógica conversacional:
	•	Ele é um agente de bastidor.
	•	Não deveria “aparecer” para o paciente.
	•	Implicação: o orquestrador precisa garantir que:
	•	Se for acionar Atualização de campos, isso não quebre o fluxo de conversa.
	•	Ou seja, não deve atrasar ou impedir a resposta ao usuário.

⸻

2.3. Acolhimento
	•	Disparado quando não há nome.
	•	Objetivo:
	•	Quebrar o gelo.
	•	Puxar nome de forma natural.
	•	Quando obtém o nome:
	•	Ideal: já fazer uma micro personalização do próximo passo:
	•	“Pra eu te orientar da melhor forma, me conta rapidinho qual é o seu objetivo hoje: emagrecer, saúde em geral, estética…?”

Aqui a lógica está correta, mas precisa ser muito adaptativa:
	•	Ex.: se o lead já chega dizendo:
	•	“Oi, aqui é a Maria, queria saber como funciona a consulta”
	•	Acolhimento não deve repetir “qual o seu nome?”, e sim reconhecer:
	•	“Maria” já está ali e pular direto para qualificação.

O ponto técnico: essa inteligência está parcialmente na arquitetura, mas precisa estar explicitamente no prompt do orquestrador e do agente de acolhimento.

⸻

2.4. Qualificação

Do documento:
	•	Dois pilares:
	1.	Demonstrar se a pessoa realmente deseja realizar a consulta.
	2.	Verificar se ela continua querendo seguir mesmo depois de conhecer o valor (ou depois da objeção tratada).

Regras específicas úteis:
	•	Se o lead inicia com “quero agendar” logo de cara:
	•	NÃO assumir de imediato prontidão.
	•	Tratar como intenção forte, mas ainda passar pelas etapas mínimas:
	•	Entender brevemente o objetivo.
	•	Explicar como funciona o atendimento.
	•	Só depois checar:
	•	“Quer seguir com a marcação mesmo assim? Posso te orientar sobre os próximos passos”.
	•	Se o lead expressa intenção de agendar após já ter sido contextualizado:
	•	Aqui sim o fluxo pode assumir que é desejo real de avançar.

Ou seja, a lógica precisa diferenciar:
	•	“Quero agendar” na primeira mensagem (ainda em fase de curiosidade).
	•	“Quero agendar” depois de já entender o que é a consulta e ter visto valor.

⸻

2.5. Aguardando Agendamento (regra que você quer mudar)

Situação atual:
	•	Quando: mensagem indica prontidão (“quero agendar”, “pode marcar”, “vamos fechar”).
	•	Ação: informar que humano vai seguir com datas/horários e transferir.

Você quer mudar para:
	•	“Quando” reformulado:
	•	Seguir a lógica do objetivo principal:
	•	O agente atua até a pessoa:
	•	Deixar claro que quer agendar.
	•	Informar ou aceitar período/data.
	•	“Objetivo” mantido:
	•	Transferir para humano, mas apenas depois de já ter o básico de janela de datas/turno.

Nova lógica alvo, em termos conversacionais:
	1.	Lead demonstra intenção clara de agendar (pós-qualificação):
	•	O agente confirma:
	•	“Perfeito, [nome], vamos então caminhar para a marcação.”
	2.	O agente faz pelo menos 1–2 perguntas-chave:
	•	Turno ou dia/período:
	•	“Você prefere manhã ou tarde?”
ou
	•	“Você tem algum dia da semana que seja melhor pra você?”
	3.	Só depois disso:
	•	Quando o lead entrega uma referência de disponibilidade:
	•	“Tenho preferência pela parte da tarde.”
ou
	•	“Queria pra semana que vem.”
	•	O agente encerra sua parte:
	•	Explica que encaminhará para equipe.
	•	Garante que a equipe vai tratar a agenda real com base nesse período.
	•	Ex.: “Vou passar agora sua preferência de [tarde / dia X] para a equipe. Eles vão te chamar aqui mesmo com as opções certinhas de horário, tudo bem?”

Assim, o humano já recebe o lead pré-organizado, e o paciente percebe que o agente realmente conduziu algo, não só “te jogo pra alguém”.

⸻

2.6. Objeções/Valores
	•	Quando há objeções sobre preço, pagamento, convênio, distância, tempo.
	•	Objetivo:
	•	Explicar valor.
	•	Contextualizar.
	•	Tentar quebrar objeção.
	•	Mas sem forçar, com limite de tentativas.

Ponto importante que o fluxo já define bem:
	•	Se após tentar uma vez quebrar objeção o usuário disser que não deseja seguir:
	•	Encerrar com empatia.
	•	Não pressionar.
	•	Encaminhar para Nutrição (ou encerramento definitivo, conforme política).

Essa limitação é saudável para não ficar robótico/insistente.

⸻

2.7. Escalação/Compliance
	•	Disparado quando:
	•	Tema sensível.
	•	Risco.
	•	Pedido fora de escopo.
	•	Pedido explícito de falar com humano.
	•	Papel:
	•	Proteger a clínica.
	•	Manter confiança.
	•	Evitar respostas inadequadas ou fora de competência do agente.

A lógica aqui está correta, mas deve estar amarrada a um conjunto claro de gatilhos no orquestrador (palavras-chave, categorias de intenção, etc.).

⸻

2.8. Nutrição
	•	Quando o lead:
	•	Não está pronto.
	•	Pede tempo.
	•	Não aceita valor.
	•	Agente deve:
	•	Agradecer genuinamente.
	•	Reforçar valor (sem contra-atacar).
	•	Deixar porta aberta (“se mudar de ideia, estou por aqui”).

Essa parte é boa para manter percepção de cuidado mesmo sem conversão imediata.

⸻

3. Gaps Lógicos Relevantes
	1.	Critérios formais de “intenção de agendar”
	•	Hoje está conceitual, mas não parametrizado:
	•	“Dizer que quer agendar” na primeira mensagem não é igual a intenção madura.
	•	Seria útil explicitar, em termos de regra:
	•	Intenção só é válida se:
	•	Já passou por explicação mínima de consulta ou
	•	O lead é recorrente com histórico de consulta anterior.
	2.	Definição exata do “gatilho de passagem” para o humano
	•	O documento diz:
	•	“Quando o usuário informar claramente qual data ou período ele deseja agendar…”
	•	Na prática, isso precisa virar condição estruturada:
	•	Ex.: if has(intent_agendar) AND has(disponibilidade_temporal) → Escalação para equipe de agendamento.
	3.	Tratamento de mensagens ambíguas não está codificado como regra transversal
	•	Você já sabe do problema (“Pode ser”).
	•	Precisa virar padrão:
	•	Sempre que resposta for vaga (pode ser, tanto faz, talvez, quem sabe, acho que sim etc.), o fluxo chama sub-rotina de clarificação.
	4.	Multi-intenção ainda está mal especificado
	•	Exemplo do “emagrecer + valor da consulta”.
	•	Orquestrador precisa de política clara:
	•	Resolver primeiro acolhimento/qualificação e depois objeção?
	•	Ou responder ambas na mesma interação sempre que possível?

⸻

4. Proposta de Lógica “quase-algoritmo” para o Orquestrador

Em formato simplificado:
	1.	Recebe mensagem + contexto.
	2.	Identifica:
	•	tem_nome?
	•	objetivo_conhecido?
	•	intencao_agendar?
	•	pergunta_valor/objeção?
	•	dados_atualizaveis?
	•	risco/compliance?
	•	ambiguidade_resposta?
	•	pronto_para_agendamento?
(intencao_agendar + disponibilidade_temporal)
	3.	Regras de prioridade:
	1.	Se risco/compliance → Escalação.
	2.	Se não tem_nome → Acolhimento.
	3.	Se dados_atualizaveis → Atualização de campos (em paralelo ao próximo passo).
	4.	Se ambiguidade_resposta → Clarificar intenção.
	5.	Se pronto_para_agendamento → Aguardando agendamento (comunicando transferência).
	6.	Se intencao_agendar mas não tem disponibilidade_temporal:
	•	Entrar em modo pré-agendamento:
	•	Fazer perguntas de turno/período/dia.
	7.	Se pergunta_valor/objeção:
	•	Objeção/Valores.
	8.	Caso contrário:
	•	Qualificação.

Essa hierarquia garante:
	•	Segurança/compliance em primeiro lugar.
	•	Depois identificação básica (nome).
	•	Depois enriquecimento silencioso de CRM.
	•	Depois clareza (ambiguidade).
	•	Só então agendamento e objeção/qualificação.