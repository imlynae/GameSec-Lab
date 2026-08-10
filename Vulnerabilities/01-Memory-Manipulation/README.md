# Lab 01 — Client-Side Memory Manipulation

🇺🇸 English | [🇧🇷 Português](./README.pt-BR.md)

## Overview

This lab demonstrates how sensitive game state stored entirely in client memory can be identified and modified at runtime.

The target is **GameSec**, a deliberately vulnerable Unity game developed as part of this repository for studying game security concepts in a controlled environment.

The experiment was performed in two stages:

1. **Manual validation using Cheat Engine**
2. **Programmatic reproduction using a custom Python memory scanner**

The first stage was used to identify and validate the vulnerability. After understanding the behavior, a custom tool was developed to reproduce the same memory manipulation without relying on Cheat Engine.

> **Scope:** All testing documented in this lab was performed exclusively against `GameSec.exe`, an intentionally vulnerable application developed specifically for this project.

---

## Vulnerability

The player's Gold is stored as a plain integer in client memory:

```csharp
public int gold = 100;
```

The game treats this client-side value as the authoritative source for the player's current currency.

As a result, a process with permission to access the game's memory can modify the value without interacting with the intended game mechanics.

---

## Expected Behavior

The player starts with:

```text
Gold: 100
XP: 0
```

Defeating an enemy legitimately rewards:

```text
+25 Gold
+20 XP
```

Therefore, after defeating two enemies, the expected state is:

```text
Gold: 150
XP: 40
```

---

# Methodology

## Stage 1 — Manual Validation with Cheat Engine

The first objective was to determine whether the Gold value could be identified and modified directly in memory.

With the player initially holding:

```text
Gold: 100
```

Cheat Engine was attached to `GameSec.exe`.

An **Exact Value** scan was performed using:

```text
Value: 100
Value Type: 4 Bytes
```

The initial scan returned multiple addresses because the integer `100` existed in memory for several unrelated reasons.

### Filtering Candidates

An enemy was defeated normally:

```text
Gold: 100 → 125
```

A `Next Scan` was then performed for:

```text
125
```

Only addresses that previously contained `100` and now contained `125` remained as candidates.

This significantly reduced the number of possible addresses.

### Manual Memory Modification

A remaining candidate was added to the Cheat Engine address list and manually changed:

```text
125 → 999
```

The game immediately displayed:

```text
Gold: 999
```

This confirmed that the player's currency could be directly manipulated in process memory.

The vulnerability was therefore considered **manually validated**.

---

## Stage 2 — Programmatic Reproduction

After validating the vulnerability with Cheat Engine, the next objective was to reproduce the same technique without relying on an existing memory editor.

A custom memory scanner was developed in Python using Windows process and memory APIs.

The tool implements three primary operations:

```text
first <value>
next <value>
write <value>
```

---

### First Scan

The game was restarted with:

```text
Gold: 100
```

The scanner was executed:

```bash
python scanner.py first 100
```

The tool:

1. locates `GameSec.exe`;
2. obtains its process identifier;
3. opens the process;
4. enumerates readable memory regions;
5. searches for the 32-bit integer representation of `100`;
6. stores matching addresses as candidates.

The initial scan produces multiple candidates because the scanner does not know what a value represents.

It only knows that a particular memory location contains the requested integer.

---

### Next Scan

An enemy was defeated normally:

```text
Gold: 100 → 125
```

The previous candidates were filtered:

```bash
python scanner.py next 125
```

Instead of scanning the entire process again, the tool reads only previously identified addresses.

Any address that does not contain `125` is discarded.

A second enemy was then defeated:

```text
Gold: 125 → 150
```

Another filtering pass was performed:

```bash
python scanner.py next 150
```

During the documented experiment, this reduced the candidate set to:

```text
Candidates remaining: 1
```

The memory location associated with the Gold value had been successfully isolated.

---

### Memory Write

With a single candidate remaining, the scanner was instructed to write a new value:

```bash
python scanner.py write 999
```

The tool read the current value, performed the memory write, and verified the result.

The game immediately displayed:

```text
Gold: 999
XP: 40
```

The vulnerability originally identified through Cheat Engine had therefore been successfully reproduced using a custom-built tool.

---

# Result

The vulnerability was successfully exploited through **two approaches**:

| Method | Result |
|---|---|
| Cheat Engine | Successful |
| Custom Python Memory Scanner | Successful |

The legitimate game state after defeating two enemies was:

```text
Gold: 150
XP: 40
```

After memory manipulation:

```text
Gold: 999
XP: 40
```

| State | Gold | XP |
|---|---:|---:|
| Initial | 100 | 0 |
| After Enemy #1 | 125 | 20 |
| After Enemy #2 | 150 | 40 |
| After memory manipulation | **999** | 40 |

The unchanged XP value provides additional evidence that the additional Gold was not obtained through the normal enemy reward flow.

---

## Proof of Concept

![Successful memory manipulation](./screenshots/gold-999.png)

---

# Technical Flow

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
            many candidates
                   │
                   ▼
             Enemy defeated
              Gold = 125
                   │
                   ▼
          ┌─────────────────┐
          │    Next Scan    │
          │    int32 125    │
          └────────┬────────┘
                   │
             fewer candidates
                   │
                   ▼
             Enemy defeated
              Gold = 150
                   │
                   ▼
          ┌─────────────────┐
          │    Next Scan    │
          │    int32 150    │
          └────────┬────────┘
                   │
                   ▼
           1 candidate remains
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

# Root Cause

The vulnerability exists because a security-sensitive gameplay value is:

- stored directly in client memory;
- represented as a predictable primitive value;
- mutable during runtime;
- trusted by the game as authoritative state.

The client controls both the storage and interpretation of the currency value.

This illustrates an important security principle:

> **A client under the player's control should not be considered a trusted authority for security-sensitive game state.**

---

# Custom Memory Scanner

The second stage of the proof of concept uses a custom Python tool developed specifically for this lab.

```text
Tools/
└── MemoryScanner/
    ├── scanner.py
    └── logs/
```

The scanner demonstrates:

- Windows process discovery;
- PID identification;
- process handle acquisition;
- virtual memory region enumeration;
- process memory reading;
- 32-bit integer scanning;
- iterative candidate filtering;
- process memory writing;
- session logging.

The implementation is intentionally restricted to:

```text
GameSec.exe
```

to maintain the controlled scope of the laboratory.

---

# Scanner Workflow

The scanner reproduces the basic memory-search workflow originally performed manually:

```text
Known Value
    │
    ▼
First Scan
    │
    ▼
Candidate Addresses
    │
    ▼
Legitimate State Change
    │
    ▼
Next Scan
    │
    ▼
Candidate Filtering
    │
    ▼
Address Identification
    │
    ▼
Memory Write
```

The important distinction is that the second experiment implements this behavior programmatically instead of delegating it to Cheat Engine.

---

# Evidence

The scanner generates session logs containing the experiment flow.

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

Selected evidence from successful experiments is stored under:

```text
evidence/
```

Runtime files such as candidate lists and active session metadata are not intended to be committed.

---

# Impact

Similar weaknesses may allow client-controlled modification of values such as:

- currency;
- health;
- ammunition;
- experience;
- inventory quantities;
- character attributes;
- progression values.

The actual security impact depends heavily on game architecture.

For a purely offline single-player game, modifying local memory may have little meaningful security impact.

For multiplayer games, shared economies, competitive progression, or systems where a server trusts values supplied by the client, the consequences may be significantly more serious.

---

# Mitigation

**Status: Not yet implemented**

The next stage of this laboratory will investigate potential mitigations and their limitations.

Planned experiments include:

- client-side integrity checks;
- value obfuscation;
- tamper detection;
- authoritative state design;
- attempts to bypass implemented protections.

The objective is not merely to make the value more difficult to locate.

Instead, the experiment will explore the distinction between:

```text
Obfuscation
     ≠
Trust
```

Making a client-side value harder to modify does not make the client authoritative.

---

# Lessons Learned

The experiment demonstrated the complete progression from vulnerability discovery to independent reproduction.

```text
Existing Tool
     │
     ▼
Observe Behavior
     │
     ▼
Validate Vulnerability
     │
     ▼
Understand Technique
     │
     ▼
Implement Custom Tool
     │
     ▼
Reproduce Attack
```

Cheat Engine was useful for manually understanding how the value behaved in memory.

Developing the custom scanner then required reproducing the underlying concepts programmatically, including memory enumeration, process memory reading, candidate filtering, and memory writing.

Most importantly, the experiment demonstrates that hiding a gameplay value behind normal game mechanics does not protect it when the authoritative state remains under client control.

---

# Disclaimer

This project was created exclusively for educational and game security research purposes.

All experiments documented in this repository were performed against software intentionally developed and controlled for this laboratory.