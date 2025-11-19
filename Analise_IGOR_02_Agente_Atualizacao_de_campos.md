# Análise crítica – IGOR_02_Agente_Atualização de campos

Este documento aprofunda a análise do workflow `IGOR_02_Agente_Atualização de campos` e como ele se encaixa (ou não) na lógica global definida para o projeto IGOR.

---

## 1. Função do workflow na arquitetura

### 1.1 Papel declarado

O workflow `IGOR_02_Agente_Atualização de campos` é acionado pelo Orquestrador quando este decide:

```json
{
  "next_agent": "Atualização de campos",
  "updates": [
    { "field": "<nome_do_campo_logico>", "value": "<valor_extraido>", "tool": "<tool_associada?>" }
  ]
}
```

O objetivo é **propagar informações extraídas da conversa** (nome, cidade, objetivo, disponibilidade, etc.) para campos do Kommo, sem solicitar nada ao usuário.

Na lógica global, esse agente é:

- **técnico** (não fala com o paciente),
- responsável por **escrever no CRM** a partir de `updates`,
- e deve operar com **máxima segurança**, pois um erro aqui polui o histórico e quebra o funil.

### 1.2 Fluxo técnico interno

Resumo do que o workflow faz hoje:

1. `When Executed by Another Workflow` recebe o objeto com `updates` + contexto (link, lead_id, authorization, etc.).
2. `Split Out` abre o array `updates` em itens individuais.
3. `Loop Over Items` itera por cada `{field, value}`.
4. `If` verifica se `field` é `"nome"` ou `"cidade"` (case-insensitive).
   - Se for **nome**:
     - `Atualiza nome` faz um PATCH no Kommo:
       - URL: `/api/v4/leads/{lead_id}`
       - corpo: `{"name": value}`  
     - Depois retorna ao `Loop Over Items`.
   - Se for **cidade**:
     - `Atualiza cidade` faz um PATCH atualizando um `custom_fields_values` fixo (field_id da cidade).
     - Depois retorna ao `Loop Over Items`.
5. Para qualquer outro `field`:
   - o item vai para `AI Agent`, que recebe:
     - o JSON do item (`field`, `value`…),
     - um `systemMessage` técnico (agente de atualização de campos Kommo),
     - acesso ao Vector Store PGVector com metadados dos campos,
     - acesso à ferramenta `kommo_update_field` (HTTP tool) para atualizar campos personalizados via `field_id`.
6. O `AI Agent`:
   - usa o Vector Store para descobrir qual campo técnico corresponde a `field`,
   - normaliza `value`,
   - decide se chama ou não `kommo_update_field`.
7. Quando todos os updates são processados:
   - `Edit Fields1` define `output = "Campos atualizados"`,
   - `Return` devolve esse output ao Orquestrador.

Na volta, o Orquestrador pode buscar `lead_info` atualizado e usá-lo como base de decisão.

---

## 2. Coerência com a lógica geral do projeto

### 2.1 Onde ele se encaixa bem

Alguns pontos estão **alinhados** com a filosofia do fluxo:

- O agente não conversa com o paciente; atua apenas internamente, como esperado.
- Há uma separação entre:
  - **campos simples** (nome, cidade) com updates diretos,
  - e **campos complexos** (objetivo, disponibilidade, etc.) tratados via Vector Store + `kommo_update_field`.
- O `systemMessage` técnico do `AI Agent` (no node LangChain) já orienta a:
  - **não inventar field_id**,
  - normalizar `value` conforme o tipo (select, booleano, data, etc.),
  - não atualizar em caso de ambiguidade,
  - e priorizar segurança sobre “preencher a qualquer custo”.

Isso está alinhado com o princípio global de:

> “É melhor **não atualizar** do que gravar um dado errado no CRM.”

### 2.2 Pontos de desconexão / risco atual

Mesmo com essa base boa, há alguns pontos que podem gerar desconexão com a lógica que você desenhou para o fluxo inteiro:

1. **Atualização direta de `nome` e `cidade` sem o mesmo nível de rigor**  
   - Para `nome` e `cidade`, o workflow faz PATCH diretamente, sem passar pelo agente técnico.  
   - Isso é útil por ser simples, mas:
     - assume que qualquer `field: "nome"`/`"cidade"` vindo do Orquestrador é sempre confiável,  
     - e ignora as mesmas salvaguardas de ambiguidade que você exige em `prompt_atualizacao` (Regra 1 no Orquestrador).
   - Se o Orquestrador, por algum bug ou ajuste futuro de prompt, interpretar equivocadamente um trecho como “nome” ou “cidade”, esse workflow **não tem freio** para impedir a escrita.

2. **Dependência forte de `prompt_atualizacao` para segurança upstream**  
   - A lógica de “só gerar `updates` quando a mensagem for resposta direta à pergunta anterior” está toda no Orquestrador (via `prompt_atualizacao`).
   - Se `prompt_atualizacao` ficar mais permissivo ou for alterado sem cuidado, o agente de atualização recebe `updates` mais “soltos”.  
   - No caso dos campos genéricos, o `AI Agent` ainda tem salvaguardas internas; mas nos campos diretos (nome/cidade), a atualização é automática.

3. **Ausência de logging estruturado sobre o que foi atualizado**  
   - Hoje o workflow retorna apenas `"Campos atualizados"`.
   - Não há um log estruturado fácil de ler (pelo menos no workflow) com:
     - qual `field` foi atualizado,
     - qual era o `value`,
     - qual `field_id` foi usado,
     - e se a ação veio de um PATCH direto ou da tool `kommo_update_field`.
   - Isso dificulta auditoria posterior quando há uma suspeita de update errado.

4. **Falta de alinhamento explícito com o “estado do funil”**  
   - O agente opera puramente em cima de `updates`.  
   - Não verifica, por exemplo:
     - se o lead ainda está em atendimento IA,
     - se o campo é coerente com o estágio (por exemplo, disponibilidade sendo atualizada quando o lead ainda está “só pesquisando”).
   - Em teoria o Orquestrador já cuida disso, mas o agente de atualização não tem nenhuma consciência de estágio para fazer checks adicionais.

---

## 3. O que endurecer e como

Com base no que você considera “lógica correta”, estes são os pontos que eu endureceria no `IGOR_02_Agente_Atualização de campos`:

### 3.1 Blindar os campos nome e cidade

Hoje:

- `If` → `"nome"` / `"cidade"` → PATCH direto.

Sugestão:

1. **Adicionar validações simples antes de atualizar:**
   - Para `nome`:
     - rejeitar valores muito curtos (`< 2 caracteres`),
     - rejeitar valores só com números ou símbolos,
     - rejeitar textos genéricos (“novo contato”, “teste”, “lead”, etc.).
   - Para `cidade`:
     - rejeitar valores vazios,
     - rejeitar strings com muitos dígitos (que pareçam CEP ou telefone),
     - opcionalmente: validar se tem pelo menos uma letra.

2. **Opcionalmente, passar também por um “mini agente técnico” ou heurística interna:**
   - Ex.: um pequeno bloco de código (node `Code`) que checa se o `value` parece um nome próprio ou uma cidade antes de fazer o PATCH.

3. **Se falhar nos checks:**
   - não atualizar,
   - talvez marcar esse update como “ignorado” em um log (ver seção 3.3).

### 3.2 Tornar o agente mais consciente de estágio (quando fizer sentido)

Sem sobrecarregar o workflow, há alguns checks simples que poderiam ser feitos:

- Receber de `lead_info` um campo mínimo de estágio (por exemplo, `lead_info.estado_funil` ou `lead_info.status_id` já decodificado).
- Adicionar, no prompt do `AI Agent`, algo do tipo:
  - “Antes de atualizar campos que indicam disponibilidade ou decisão (ex.: `Disponibilidade`, `Estado de decisão`), considere se o estágio do lead (`estado_funil`/`status`) combina com esse tipo de update. Se houver incoerência, prefira não atualizar.”

Isso evita, por exemplo, gravar “Disponibilidade” como se já estivesse decidida em fases muito iniciais.

### 3.3 Melhorar logging e visibilidade

Adicionar um node `Code` ou `Set` para gerar um resumo estruturado de cada update realizado, por exemplo:

```json
{
  "field_logico": "objetivo_principal",
  "field_id": 123456,
  "valor_aplicado": "Emagrecimento",
  "origem": "kommo_update_field",
  "status": "atualizado"
}
```

e outro para updates ignorados:

```json
{
  "field_logico": "cidade",
  "valor_recebido": "123",
  "origem": "nome/cidade direto",
  "status": "ignorado_por_regra"
}
```

Isso pode ser:

- escrito em uma tabela de log (Postgres),
- ou mesmo enviado para um canal de debug (no mínimo, retornar ao Orquestrador para ser armazenado).

### 3.4 Alinhar a documentação com o workflow

O documento `Logica_do_Roteamento_IGOR.md` já foi atualizado para refletir:

- o fato de que **nome/cidade** são atualizados por caminho direto,
- e que demais campos usam o agente técnico + Vector Store.

Sempre que endurecer as regras (por exemplo, colocando validações extras para nome/cidade), é importante atualizar esse documento para continuar sendo a **fonte da verdade**.

---

## 4. Conclusões

- O `IGOR_02_Agente_Atualização de campos` está, na essência, **bem integrado** ao fluxo:
  - é chamado em momentos específicos (decididos pelo Orquestrador),
  - opera como agente técnico,
  - e usa Vector Store + tool de HTTP para atualizar campos personalizados de forma relativamente segura.
- Os principais riscos atuais estão em:
  - **atualizações diretas de `nome` e `cidade`**, que não passam pelos mesmos filtros de ambiguidade dos outros campos,
  - **falta de logging detalhado**, que dificulta rastrear updates errados,
  - e **dependência total de upstream** (Orquestrador + prompt_atualizacao) para garantir que os `updates` sejam sempre confiáveis.

Endurecendo as regras para os campos diretos (nome/cidade), adicionando um pouco mais de consciência de estágio e melhorando logging, esse workflow fica alinhado com a filosofia que você vem aplicando em todo o projeto:  

> “Andar rápido quando faz sentido, mas **nunca** à custa de incoerência ou dados errados no CRM.”

