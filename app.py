import os
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI
import database as db

# --- Page Configuration ---
st.set_page_config(
    page_title="Classroom - AI Code Mentor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize SQLite database
db.init_db()

# --- Professional CSS Styles (No Emojis, Clean Modern Classroom Theme) ---
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
        margin-bottom: 18px;
    }

    .brand-logo {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f8fafc;
        font-weight: 700;
        font-size: 19px;
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

    .status-badge-active {
        display: inline-block;
        padding: 2px 6px;
        font-size: 0.70rem;
        font-weight: 600;
        border-radius: 4px;
        background: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
    }

    .status-badge-warn {
        display: inline-block;
        padding: 2px 6px;
        font-size: 0.70rem;
        font-weight: 600;
        border-radius: 4px;
        background: #fef2f2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    .timer-card {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
    }

    .timer-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        text-align: center;
        letter-spacing: 2px;
        margin: 4px 0;
    }

    .timer-label {
        font-size: 0.70rem;
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

# --- Provider Presets ---
PROVIDERS = {
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "nvidia/nemotron-3-ultra-550b-a55b",
        "models": [
            "nvidia/nemotron-3-ultra-550b-a55b",
            "meta/llama-3.3-70b-instruct",
            "deepseek-ai/deepseek-r1",
            "nvidia/llama-3.1-nemotron-70b-instruct",
        ],
        "supports_thinking": True,
        "env_var": "NVIDIA_API_KEY",
    },
    "DeepSeek (Official)": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "supports_thinking": True,
        "env_var": "DEEPSEEK_API_KEY",
    },
    "OpenRouter (Free Models)": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "deepseek/deepseek-r1:free",
        "models": [
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-exp:free",
            "qwen/qwen-2.5-coder-32b-instruct:free",
        ],
        "supports_thinking": False,
        "env_var": "OPENROUTER_API_KEY",
    },
    "Groq (Ultra-Fast Free Tier)": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "deepseek-r1-distill-llama-70b",
            "llama3-70b-8192",
        ],
        "supports_thinking": False,
        "env_var": "GROQ_API_KEY",
    },
    "Custom OpenAI-Compatible": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "supports_thinking": False,
        "env_var": "CUSTOM_API_KEY",
    },
}

# --- Pedagogical Presets ---
TEACHING_PRESETS = {
    "Master Teacher (Deep & Simple Intuition)": (
        "You are an inspiring, world-class Computer Science Professor and Code Mentor. "
        "Your mission is to teach the student any topic they ask in depth, but in an extraordinarily simple and intuitive way.\n\n"
        "Follow this structured pedagogical blueprint for every lesson:\n"
        "1. Real-World Analogy: Start with a concrete, everyday analogy to establish intuition before introducing technical jargon.\n"
        "2. The Problem It Solves: Explain why this concept was invented and what fails without it.\n"
        "3. Step-by-Step Deep-Dive: Walk through the core mechanics logically from the ground up.\n"
        "4. Mental Model / Diagram: Use clean text diagrams, ASCII art, or step-by-step state traces to visualize flow.\n"
        "5. Clean, Annotated Code: Provide clear, readable code with descriptive comments on critical lines.\n"
        "6. Time & Space Complexity: Clearly analyze efficiency (Big-O).\n"
        "7. Beginner Pitfalls: Point out the 2-3 most common mistakes learners make.\n"
        "8. Quick Knowledge Check: Finish with a single engaging question or mini-exercise for the student to confirm understanding."
    ),
    "Socratic Guide (Interactive Learning)": (
        "You are a Socratic Coding Tutor. Instead of dumping full solutions, you guide the student step-by-step. "
        "Explain concepts simply, ask thought-provoking questions, encourage the student to think through edge cases, "
        "and provide hints that lead them to discover the answer themselves."
    ),
    "Bug Hunter & Code Auditor": (
        "You are a Senior Software Verification Engineer. Analyze submitted code meticulously. "
        "Identify logic bugs, off-by-one errors, memory inefficiencies, concurrency issues, "
        "and security flaws. Provide the corrected implementation with clear explanations."
    ),
    "Algorithms & Data Structures Specialist": (
        "You are an Algorithms Specialist. For every problem, provide: 1) Intuition and brute-force approach, "
        "2) Optimal solution with detailed walkthrough, 3) Time and Space complexity analysis, "
        "4) Python/C++ implementation with comments on non-trivial lines."
    ),
}

# --- Session State Initialization ---
if "active_session_id" not in st.session_state:
    all_sessions = db.list_sessions()
    if all_sessions:
        st.session_state.active_session_id = all_sessions[0]["id"]
    else:
        st.session_state.active_session_id = db.create_session("Welcome Lesson")

if "study_notes" not in st.session_state:
    st.session_state.study_notes = ""

if "timer_seconds" not in st.session_state:
    st.session_state.timer_seconds = 25 * 60

if "provider_keys" not in st.session_state:
    st.session_state.provider_keys = {}

# --- Sidebar: ChatGPT-Style Chat History & Controls ---
with st.sidebar:
    # 1. New Chat Button (ChatGPT-Style)
    if st.button("+ New Lesson", use_container_width=True, type="primary"):
        new_id = db.create_session("New Lesson")
        st.session_state.active_session_id = new_id
        st.rerun()

    # 2. Recent Chat History List (Stored in SQLite Database)
    st.markdown("#### Chat History")
    recent_sessions = db.list_sessions()
    if recent_sessions:
        for s in recent_sessions[:12]:
            is_active = (s["id"] == st.session_state.active_session_id)
            btn_col, del_col = st.columns([5, 1])
            with btn_col:
                label = f"{'▶ ' if is_active else ''}{s['title'][:24]}"
                if st.button(label, key=f"session_{s['id']}", use_container_width=True):
                    st.session_state.active_session_id = s["id"]
                    st.rerun()
            with del_col:
                if st.button("X", key=f"del_{s['id']}", help="Delete chat"):
                    db.delete_session(s["id"])
                    if st.session_state.active_session_id == s["id"]:
                        remaining = db.list_sessions()
                        st.session_state.active_session_id = remaining[0]["id"] if remaining else db.create_session("New Lesson")
                    st.rerun()
    else:
        st.caption("No saved chats yet.")

    st.markdown("---")

    # 3. Provider & Model Setup (Supports NVIDIA, DeepSeek, OpenRouter, Groq)
    st.markdown("#### AI Provider & Model")
    chosen_provider_name = st.selectbox(
        "Provider",
        options=list(PROVIDERS.keys()),
        index=0,
    )
    provider_info = PROVIDERS[chosen_provider_name]

    # Resolve default key from secrets or env
    fallback_key = ""
    try:
        if hasattr(st, "secrets") and provider_info["env_var"] in st.secrets:
            fallback_key = st.secrets[provider_info["env_var"]]
    except Exception:
        pass
    if not fallback_key:
        fallback_key = os.getenv(provider_info["env_var"], "")

    # Check session state for user-entered key
    stored_key = st.session_state.provider_keys.get(chosen_provider_name, fallback_key)

    api_key_input = st.text_input(
        f"{chosen_provider_name} API Key",
        value=stored_key,
        type="password",
        help=f"Paste key for {chosen_provider_name}. Takes effect immediately.",
    )
    st.session_state.provider_keys[chosen_provider_name] = api_key_input
    active_api_key = api_key_input.strip()

    if active_api_key:
        st.markdown('<span class="status-badge-active">API Key Configured</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-warn">API Key Required</span>', unsafe_allow_html=True)

    # Base URL & Model input
    if chosen_provider_name == "Custom OpenAI-Compatible":
        base_url = st.text_input("Custom Base URL", value="https://api.openai.com/v1")
        model = st.text_input("Custom Model Name", value="gpt-4o")
    else:
        base_url = provider_info["base_url"]
        model = st.selectbox("Model", options=provider_info["models"], index=0)

    enable_thinking = st.toggle(
        "Enable Chain-of-Thought",
        value=provider_info["supports_thinking"],
        help="Enables deep reasoning extraction.",
    )

    auto_expand_thoughts = st.checkbox("Always Expand Reasoning Trace", value=False)

    st.markdown("---")

    # 4. Context Window (Memory Depth)
    st.markdown("#### Context Window (Memory Depth)")
    context_option = st.select_slider(
        "Turns Remembered",
        options=[2, 4, 6, 10, 16, 24, "Full History"],
        value=10,
        help="Limits past turns sent to save tokens and prevent rate limits.",
    )

    st.markdown("---")

    # 5. Focus Study Timer
    st.markdown("#### Study Focus Timer")
    timer_preset = st.selectbox(
        "Interval Preset",
        options=["25 min (Pomodoro)", "50 min (Deep Dive)", "15 min (Review)", "5 min (Break)"],
        index=0,
    )
    duration_map = {
        "25 min (Pomodoro)": 25 * 60,
        "50 min (Deep Dive)": 50 * 60,
        "15 min (Review)": 15 * 60,
        "5 min (Break)": 5 * 60,
    }
    selected_duration = duration_map[timer_preset]
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

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        if st.button("Reset Timer", use_container_width=True):
            st.session_state.timer_seconds = selected_duration
            st.rerun()
    with t_col2:
        if st.button("Set Preset", use_container_width=True):
            st.session_state.timer_seconds = selected_duration
            st.rerun()

    st.markdown("---")

    # 6. Teaching Style
    st.markdown("#### Instructor Mode")
    chosen_preset_name = st.selectbox("Pedagogy", options=list(TEACHING_PRESETS.keys()), index=0)
    system_prompt = st.text_area("System Prompt", value=TEACHING_PRESETS[chosen_preset_name], height=110)

# --- Header ---
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-logo">C</div>
        <div>
            <div class="brand-title">
                Classroom
                <span class="study-badge">AI Code & CS Mentor</span>
            </div>
            <div class="brand-subtitle">
                Interactive Computer Science Studio - Deep Intuition, Relatable Analogies & Step-by-Step Architecture
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Fetch Current Session Messages from SQLite ---
session_messages = db.get_session_messages(st.session_state.active_session_id)

# --- Study Tabs ---
chat_tab, scratchpad_tab, export_tab = st.tabs(["Interactive Classroom", "Study Notes & Scratchpad", "Export & Backup"])

with scratchpad_tab:
    st.markdown("#### Session Notes & Code Scratchpad")
    st.caption("Jot down notes or code patterns during your lesson. Notes persist across questions.")
    st.session_state.study_notes = st.text_area(
        "Notes Content",
        value=st.session_state.study_notes,
        height=320,
        placeholder="e.g. Recursion Base Case: condition where recursion stops to prevent stack overflow...",
        label_visibility="collapsed",
    )
    if st.session_state.study_notes:
        st.download_button(
            label="Save Notes to Disk (.txt)",
            data=st.session_state.study_notes,
            file_name=f"classroom_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

with export_tab:
    st.markdown("#### Export Current Lesson")
    if session_messages:
        md_export = f"# Classroom Lesson Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for m in session_messages:
            role_label = "Student" if m["role"] == "user" else "Instructor"
            md_export += f"### {role_label}\n\n"
            if m.get("reasoning"):
                md_export += f"<details><summary>Reasoning Process</summary>\n\n```text\n{m['reasoning']}\n```\n</details>\n\n"
            md_export += f"{m['content']}\n\n---\n\n"

        st.download_button(
            label="Download Lesson as Markdown (.md)",
            data=md_export,
            file_name=f"classroom_lesson_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        json_export = json.dumps(session_messages, indent=2)
        st.download_button(
            label="Download Lesson as JSON (.json)",
            data=json_export,
            file_name=f"classroom_lesson_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.caption("No messages to export in this lesson yet.")

with chat_tab:
    # Render Chat History from SQLite
    for msg in session_messages:
        with st.chat_message(msg["role"]):
            if msg.get("reasoning"):
                with st.expander("Model Reasoning & Chain-of-Thought", expanded=auto_expand_thoughts):
                    st.markdown(f"```text\n{msg['reasoning']}\n```")
            st.markdown(msg["content"])

    # User Input Field
    user_query = st.chat_input("Enter any topic you want to learn (e.g. Recursion, Pointers, Concurrency, Graph DFS)...")

    if user_query:
        if not active_api_key:
            st.error(f"Please provide an API Key for {chosen_provider_name} in the sidebar.")
            st.stop()

        # If this is the first message in the session, update session title to the topic
        if len(session_messages) == 0:
            short_title = user_query[:32] + ("..." if len(user_query) > 32 else "")
            db.update_session_title(st.session_state.active_session_id, short_title)

        # Save student message to SQLite
        db.add_message(st.session_state.active_session_id, "user", user_query)

        with st.chat_message("user"):
            st.markdown(user_query)

        # Reload updated messages from SQLite
        updated_messages = db.get_session_messages(st.session_state.active_session_id)

        # Apply Context Window Trimming
        if context_option == "Full History":
            selected_history = updated_messages
        else:
            num_to_keep = int(context_option) * 2
            selected_history = updated_messages[-num_to_keep:]

        # Initialize OpenAI client with selected provider
        client = OpenAI(
            base_url=base_url,
            api_key=active_api_key,
        )

        api_messages = [{"role": "system", "content": system_prompt}]
        for m in selected_history:
            api_messages.append({"role": m["role"], "content": m["content"]})

        with st.chat_message("assistant"):
            thought_placeholder = None
            thought_status = None
            full_reasoning = ""
            full_content = ""

            if enable_thinking:
                thought_status = st.status("Analyzing pedagogy and structuring lesson plan...", expanded=True)
                with thought_status:
                    thought_placeholder = st.empty()

            response_placeholder = st.empty()

            # Extra body logic per provider
            extra_body = {}
            if enable_thinking and chosen_provider_name == "NVIDIA NIM":
                extra_body["chat_template_kwargs"] = {"enable_thinking": True}

            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    temperature=1.0 if enable_thinking else 0.7,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                )

                for chunk in completion:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta

                    # 1. Reasoning trace (NVIDIA, DeepSeek reasoner, etc.)
                    reasoning_chunk = getattr(delta, "reasoning_content", None)
                    if reasoning_chunk:
                        full_reasoning += reasoning_chunk
                        if thought_placeholder:
                            thought_placeholder.markdown(f"```text\n{full_reasoning}\n```")

                    # 2. Content
                    if delta.content is not None:
                        if enable_thinking and full_reasoning and thought_status:
                            thought_status.update(
                                label="Lesson plan derived",
                                state="complete",
                                expanded=auto_expand_thoughts,
                            )
                        full_content += delta.content
                        response_placeholder.markdown(full_content + "▌")

                # Final render
                response_placeholder.markdown(full_content)

                if enable_thinking and thought_status:
                    thought_status.update(
                        label="Lesson plan derived" if full_reasoning else "No explicit reasoning trace returned",
                        state="complete",
                        expanded=auto_expand_thoughts,
                    )

                # Save assistant response to SQLite database
                db.add_message(
                    st.session_state.active_session_id,
                    "assistant",
                    full_content,
                    full_reasoning if full_reasoning else None,
                )

            except Exception as e:
                err_str = str(e)
                if "403" in err_str:
                    st.error(
                        f"**Authentication / Quota Error (HTTP 403) from {chosen_provider_name}**\n\n"
                        f"Your API key was rejected or the free trial credits for `{model}` have expired.\n\n"
                        "**Quick Solutions:**\n"
                        "1. **Switch Model**: In the sidebar, try `meta/llama-3.3-70b-instruct`.\n"
                        "2. **Use Free OpenRouter Models**: In the sidebar, select **OpenRouter (Free Models)** and use `deepseek/deepseek-r1:free` or `meta-llama/llama-3.3-70b-instruct:free`.\n"
                        "3. **Use DeepSeek or Groq**: Switch provider to DeepSeek or Groq in the sidebar and paste a free key.\n"
                        "4. **Update Key**: Paste a fresh key directly into the API Key input in the sidebar."
                    )
                else:
                    st.error(f"Inference error from {chosen_provider_name}: {e}")
