# Lab 01 — Client-Side Memory Manipulation

🇺🇸 English | [🇧🇷 Português](./README.pt-BR.md)

## So... I broke my own game

The idea behind this lab was pretty simple: I wanted to find out how easy it would be to manipulate an important value in my own Unity game without touching the source code. For this experiment, the target was the player's Gold.

We started with:

```text
Gold: 100
XP: 0
```

Two enemies later:

```text
Gold: 150
XP: 40
```

And after a few minutes messing around with memory:

```text
Gold: 999
XP: 40
```

So yeah. The integer holding my Gold did not survive the experiment.

> Everything documented here was tested exclusively against `GameSec.exe`, an intentionally vulnerable game I developed myself to study Game Security.

---

## The Problem

In the first prototype, Gold was stored like this:

```csharp
public int gold = 100;
```

Yep. That's it.

The game completely trusted this value in client memory, so the question became:

> if the player controls the machine, what exactly stops them from controlling that `100` too?

Spoiler: in this version, absolutely nothing.

---

# Part 1 — Cheat Engine

Before getting *too* carried away and developing my own tool, I first wanted to prove that the vulnerability actually existed.

So I started with Cheat Engine.

With:

```text
Gold: 100
```

I performed a scan for:

```text
Exact Value
4 Bytes
100
```

Naturally, I got a bunch of results because, unfortunately, my computer has no idea that **this specific 100 is my hard-earned money**.

I killed an enemy:

```text
100 → 125
```

and performed a `Next Scan`.

The list got significantly smaller.

Then I changed one of the remaining candidates:

```text
125 → 999
```

Went back to the game and...

```text
Gold: 999
```

It worked.

First conclusion of the lab:

> trusting an integer stored entirely on the client might not be the greatest idea ever conceived.

---

# Part 2 — "Okay, but can I do this without Cheat Engine?"

This is where the lab got a lot more fun.

After validating the vulnerability with an existing tool, I decided to reproduce the process myself in Python.

And so this was born:

```text
Tools/
└── MemoryScanner/
    └── scanner.py
```

My scanner implements three commands:

```text
first
next
write
```

The workflow looked like this:

```text
Gold = 100
   ↓
python scanner.py first 100
   ↓
many candidates

kill enemy

Gold = 125
   ↓
python scanner.py next 125
   ↓
fewer candidates

kill another enemy

Gold = 150
   ↓
python scanner.py next 150
   ↓
1 candidate

python scanner.py write 999
   ↓

Gold = 999
```

And at that point, I officially no longer needed Cheat Engine to reproduce the attack.

---

## What is the scanner actually doing?

No magic, I promise.

It:

- finds the `GameSec.exe` process;
- retrieves its PID;
- opens the process;
- walks through readable memory regions;
- searches for 32-bit integers;
- stores candidate addresses;
- filters those addresses as the value changes;
- writes a new value once only one candidate remains.

Basically, I started this lab thinking:

> "I want to hack my little game."

and somehow ended up implementing process memory reading and writing on Windows.

That escalated kinda quickly, huh?

---

# Result

After defeating two enemies, the legitimate game state was:

```text
Gold: 150
XP: 40
```

After manipulating memory:

```text
Gold: 999
XP: 40
```

| State | Gold | XP |
| --- | ---: | ---: |
| Initial | 100 | 0 |
| Enemy #1 | 125 | 20 |
| Enemy #2 | 150 | 40 |
| After manipulation | **999** | 40 |

The fact that XP remained at `40` is also useful evidence: I didn't obtain the extra Gold through the game's normal reward flow.

I basically went straight to memory and said:

> "You're 999 now."

---

## Proof of Concept



---

# Root Cause

The problem isn't simply that `gold` is an `int`.

The actual problem is **trusting the client**.

The client:

```text
stores the Gold
      +
decides what the Gold is
      +
uses that Gold as truth
```

If the user controls the client, they also have the ability to interfere with that state.

That was probably the biggest takeaway from this first lab:

> making a value harder to modify is not the same thing as making that value trustworthy.

---

# Impact

In this offline prototype?

Nothing particularly dramatic. At worst, I become absurdly rich in my own game.

But the same principle applied to larger systems could affect:

- currency;
- XP;
- health;
- ammunition;
- inventory;
- progression;
- scores;
- shared economies.

The issue becomes especially relevant when a server accepts values provided by the client as truth.

And yes, this has already become an idea for another lab!!!!!

---

# Logs

The scanner also saves session logs.

Example:

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

Because I'm on team **organized evidence**.

---

# What's Next?

Now comes the fun part:

**trying to protect the Gold.**

But I don't want to simply hide the value somewhere and declare victory.

The next stage will be:

```text
implement protection
        ↓
try to break the protection
        ↓
discover that it probably wasn't that great
        ↓
improve it
        ↓
break it again
```

The goal of this project isn't to create an "unhackable" system.

It's to understand **why vulnerabilities exist, how they are exploited, and which defenses actually change the trust model**.

---

## Disclaimer

This project exists exclusively for Game Security study and research.

Every experiment was performed against software I developed myself specifically to be tested and broken.

No cubes were permanently harmed during testing. (Maybe.)