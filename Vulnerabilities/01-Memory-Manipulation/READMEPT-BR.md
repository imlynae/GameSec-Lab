# Lab 01 — Client-Side Memory Manipulation

🇺🇸 English | [🇧🇷 Português](./README.pt-BR.md)

## So... I broke my own game

A ideia desse laboratório era simples: eu queria descobrir o quão fácil seria manipular um valor importante do meu próprio jogo Unity sem tocar no código-fonte, e nessa experiência, alvo foi o Gold do jogador.

Começamos com:

```text
Gold: 100
XP: 0
```

Dois inimigos depois:

```text
Gold: 150
XP: 40
```

E alguns minutos brincando com memória depois:

```text
Gold: 999
XP: 40
```

Ou seja: O int estipulado para o gold foi quebrado.

> Tudo aqui foi testado exclusivamente no `GameSec.exe`, um jogo propositalmente vulnerável que eu mesma desenvolvi para estudar Game Security.

---

## O problema

No primeiro protótipo, o Gold era armazenado assim:

```csharp
public int gold = 100;
```

Sim. Só.

O jogo confiava completamente nesse valor dentro da memória do cliente, então a pergunta virou:

> se o jogador controla a máquina, o que impede ele de controlar esse `100` também?

Spoiler: nessa versão, absolutamente nada.

---

# Parte 1 — Cheat Engine

Antes de inventar (tanta) moda e desenvolver minha própria ferramenta, eu queria primeiro provar que a vulnerabilidade realmente existia.

Então comecei pelo Cheat Engine.

Com:

```text
Gold: 100
```

fiz um scan por:

```text
Exact Value
4 Bytes
100
```

Naturalmente, apareceram vários resultados porque, infelizmente, meu computador não sabe que **aquele 100 específico é meu dinheirinho suado**.

Matei um inimigo:

```text
100 → 125
```

e fiz um `Next Scan`.

A lista caiu bastante.

Depois alterei um dos candidatos:

```text
125 → 999
```

Voltei para o jogo e...

```text
Gold: 999
```

Funcionou.

Primeira conclusão do laboratório:

> confiar em um inteiro armazenado no cliente talvez não seja exatamente uma boa ideia.

---

# Parte 2 — "Tá, mas eu consigo fazer isso sem Cheat Engine?"

Essa foi a parte que deixou o laboratório bem mais divertido.

Depois de validar o problema com uma ferramenta pronta, decidi reproduzir o processo em Python.

Nasceu então:

```text
Tools/
└── MemoryScanner/
    └── scanner.py
```

Meu scanner implementa três comandos:

```text
first
next
write
```

O fluxo ficou assim:

```text
Gold = 100
   ↓
python scanner.py first 100
   ↓
vários candidatos

mata inimigo

Gold = 125
   ↓
python scanner.py next 125
   ↓
menos candidatos

mata outro inimigo

Gold = 150
   ↓
python scanner.py next 150
   ↓
1 candidato

python scanner.py write 999
   ↓

Gold = 999
```

E aí eu oficialmente parei de depender do Cheat Engine para reproduzir o ataque.

---

## O que o scanner faz por baixo dos panos

Sem magia, prometo.

Ele:

- encontra o processo `GameSec.exe`;
- pega o PID;
- abre o processo;
- percorre regiões de memória legíveis;
- procura inteiros de 32 bits;
- salva os endereços candidatos;
- filtra esses endereços conforme o valor muda;
- escreve um novo valor quando sobra um único candidato.

Basicamente, eu comecei esse laboratório pensando:

> "quero hackear meu joguinho"

e terminei implementando leitura e escrita de memória de processos no Windows.

Escalou meio rápido, né?

---

# Resultado

Depois de dois inimigos, o estado legítimo era:

```text
Gold: 150
XP: 40
```

Após a manipulação:

```text
Gold: 999
XP: 40
```

| Estado | Gold | XP |
|---|---:|---:|
| Inicial | 100 | 0 |
| Inimigo #1 | 125 | 20 |
| Inimigo #2 | 150 | 40 |
| Após manipulação | **999** | 40 |

O XP continuar em `40` é uma evidência útil: eu não ganhei Gold através do fluxo normal de recompensa. Só fui diretamente na memória e falei "agora é 999".

---

## Proof of Concept

![Gold alterado em memória](./screenshots/gold-999.png)

---

# Causa raiz

O problema não é simplesmente o fato de `gold` ser um `int`.

A causa real é **confiança no cliente**.

O cliente:

```text
armazena o Gold
      +
decide qual é o Gold
      +
usa esse Gold como verdade
```

Se o usuário controla o cliente, ele também tem possibilidade de interferir nesse estado.

Essa foi provavelmente a principal conclusão desse primeiro laboratório:

> dificultar a alteração de um valor não é a mesma coisa que tornar esse valor confiável.

---

# Impacto

Nesse protótipo offline?

Nada muito dramático. No máximo eu fico absurdamente rica no meu próprio jogo, mas o mesmo princípio aplicado a sistemas maiores pode afetar:

- moeda;
- XP;
- vida;
- munição;
- inventário;
- progressão;
- pontuações;
- economias compartilhadas.

Em especial, o problema fica muito mais relevante quando um servidor aceita valores enviados pelo cliente como verdade.

E sim, isso já virou ideia para outro lab!!!!!

---

# Logs

O scanner também salva logs das sessões.

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

Porque eu sou do time das provas organizadas.

---

# Próximo passo

Agora vem a parte divertida:

**tentar proteger o Gold.**

Mas não quero simplesmente esconder o valor e declarar vitória.

A próxima etapa será:

```text
implementar proteção
        ↓
tentar quebrar a proteção
        ↓
descobrir que ela provavelmente não era tão boa
        ↓
melhorar
        ↓
quebrar de novo
```

O objetivo desse projeto não é criar um sistema "impossível de hackear".

É entender **por que as vulnerabilidades existem, como são exploradas e quais defesas realmente mudam o modelo de confiança**.

---

## Disclaimer

Este projeto existe exclusivamente para estudo e pesquisa em Game Security.

Todos os experimentos foram realizados contra software que eu mesma desenvolvi especificamente para ser testado e quebrado.

Nenhum cubo foi permanentemente prejudicado durante os testes. (Talvez)