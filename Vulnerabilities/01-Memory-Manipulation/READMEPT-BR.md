# Lab 01 — Manipulação de Memória no Cliente

[🇺🇸 English](./README.md) | 🇧🇷 Português

## Visão Geral

Este laboratório demonstra como estados sensíveis de um jogo, quando armazenados inteiramente na memória do cliente, podem ser identificados e modificados durante a execução.

O alvo utilizado é o **GameSec**, um jogo Unity deliberadamente vulnerável desenvolvido como parte deste repositório para o estudo de conceitos de segurança em jogos dentro de um ambiente controlado.

O experimento foi realizado em duas etapas:

1. **Validação manual utilizando Cheat Engine**
2. **Reprodução programática utilizando um memory scanner próprio desenvolvido em Python**

A primeira etapa teve como objetivo identificar e validar a vulnerabilidade. Após compreender seu funcionamento, uma ferramenta própria foi desenvolvida para reproduzir a mesma manipulação de memória sem depender do Cheat Engine.

> **Escopo:** Todos os testes documentados neste laboratório foram realizados exclusivamente contra o `GameSec.exe`, uma aplicação intencionalmente vulnerável desenvolvida especificamente para este projeto.

---

## Vulnerabilidade

A quantidade de Gold do jogador é armazenada como um inteiro simples na memória do cliente:

```csharp
public int gold = 100;
```

O jogo utiliza esse valor presente no cliente como fonte autoritativa para determinar a quantidade atual de Gold do jogador.

Como consequência, um processo com permissão para acessar a memória do jogo pode modificar esse valor sem utilizar as mecânicas previstas pelo sistema.

---

## Comportamento Esperado

O jogador inicia com:

```text
Gold: 100
XP: 0
```

Derrotar um inimigo de maneira legítima concede:

```text
+25 Gold
+20 XP
```

Portanto, após derrotar dois inimigos, o estado esperado é:

```text
Gold: 150
XP: 40
```

---

# Metodologia

## Etapa 1 — Validação Manual com Cheat Engine

O primeiro objetivo foi determinar se o valor de Gold poderia ser identificado e modificado diretamente na memória.

Com o jogador inicialmente possuindo:

```text
Gold: 100
```

o Cheat Engine foi conectado ao processo `GameSec.exe`.

Foi realizada uma busca do tipo **Exact Value** utilizando:

```text
Value: 100
Value Type: 4 Bytes
```

A primeira busca retornou múltiplos endereços, pois o inteiro `100` estava presente na memória por diferentes motivos não necessariamente relacionados ao Gold.

### Filtragem dos Candidatos

Um inimigo foi derrotado normalmente:

```text
Gold: 100 → 125
```

Em seguida, foi realizado um `Next Scan` procurando pelo novo valor:

```text
125
```

Apenas os endereços que anteriormente continham `100` e passaram a conter `125` permaneceram como candidatos.

Isso reduziu significativamente a quantidade de possíveis endereços.

### Modificação Manual da Memória

Um dos candidatos restantes foi adicionado à lista de endereços do Cheat Engine e alterado manualmente:

```text
125 → 999
```

O jogo imediatamente passou a apresentar:

```text
Gold: 999
```

Isso confirmou que a moeda do jogador poderia ser manipulada diretamente na memória do processo.

A vulnerabilidade foi, portanto, **validada manualmente**.

---

## Etapa 2 — Reprodução Programática

Após validar a vulnerabilidade com o Cheat Engine, o próximo objetivo foi reproduzir a mesma técnica sem depender de um editor de memória existente.

Para isso, foi desenvolvido um memory scanner próprio em Python utilizando APIs de processos e memória do Windows.

A ferramenta implementa três operações principais:

```text
first <valor>
next <valor>
write <valor>
```

---

### First Scan

O jogo foi reiniciado com:

```text
Gold: 100
```

O scanner foi executado:

```bash
python scanner.py first 100
```

A ferramenta:

1. localiza o processo `GameSec.exe`;
2. identifica seu PID;
3. abre o processo;
4. enumera suas regiões legíveis de memória;
5. procura pela representação do inteiro de 32 bits `100`;
6. armazena os endereços correspondentes como candidatos.

A primeira varredura retorna múltiplos candidatos porque o scanner não sabe o significado daquele valor.

Ele sabe apenas que determinada posição da memória contém o inteiro procurado.

---

### Next Scan

Um inimigo foi derrotado normalmente:

```text
Gold: 100 → 125
```

Os candidatos anteriores foram então filtrados:

```bash
python scanner.py next 125
```

Em vez de percorrer toda a memória novamente, a ferramenta verifica somente os endereços identificados anteriormente.

Qualquer endereço que não contenha `125` é descartado.

Um segundo inimigo foi derrotado:

```text
Gold: 125 → 150
```

e uma nova filtragem foi realizada:

```bash
python scanner.py next 150
```

Durante o experimento documentado, esse processo reduziu os resultados até restar:

```text
Candidates remaining: 1
```

O endereço de memória associado ao Gold havia sido isolado com sucesso.

---

### Memory Write

Com apenas um candidato restante, o scanner recebeu a instrução de escrever um novo valor:

```bash
python scanner.py write 999
```

A ferramenta leu o valor existente, realizou a escrita na memória e verificou o resultado.

O jogo imediatamente passou a apresentar:

```text
Gold: 999
XP: 40
```

A vulnerabilidade originalmente identificada através do Cheat Engine havia, portanto, sido **reproduzida com sucesso através de uma ferramenta própria**.

---

# Resultado

A vulnerabilidade foi explorada com sucesso através de **duas abordagens**:

| Método | Resultado |
|---|---|
| Cheat Engine | Sucesso |
| Memory Scanner próprio em Python | Sucesso |

O estado legítimo após derrotar dois inimigos era:

```text
Gold: 150
XP: 40
```

Após a manipulação da memória:

```text
Gold: 999
XP: 40
```

| Estado | Gold | XP |
|---|---:|---:|
| Inicial | 100 | 0 |
| Após Inimigo #1 | 125 | 20 |
| Após Inimigo #2 | 150 | 40 |
| Após manipulação da memória | **999** | 40 |

O XP permanecer em `40` fornece evidência adicional de que o Gold adicional não foi obtido através do fluxo normal de recompensa dos inimigos.

---

## Prova de Conceito

![Manipulação de memória realizada com sucesso](./screenshots/gold-999.png)

---

# Fluxo Técnico

```text
                GameSec.exe
                    │
                    │
              Gold = 100
                    │
                    ▼
          ┌─────────────────┐
          │   First Scan    │
          │    int32 100    │
          └────────┬────────┘
                   │
           vários candidatos
                   │
                   ▼
            Inimigo derrotado
              Gold = 125
                   │
                   ▼
          ┌─────────────────┐
          │    Next Scan    │
          │    int32 125    │
          └────────┬────────┘
                   │
           menos candidatos
                   │
                   ▼
            Inimigo derrotado
              Gold = 150
                   │
                   ▼
          ┌─────────────────┐
          │    Next Scan    │
          │    int32 150    │
          └────────┬────────┘
                   │
                   ▼
            resta 1 candidato
                   │
                   ▼
          ┌─────────────────┐
          │  Memory Write   │
          │    150 → 999    │
          └────────┬────────┘
                   │
                   ▼
               GameSec.exe

               Gold = 999
                 XP = 40
```

---

# Causa Raiz

A vulnerabilidade existe porque um valor relevante para a lógica do jogo é:

- armazenado diretamente na memória do cliente;
- representado através de um tipo primitivo previsível;
- modificável durante a execução;
- considerado pelo jogo como estado autoritativo.

Em outras palavras, o cliente controla tanto o armazenamento quanto a interpretação do valor utilizado como moeda.

O experimento demonstra um princípio importante de segurança em jogos:

> **Um cliente sob controle do jogador não deve ser considerado uma autoridade confiável para estados sensíveis do jogo.**

---

# Memory Scanner Próprio

A segunda etapa da prova de conceito utiliza uma ferramenta própria desenvolvida em Python especificamente para este laboratório.

```text
Tools/
└── MemoryScanner/
    ├── scanner.py
    └── logs/
```

O scanner demonstra conceitos como:

- descoberta de processos no Windows;
- identificação do PID;
- obtenção de handles de processos;
- enumeração de regiões de memória virtual;
- leitura da memória de outro processo;
- busca por inteiros de 32 bits;
- filtragem iterativa de endereços candidatos;
- escrita controlada na memória do processo;
- geração de logs das sessões de teste.

A implementação foi intencionalmente limitada ao processo:

```text
GameSec.exe
```

mantendo a ferramenta dentro do escopo controlado deste laboratório.

---

# Fluxo do Scanner

O scanner reproduz o fluxo básico de busca em memória realizado inicialmente de forma manual:

```text
Valor conhecido
      │
      ▼
First Scan
      │
      ▼
Endereços candidatos
      │
      ▼
Mudança legítima de estado
      │
      ▼
Next Scan
      │
      ▼
Filtragem de candidatos
      │
      ▼
Identificação do endereço
      │
      ▼
Memory Write
```

A diferença importante é que o segundo experimento implementa esse comportamento programaticamente, em vez de delegá-lo ao Cheat Engine.

---

# Evidências

O scanner gera logs de sessão contendo o fluxo do experimento.

Exemplo:

```text
[FIRST SCAN]
Target value: 100
Candidates found: ...

[NEXT SCAN]
Target value: 125
Candidates remaining: ...

[NEXT SCAN]
Target value: 150
Candidates remaining: 1

[MEMORY WRITE]
Old value: 150
New value: 999
Result: SUCCESS
Confirmed value: 999
```

Evidências selecionadas de execuções bem-sucedidas são armazenadas em:

```text
evidence/
```

Arquivos utilizados apenas durante a execução, como listas de candidatos e metadados da sessão ativa, não são destinados ao versionamento.

---

# Impacto

Fraquezas semelhantes podem permitir a modificação de valores controlados pelo cliente, como:

- moedas;
- vida;
- munição;
- experiência;
- quantidade de itens;
- atributos de personagens;
- valores relacionados à progressão.

O impacto real de segurança depende diretamente da arquitetura do jogo.

Em um jogo exclusivamente single-player e offline, modificar a memória local pode representar pouco ou nenhum impacto significativo de segurança.

Por outro lado, em jogos multiplayer, economias compartilhadas, progressão competitiva ou sistemas nos quais o servidor confia em valores fornecidos pelo cliente, as consequências podem ser consideravelmente mais graves.

---

# Mitigação

**Status: Ainda não implementada**

A próxima etapa deste laboratório investigará possíveis formas de mitigação e, principalmente, as limitações de cada abordagem.

Os próximos experimentos incluem:

- verificações de integridade no cliente;
- ofuscação de valores;
- detecção de adulterações;
- arquitetura com estado autoritativo;
- tentativas de contornar as proteções implementadas.

O objetivo não é simplesmente tornar o valor mais difícil de encontrar.

O experimento pretende explorar a diferença entre:

```text
Ofuscação
    ≠
Confiança
```

Tornar um valor presente no cliente mais difícil de modificar não transforma o cliente em uma fonte autoritativa confiável.

---

# Aprendizados

O experimento demonstrou todo o processo desde a descoberta da vulnerabilidade até sua reprodução independente.

```text
Ferramenta existente
        │
        ▼
Observar comportamento
        │
        ▼
Validar vulnerabilidade
        │
        ▼
Compreender a técnica
        │
        ▼
Implementar ferramenta própria
        │
        ▼
Reproduzir o ataque
```

O Cheat Engine foi útil para compreender manualmente como o valor se comportava na memória.

O desenvolvimento do scanner próprio exigiu então reproduzir programaticamente os conceitos envolvidos, incluindo enumeração da memória, leitura de memória de processos, filtragem de candidatos e escrita em memória.

Mais importante, o experimento demonstra que esconder um valor atrás das mecânicas normais do jogo não o protege quando o estado autoritativo permanece sob controle do cliente.

---

# Aviso

Este projeto foi desenvolvido exclusivamente para fins educacionais e pesquisa em segurança de jogos.

Todos os experimentos documentados neste repositório foram realizados contra software desenvolvido intencionalmente e controlado para este laboratório.