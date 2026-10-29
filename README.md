# 🧠 Nemotron Reasoning Chat Web App

An interactive, browser-based chat application built with **Streamlit** and **NVIDIA NIM API** (`nvidia/nemotron-3-ultra-550b-a55b`).

## ✨ Features
- 🧠 **Live Thought Process / Reasoning Accordion**: Watch Nemotron's deep reasoning trace stream live inside an expandable status container (`st.status` / `st.expander`), separated from the final output.
- 💬 **Streaming Responses**: Real-time markdown streaming of the final generated response.
- ⚙️ **Configurable Controls in Sidebar**:
  - **API Key**: Enter securely with masking or load via `NVIDIA_API_KEY`.
  - **Thinking Toggle**: Enable or disable internal chain-of-thought generation (`enable_thinking`).
  - **Auto-expand Accordion**: Option to keep reasoning traces open or collapsed.
  - **Hyperparameters**: Sliders for `temperature`, `top_p`, and `max_tokens`.
  - **System Prompt**: Fully customizable persona and instructions.
  - **Clear Chat**: Reset session history with one click.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Set your API Key
Set in your environment:
```bash
set NVIDIA_API_KEY=your_key_here
```
Or simply paste it directly into the web UI sidebar password field.

### 3. Run the App
```bash
streamlit run app.py
```
Or double-click `run.bat` on Windows!
