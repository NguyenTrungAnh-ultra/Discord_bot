---
name: agent-guidelines
description: Core behavioral and naming rules for the agent. Enforces objective communication and strict technical naming conventions.
---

# Agent Core Guidelines

You must strictly adhere to the following rules at all times when communicating with the user or writing code.

## 1. Objective and Nuanced Communication

- **PROHIBITED:** Never assert the correctness, safety, or performance of a code solution using absolute or extreme terms (e.g., "always optimal", "the only solution", "100% bug-free", "guaranteed to work").
- **REQUIRED:** All technical assertions must be qualified by boundary conditions or assumptions. Use objective, verifiable, and nuanced language (e.g., "Based on current benchmarks...", "Assuming the input data is...", "This approach mitigates risk X, provided that Y").

## 2. Strict Technical Naming Conventions

You must strictly follow technical naming conventions for all file names, function names, and headings. Your naming style must be functional, precise, and literal.

**Guidelines:**

1. Use "Intention-Revealing Names" and "Self-Documenting" logic. The name must answer: Why does it exist? What does it do?
2. Prioritize "Descriptive Naming" over any aesthetic, creative, or flowery language. Do not use fancy synonyms.
3. Apply "Semantic Naming" and "Domain-Driven Naming". Use exact business or technical terms.
4. For functions or action-based files, use the "Verb-Noun" pattern (e.g., `getUserData`, `sendNotification`).
5. Avoid "Noise Words" such as 'Data', 'Info', 'Manager', or 'Processor' unless absolutely necessary. Keep it minimal and clean.
6. Follow the "Principle of Least Astonishment". Names must be predictable and boringly accurate.

- **Bad Examples:** `MagicHelper`, `UserSuperDataProcessor`, `AwesomeDashboardTitle`
- **Good Examples:** `UserAuthentication`, `FetchProductList`, `BillingSummary`
