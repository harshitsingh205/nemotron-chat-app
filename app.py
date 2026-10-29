import os
import time
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI

# --- Page Configuration ---
st.set_page_config(
    page_title="Nemotron Code & Study Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Professional CSS Styles (No Emojis, Clean Typography) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .brand-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }

    .brand-logo {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f8fafc;
        font-weight: 700;
        font-size: 18px;
        letter-spacing: -0.5px;
        border: 1px solid #334155;
    }

    .brand-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }

    .brand-subtitle {
        font-size: 0.85rem;
        color: #64748b;
        margin: 2px 0 0 0;
    }

    .study-badge {
        display: inline-block;
        padding: 2px 8px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-radius: 4px;
        background: #e0e7ff;
        color: #3730a3;
        margin-left: 8px;
    }

    .reasoning-box {
        background-color: #f8fafc;
        border-left: 3px solid #64748b;
        padding: 12px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.86rem;
        color: #334155;
        border-radius: 0 6px 6px 0;
        margin-bottom: 10px;
        line-height: 1.5;
    }

    .timer-card {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }

    .timer-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        text-align: center;
        letter-spacing: 2px;
        margin: 6px 0;
    }

    .timer-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        text-align: center;
        letter-spacing: 0.8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Study Presets for Coding ---
STUDY_PRESETS = {
    "Code Mentor (Socratic)": (
        "You are an expert Computer Science Professor and Code Mentor. "
        "Your goal is to help the student learn deeply. Break concepts into fundamentals, "
        "explain algorithmic complexity (Time and Space Big-O), provide clean annotated code, "
        "and point out common edge cases and best practices."
    ),
    "Bug Hunter & Code Auditor": (
        "You are a Senior Software Verification Engineer. Analyze submitted code meticulously. "
        "Identify logic bugs, off-by-one errors, memory inefficiencies, concurrency issues, "
        "and security flaws. Provide the corrected implementation with clear explanations."
    ),
    "Data Structures & Algorithms": (
        "You are an Algorithms Specialist. For every problem, provide: 1) Intuition and brute-force approach, "
        "2) Optimal solution with detailed walkthrough, 3) Time and Space complexity analysis, "
        "4) Python/C++ implementation with comments on non-trivial lines."
    ),
    "Concise Technical Reference": (
        "You are a concise software documentation specialist. Give brief, precise explanations with minimal prose "
        "and clean, copy-pasteable production-ready code examples."
    ),
}

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "study_notes" not in st.session_state:
    st.session_state.study_notes = ""

if "timer_seconds" not in st.session_state:
    st.session_state.timer_seconds = 25 * 60  # 25 min Pomodoro default

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_target_end" not in st.session_state:
    st.session_state.timer_target_end = None

# --- Sidebar: Workspace & Controls ---
with st.sidebar:
    st.markdown("### Workspace Controls")

    # API Key Handling (checks st.secrets first, then environment variable)
    env_key = ""
    try:
        if hasattr(st, "secrets") and "NVIDIA_API_KEY" in st.secrets:
            env_key = st.secrets["NVIDIA_API_KEY"]
    except Exception:
        pass
    if not env_key:
        env_key = os.getenv("NVIDIA_API_KEY", "")

    api_key = st.text_input(
        "NVIDIA API Key",
        value=env_key,
        type="password",
        help="Reads from Streamlit Secrets or NVIDIA_API_KEY environment variable.",
    )

    st.markdown("---")

    # Focus Timer Section
    st.markdown("#### Study Focus Timer")
    timer_col1, timer_col2 = st.columns([1, 1])

    with timer_col1:
        timer_preset = st.selectbox(
            "Duration",
            options=["25 min (Pomodoro)", "50 min (Deep Dive)", "15 min (Review)", "5 min (Break)"],
            index=0,
            label_visibility="collapsed",
        )

    duration_map = {
        "25 min (Pomodoro)": 25 * 60,
        "50 min (Deep Dive)": 50 * 60,
        "15 min (Review)": 15 * 60,
        "5 min (Break)": 5 * 60,
    }

    selected_duration = duration_map[timer_preset]

    # Timer display & controls
    mins, secs = divmod(st.session_state.timer_seconds, 60)
    timer_str = f"{mins:02d}:{secs:02d}"

    st.markdown(
        f"""
        <div class="timer-card">
            <div class="timer-label">Focus Interval</div>
            <div class="timer-display">{timer_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t_btn_col1, t_btn_col2 = st.columns(2)
    with t_btn_col1:
        if st.button("Reset Timer", use_container_width=True):
            st.session_state.timer_seconds = selected_duration
            st.rerun()

    with t_btn_col2:
        if st.button("Set Preset", use_container_width=True):
            st.session_state.timer_seconds = selected_duration
            st.rerun()

    st.markdown("---")

    # Study Persona & Mode
    st.markdown("#### Learning Persona")
    chosen_preset_name = st.selectbox(
        "Active Mode",
        options=list(STUDY_PRESETS.keys()),
        index=0,
    )

    system_prompt = st.text_area(
        "System Instructions",
        value=STUDY_PRESETS[chosen_preset_name],
        height=100,
    )

    st.markdown("---")

    # Model & Reasoning Settings
    st.markdown("#### Model Parameters")
    model = st.selectbox(
        "Inference Model",
        options=[
            "nvidia/nemotron-3-ultra-550b-a55b",
            "deepseek-ai/deepseek-r1",
            "meta/llama-3.3-70b-instruct",
        ],
        index=0,
    )

    enable_thinking = st.toggle(
        "Enable Chain-of-Thought",
        value=True,
        help="Captures internal reasoning process before generating answers.",
    )

    auto_expand_thoughts = st.checkbox(
        "Always Expand Reasoning Trace",
        value=False,
    )

    with st.expander("Advanced Inference Settings"):
        temperature = st.slider("Temperature", 0.0, 1.5, 1.0 if enable_thinking else 0.7, 0.05)
        top_p = st.slider("Top-P", 0.01, 1.0, 0.95, 0.01)
        max_tokens = st.slider("Max Tokens", 512, 16384, 4096, 512)

    st.markdown("---")

    # Session Management & Export
    st.markdown("#### Chat Records & Export")
    if st.session_state.messages:
        # Generate Markdown Export
        md_export = f"# Study Session Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, m in enumerate(st.session_state.messages):
            role_label = "Student" if m["role"] == "user" else "Nemotron Mentor"
            md_export += f"### {role_label}\n\n"
            if m.get("reasoning"):
                md_export += f"<details><summary>Reasoning Process</summary>\n\n```text\n{m['reasoning']}\n```\n</details>\n\n"
            md_export += f"{m['content']}\n\n---\n\n"

        st.download_button(
            label="Download Session as Markdown",
            data=md_export,
            file_name=f"study_session_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        json_export = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            label="Download Session as JSON",
            data=json_export,
            file_name=f"study_session_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Main Workspace Header ---
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-logo">N</div>
        <div>
            <div class="brand-title">
                Nemotron Learning & Coding Studio
                <span class="study-badge">Reasoning Enabled</span>
            </div>
            <div class="brand-subtitle">
                Professional Algorithmic Study Environment with Step-by-Step Chain-of-Thought
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Study Tabs ---
chat_tab, scratchpad_tab, guide_tab = st.tabs(["Interactive Study Session", "Study Notes & Scratchpad", "Study Guide & Tips"])

with scratchpad_tab:
    st.markdown("#### Session Notes & Code Scratchpad")
    st.caption("Jot down algorithmic patterns, definitions, or code snippets here during your study session. Notes persist while this tab is open.")
    st.session_state.study_notes = st.text_area(
        "Notes Content",
        value=st.session_state.study_notes,
        height=320,
        placeholder="e.g. Binary Search invariant: low <= high, mid = low + (high - low) // 2 ...",
        label_visibility="collapsed",
    )
    if st.session_state.study_notes:
        st.download_button(
            label="Save Notes to Disk (.txt)",
            data=st.session_state.study_notes,
            file_name=f"study_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

with guide_tab:
    st.markdown("#### Effective Coding & Study Techniques with Nemotron")
    st.markdown(
        """
        - **Read the Reasoning Trace**: When tackling complex coding problems, expand the **Model Reasoning** accordion. Seeing how the model breaks down constraints, edge cases, and invariants teaches sound problem-solving intuition.
        - **Practice Socratic Inquiries**: Instead of asking *"Write code for LRU Cache"*, ask *"What data structures can achieve O(1) get and put in an LRU Cache, and how do they coordinate?"*
        - **Save Your Study Logs**: Use the sidebar **Download Session as Markdown** button at the end of each study block to build your personal knowledge base in Obsidian, Notion, or GitHub.
        """
    )

with chat_tab:
    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("reasoning"):
                with st.expander("Model Reasoning & Chain-of-Thought", expanded=auto_expand_thoughts):
                    st.markdown(f"```text\n{msg['reasoning']}\n```")
            st.markdown(msg["content"])

    # User Input Field
    user_query = st.chat_input("Enter code to review, ask an algorithm concept, or solve a problem...")

    if user_query:
        if not api_key:
            st.error("Please provide an NVIDIA API Key in the sidebar or configure it in Streamlit Cloud Secrets.")
            st.stop()

        # Append and display user query
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Initialize client
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )

        api_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            api_messages.append({"role": m["role"], "content": m["content"]})

        with st.chat_message("assistant"):
            thought_placeholder = None
            thought_status = None
            full_reasoning = ""
            full_content = ""

            if enable_thinking:
                thought_status = st.status("Analyzing problem and deriving reasoning trace...", expanded=True)
                with thought_status:
                    thought_placeholder = st.empty()

            response_placeholder = st.empty()

            extra_body = {}
            if enable_thinking:
                extra_body["chat_template_kwargs"] = {"enable_thinking": True}

            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                )

                for chunk in completion:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    # 1. Reasoning trace
                    reasoning_chunk = getattr(delta, "reasoning_content", None)
                    if reasoning_chunk:
                        full_reasoning += reasoning_chunk
                        if thought_placeholder:
                            thought_placeholder.markdown(f"```text\n{full_reasoning}\n```")

                    # 2. Final response
                    if delta.content is not None:
                        if enable_thinking and full_reasoning and thought_status:
                            thought_status.update(
                                label="Reasoning complete",
                                state="complete",
                                expanded=auto_expand_thoughts,
                            )
                        full_content += delta.content
                        response_placeholder.markdown(full_content + "▌")

                # Clean render
                response_placeholder.markdown(full_content)

                if enable_thinking and thought_status:
                    thought_status.update(
                        label="Reasoning complete" if full_reasoning else "No explicit reasoning trace returned",
                        state="complete",
                        expanded=auto_expand_thoughts,
                    )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_content,
                    "reasoning": full_reasoning if full_reasoning else None,
                })

            except Exception as e:
                st.error(f"Inference error: {e}")
