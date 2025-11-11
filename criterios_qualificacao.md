LEAD_QUALIFICADO:

  Critérios_Obrigatórios (AMBOS obrigatórios):

    1. objetivo_claro:
        exemplos: ["emagrecimento", "definição corporal", "perda de peso", "melhorar metabolismo", "reduzir medidas"]
        detalhamento: "Expressou claramente o que deseja alcançar"
        nota: "Pode ter sido mencionado na primeira mensagem ou descoberto na etapa 2"

    2. capacidade_financeira:
        sinais_positivos: ["perguntou sobre formas de pagamento", "não objetou preço", "investimento em saúde", "quando posso agendar"]
        sinais_negativos: ["muito caro", "não tenho condições", "está fora do meu orçamento", "só se aceitar convênio"]
        avaliacao: "Lead não demonstrou objeção financeira forte"

TAGS_PARA_REFINAMENTO (usar como campos personalizados no Kommo):

  Qualificadores_Extras:
    - urgencia_expressa: ["preciso resolver logo", "urgente", "não aguento mais"]
    - tentativas_anteriores: ["já tentei dietas", "fiz tratamento antes", "não funcionou"]
    - perguntas_sobre_metodo: ["como funciona", "qual diferencial", "resultados esperados"]
    - disponibilidade_agenda: ["tenho disponibilidade", "posso comparecer", "flexível horários"]
    - busca_medicacao: ["ozempic", "mounjaro", "medicamentos para emagrecimento"]

LEAD_NÃO_QUALIFICADO:
  
  Desqualificadores_Imediatos:    
    - fora_do_perfil:
        exemplos: ["só quero ganhar peso", "busco psiquiatra", "problema não é nutrologico"]
    
    - sem_capacidade_pagamento:
        declarou: ["não posso pagar", "só se aceitar convênio", "muito acima do orçamento"]
        insiste_desconto: "> 50%"
    
    - curiosidade_sem_interesse:
        indicadores: ["só quero saber", "estou pesquisando", "talvez ano que vem"]
        sem_problema_real: true

LEAD_EM_NUTRIÇÃO (Requer Acompanhamento):
  
  Características:
    - interesse_demonstrado: true
    - objecoes_a_trabalhar:
        tipos: ["preço", "tempo", "distância", "método"]
        quantidade: "1-2 objeções"
    
    - informacoes_incompletas:
        faltando: ["telefone", "problema específico", "urgência"]
        mas_engajado: true
    
    - precisa_confianca:
        sinais: ["quero conhecer melhor", "preciso entender", "tenho dúvidas"]
        potencial: "médio-alto"