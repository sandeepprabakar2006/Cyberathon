# 🧢 NetDictator: Advanced Data Sovereignty Engine

**NetDictator** is a cutting-edge **Adaptive Data Protection Engine (ADPE)** designed for modern VPC architectures. It provides "Digital Sovereignty" by enforcing security policies in real-time, moving beyond passive logging to active enforcement.

## 🚀 Vision
In an era of unprecedented data leaks, NetDictator acts as the **Supreme Authority** for data access. It intercepts every request at the edge, analyzes the content, the user's identity, and their network context to dictate exactly how data should be delivered—whether it's plain, masked, tokenized, or fully encrypted.

## 🧠 Key Innovations
- **Dynamic Inference ML**: Uses Shannon Entropy and Semantic Context to "guess" secrets without relying on fixed keyword lists.
- **Context-Aware Security**: A unique 4-layer pipeline that calculates risk based on **Content + Identity + Location**.
- **Sovereignty Matrix**: Automatically adjusts protection levels (e.g., granting full access to an Internal Admin while enforcing Tokenization on an External Admin).

## 🛠️ Technology Stack
- **Frontend**: Streamlit (Premium Royal Blue & Sandal Theme)
- **Backend**: FastAPI (High-performance asynchronous API)
- **Security**: AES-256-CBC, RSA-2048-OAEP, SHA-256 Tokenization, Regex-based Masking.
- **ML**: Hybrid approach (Mathematical Entropy + Zero-Shot Transformers).
- **Storage**: Amazon S3 integration.

## 🏃 Quick Start
1. **Clone the Repo**:
   ```bash
   git clone https://github.com/sandeepprabakar2006/Cyberathon.git
   ```
2. **Setup Environment**:
   ```bash
   pip install -r backend/requirements.txt
   cp .env.example .env # Configure your AWS & RSA keys
   ```
3. **Run Backend**:
   ```bash
   uvicorn main:app --port 8000
   ```
4. **Run Frontend**:
   ```bash
   streamlit run app.py
   ```

## 📜 Documentation
For a deep dive into the security logic and the ML model, see [ENGINE_SPEC.md](./ENGINE_SPEC.md).

---
*Developed for Cyberathon 2026 — Protecting Data Sovereignty with AI.*
