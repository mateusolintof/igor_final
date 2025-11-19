# Exemplo de interação completa até **Aguardando agendamento**

Este exemplo mostra uma conversa do início ao fim, cobrindo **todos os requisitos obrigatórios** para o Orquestrador poder rotacionar para o agente **Aguardando agendamento**:

- nome real já definido,
- lead qualificado,
- consulta explicada com **valor e condições**,
- alguma **disponibilidade básica** (turno/dia),
- prontidão **clara** para marcar.

> Observação: os trechos entre colchetes `[...]` são comentários técnicos para quem está lendo o fluxo. Eles **não** aparecem para o lead.

---

## 1. Acolhimento – captura do nome

**Lead:** Oi, queria saber sobre consulta com o Dr. Igor.  
**Alice (Acolhimento):** Oi, tudo bem? Como você prefere que eu te chame?  
**Lead:** Me chamo Carla.

[Depois disso, o campo de nome é atualizado (se preciso) e o Orquestrador entende que já existe **nome real**. Na próxima interação, ele pode mandar para **Qualificação**.]

---

## 2. Qualificação – objetivo, contexto e momento

**Alice (Qualificação):** Pra eu te orientar direitinho, Carla, qual é seu objetivo principal hoje? Você está mais focada em emagrecimento, definição corporal, reposição hormonal ou outro ponto?  
**Lead:** Meu foco é emagrecimento. Quero perder uns 10kg até o fim do ano.  
**Alice:** Entendi. Você já tentou algum acompanhamento ou dieta estruturada antes, ou seria a primeira vez com um médico voltado pra isso?  
**Lead:** Já fiz dieta por conta própria, mas nunca com acompanhamento profissional.  
**Alice:** Faz sentido, muita gente só percebe a diferença quando tem um plano realmente individualizado. E pensando no seu momento agora: você sente que quer começar logo esse processo ou ainda está só pesquisando?
  
**Lead:** Quero começar logo, não quero deixar pra depois.

[Aqui o lead já está **qualificado**: objetivo claro (emagrecimento), contexto básico e sinal de **urgência/prontidão** (“quero começar logo”). O Orquestrador pode manter em **Qualificação** para explicar a consulta.]

---

## 3. Explicação da consulta – com **valor e condições**

**Alice (Qualificação):** Perfeito. Vou te explicar rapidinho como funciona a primeira consulta com o Dr. Igor, tá?  
Na consulta presencial, ele reserva em torno de 1h30 só pra você, pra entender seu histórico, rotina e objetivos com calma. Antes, você faz o exame de bioimpedância aqui na clínica, que mostra em detalhes sua composição corporal (gordura, músculo, retenção, gordura visceral...). Com isso e com o que você me contou, ele monta um plano totalmente individualizado, e você ainda tem um retorno em até 30 dias pra ajustar o que for preciso.  
O pacote completo — consulta presencial + bioimpedância + retorno em até 30 dias — fica em **R$ 700,00**, em atendimento **exclusivamente particular** (não atendemos convênio).

**Lead:** Certo, entendi.

[Neste ponto, o requisito “consulta explicada com valor e condições” está atendido: formato, bioimpedância, retorno, **R$ 700** e particular.]

---

## 4. Transição para agendamento – checar disponibilidade simples

**Alice (Qualificação):** Sabendo como funciona a consulta e o valor, faz sentido pra você organizar essa primeira consulta agora?  
**Lead:** Faz sim, quero marcar pra começar logo.  
**Alice:** Ótimo, então podemos seguir para o agendamento. Pra encaixar melhor na sua rotina, você costuma ter mais facilidade de horário **de manhã** ou **à tarde** durante a semana?

**Lead:** À tarde é melhor pra mim, principalmente de terça ou quinta.

[Aqui o lead:
- confirma que **quer marcar agora**;  
- informa uma **disponibilidade básica** (tarde, terça/quinta).  
Todos os requisitos estruturais para **Aguardando agendamento** ficam satisfeitos.]

---

## 5. Momento em que o Orquestrador pode enviar para **Aguardando agendamento**

Depois da última resposta do lead (“À tarde é melhor pra mim, principalmente de terça ou quinta.”), o contexto é:

1. **Nome real:** Carla já está registrada como nome do lead.  
2. **Lead qualificado:** objetivo e momento foram entendidos; ele expressou urgência (“quero começar logo”).  
3. **Consulta explicada com valor:** R$ 700, bioimpedância, retorno, atendimento particular.  
4. **Disponibilidade básica:** prefere **tarde**, principalmente **terça ou quinta**.  
5. **Prontidão clara:** “Faz sim, quero marcar pra começar logo.”

Com isso, o Orquestrador pode montar algo como:

```json
{
  "next_agent": "Aguardando agendamento",
  "rationale": "Lead já está qualificado, recebeu explicação da consulta com valor, informou disponibilidade (tarde, terça/quinta) e expressou claramente que quer marcar agora.",
  "updates": []
}
```

O workflow `IGOR_02.2_AGENDAMENTO` então:

- muda o pipeline/status do lead para a fila de atendimento humano,  
- envia a mensagem de handoff (por exemplo:  
  “Perfeito. Vou te encaminhar agora pra equipe que combina direitinho o melhor horário com você aqui pelo WhatsApp.”),  
- e o fluxo de IA se desliga para esse lead.

---

## Resumo dos pontos obrigatórios no exemplo

- **Nome real:** capturado no Acolhimento (“Carla”).  
- **Qualificação:** objetivo, contexto e urgência (“emagrecimento”, “10kg”, “quero começar logo”).  
- **Explicação da consulta:** formato, bioimpedância, retorno, valor **R$ 700**, atendimento particular.  
- **Disponibilidade básica:** tarde, terça/quinta.  
- **Prontidão clara:** lead diz que **quer marcar agora** depois de entender valor e condições.

Só depois de tudo isso é que o Orquestrador deve rotacionar para **Aguardando agendamento**.

