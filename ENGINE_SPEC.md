# 🧠 NetDictator Engine Specification

This document details the internal logic and ML architecture of the **NetDictator Dynamic Inference Engine**.

## 🛡️ The 4-Layer Security Pipeline
NetDictator processes every data request through four specialized layers before delivery:

### Layer 1: NLP Sensitivity Analysis
- **Dynamic Scorer**: Goes beyond keywords. It uses a hybrid model of **Shannon Entropy** and **Semantic Context**.
- **Entropy Detection**: Identifies "Random Strings" (Like AWS Keys or Passwords) by calculating character distribution randomness.
- **Pattern Clustering**: Redacts PII (Emails, Names, SSNs, Phones) using an aggressive Multi-Regex engine optimized for tabular data.
- **Score (0-60)**: 0 (Normal) to 60 (Crucial/Secret).

### Layer 2: IP Network Verifier
- **VPC Boundary Awareness**: Detects if the requester is coming from an **Internal VPC IP** (Trust) or an **External Internet IP** (Untrusted).
- **Score (0-40)**: 0 (Internal) to 30+ (Hostile/External).

### Layer 3: Risk Decision Matrix (Contextual Overrides)
Risk isn't just about the file; it's about the **Context**.
- **The Sovereignty Matrix**:
  - **Internal Admin** = LOW Risk (Full Trust)
  - **Internal Guest** = MEDIUM Risk (Controlled Access)
  - **External Admin** = MEDIUM Risk (Secure Transit required)
  - **External Guest** = HIGH Risk (Extreme Protection)

### Layer 4: Adaptive Protection Engine
Based on the Risk Band, the engine applies surgical transformations:
- **NONE**: Zero latency, raw file access for internal authorities.
- **MASKING**: Redacts PII (e.g., `M**** K****`) while keeping secondary data visible.
- **TOKENIZATION**: Replaces values with cryptographic tokens (`TKN-XXXX`) for external transit.
- **HYBRID ENCRYPTION**: Uses **AES-256-CBC** for content and wraps the key with **RSA-2048-OAEP**.

## 🧬 ML Model: Dynamic Semantic Inference
Traditional models fail when you change a variable name (e.g., `password -> p_word`). Our engine uses **Statistical Logic**:
1. **Mathematical Entropy**: "If it looks like a random key, it IS a secret."
2. **Contextual Proximity**: "If this high-entropy string is near the word 'token', it’s a HIGH risk."
3. **Zero-Shot Fallback**: Prepared for Scale with `distilbert-base-uncased-mnli` integration for category-agnostic classification.

---
*NetDictator — Dictating the future of Secure Access.*
