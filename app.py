import os
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI
import database as db

# --- Page Configuration ---
st.set_page_config(
    page_title="Classroom - AI Computer Science Mentor",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize SQLite database
db.init_db()

# --- Avatars (Clean SVG Icons, No Broken Fonts, No Emojis) ---
STUDENT_AVATAR = "https://api.iconify.design/lucide:user.svg?color=%23475569"
TEACHER_AVATAR = "https://api.iconify.design/lucide:graduation-cap.svg?color=%231e293b"

# --- Professional CSS Styles ---
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

    .db-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 0.82rem;
        color: #334155;
        margin-bottom: 12px;
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

    .topic-pill {
        display: inline-block;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.8rem;
        color: #334155;
        margin-right: 6px;
        margin-bottom: 6px;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Verified Live Active Providers and Model IDs ---
PROVIDERS = {
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "models": [
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/nemotron-4-340b-instruct",
            "mistralai/mistral-large-2-instruct",
            "meta/codellama-70b",
            "ibm/granite-3.0-8b-instruct",
            "nvidia/nemotron-3-ultra-550b-a55b",
        ],
        "supports_thinking": True,
        "env_var": "NVIDIA_API_KEY",
    },
    "OpenRouter (Free Tier)": {
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

if "suggested_prompt" not in st.session_state:
    st.session_state.suggested_prompt = None

# --- Sidebar: ChatGPT-Style Chat History & Controls ---
with st.sidebar:
    # 1. New Chat Button
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
                label = f"{'▶ ' if is_active else ''}{s['title'][:22]}"
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

    # 3. Provider & Model Configuration
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
chat_tab, scratchpad_tab, storage_tab = st.tabs(["Interactive Classroom", "Study Notes & Scratchpad", "Database & Storage Transparency"])

with scratchpad_tab:
    st.markdown("#### Session Notes & Code Scratchpad")
    st.caption("Jot down notes or code patterns during your lesson. Notes persist across questions.")
    st.session_state.study_notes = st.text_area(
        "Notes Content",
        value=st.session_state.study_notes,
        height=320,
        placeholder="e.g. Array indexing is O(1) contiguous memory...",
        label_visibility="collapsed",
    )
    if st.session_state.study_notes:
        st.download_button(
            label="Save Notes to Disk (.txt)",
            data=st.session_state.study_notes,
            file_name=f"classroom_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
        )

with storage_tab:
    st.markdown("#### Database Storage Location & Transparency")
    stats = db.get_database_stats()
    st.markdown(
        f"""
        <div class="db-card">
            <strong>Database Type:</strong> SQLite 3 (ACID-Compliant Relational Database)<br>
            <strong>Storage File Location:</strong> <code>{stats['path']}</code><br>
            <strong>Total Saved Lessons:</strong> {stats['sessions']}<br>
            <strong>Total Message Turns:</strong> {stats['messages']}<br>
            <strong>Database File Size:</strong> {stats['size_kb']} KB
        </div>
        """,
        unsafe_allow_html=True,
    )

    db_down_col1, db_down_col2 = st.columns(2)
    with db_down_col1:
        if os.path.exists(stats["path"]):
            with open(stats["path"], "rb") as db_file:
                st.download_button(
                    label="Download Raw Database (.db file)",
                    data=db_file.read(),
                    file_name="classroom.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                )
    with db_down_col2:
        if session_messages:
            md_export = f"# Classroom Lesson Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            for m in session_messages:
                role_label = "Student" if m["role"] == "user" else "Instructor"
                md_export += f"### {role_label}\n\n"
                if m.get("reasoning"):
                    md_export += f"<details><summary>Reasoning Process</summary>\n\n```text\n{m['reasoning']}\n```\n</details>\n\n"
                md_export += f"{m['content']}\n\n---\n\n"

            st.download_button(
                label="Export Current Lesson as Markdown (.md)",
                data=md_export,
                file_name=f"lesson_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

with chat_tab:
    # Quick Topic Starter Buttons if chat is empty
    if len(session_messages) == 0:
        st.markdown("**Suggested Topics to Explore:**")
        chip1, chip2, chip3, chip4 = st.columns(4)
        with chip1:
            if st.button("Arrays & Contiguous Memory", use_container_width=True):
                st.session_state.suggested_prompt = "Explain how Arrays work in memory, why indexing is O(1), and common edge cases."
                st.rerun()
        with chip2:
            if st.button("Recursion vs Iteration", use_container_width=True):
                st.session_state.suggested_prompt = "Teach me Recursion from scratch with a call stack diagram and contrast it with iteration."
                st.rerun()
        with chip3:
            if st.button("Pointers & Dynamic Memory", use_container_width=True):
                st.session_state.suggested_prompt = "Explain Pointers and Heap vs Stack memory in simple terms using a real-world analogy."
                st.rerun()
        with chip4:
            if st.button("Dynamic Programming", use_container_width=True):
                st.session_state.suggested_prompt = "Break down Dynamic Programming, memoization, and tabulation with an intuitive example."
                st.rerun()

    # Render Chat History
    for msg in session_messages:
        avatar = STUDENT_AVATAR if msg["role"] == "user" else TEACHER_AVATAR
        with st.chat_message(msg["role"], avatar=avatar):
            if msg.get("reasoning"):
                with st.expander("Model Reasoning & Chain-of-Thought", expanded=auto_expand_thoughts):
                    st.markdown(f"```text\n{msg['reasoning']}\n```")
            st.markdown(msg["content"])

    # Handle Suggested Prompt or Direct Input
    active_prompt = None
    if st.session_state.suggested_prompt:
        active_prompt = st.session_state.suggested_prompt
        st.session_state.suggested_prompt = None
    else:
        # st.chat_input natively sends immediately when the user presses Enter
        active_prompt = st.chat_input("Enter any topic (press Enter to send)...")

    if active_prompt:
        if not active_api_key:
            st.error(f"Please provide an API Key for {chosen_provider_name} in the sidebar.")
            st.stop()

        # Auto-update session title on first message
        if len(session_messages) == 0:
            short_title = active_prompt[:32] + ("..." if len(active_prompt) > 32 else "")
            db.update_session_title(st.session_state.active_session_id, short_title)

        # Save student message to SQLite
        db.add_message(st.session_state.active_session_id, "user", active_prompt)

        with st.chat_message("user", avatar=STUDENT_AVATAR):
            st.markdown(active_prompt)

        updated_messages = db.get_session_messages(st.session_state.active_session_id)

        # Truncate context according to slider
        if context_option == "Full History":
            selected_history = updated_messages
        else:
            num_to_keep = int(context_option) * 2
            selected_history = updated_messages[-num_to_keep:]

        client = OpenAI(
            base_url=base_url,
            api_key=active_api_key,
        )

        api_messages = [{"role": "system", "content": system_prompt}]
        for m in selected_history:
            api_messages.append({"role": m["role"], "content": m["content"]})

        with st.chat_message("assistant", avatar=TEACHER_AVATAR):
            thought_placeholder = None
            thought_status = None
            full_reasoning = ""
            full_content = ""

            if enable_thinking:
                thought_status = st.status("Analyzing pedagogy and structuring lesson plan...", expanded=True)
                with thought_status:
                    thought_placeholder = st.empty()

            response_placeholder = st.empty()

            def execute_stream(target_model, with_thinking):
                extra_body = {}
                if with_thinking and chosen_provider_name == "NVIDIA NIM":
                    extra_body["chat_template_kwargs"] = {"enable_thinking": True}

                return client.chat.completions.create(
                    model=target_model,
                    messages=api_messages,
                    temperature=1.0 if with_thinking else 0.7,
                    extra_body=extra_body if extra_body else None,
                    stream=True,
                )

            current_model = model
            completion = None

            try:
                completion = execute_stream(current_model, enable_thinking)
            except Exception as e:
                err_text = str(e)
                # Auto-failover: If the requested model is gone (410) or unauthorized/quota (403)
                if "410" in err_text or "403" in err_text:
                    if chosen_provider_name == "NVIDIA NIM" and current_model != "nvidia/llama-3.1-nemotron-70b-instruct":
                        st.info("Auto-switching to verified active model: nvidia/llama-3.1-nemotron-70b-instruct")
                        current_model = "nvidia/llama-3.1-nemotron-70b-instruct"
                        try:
                            completion = execute_stream(current_model, False)
                        except Exception as e2:
                            err_text = str(e2)

                if completion is None:
                    if "403" in err_text or "Authorization failed" in err_text:
                        st.error(
                            f"**Authorization Failed (HTTP 403) for {chosen_provider_name}**\n\n"
                            "Your API key was rejected by the provider (it may have expired or exhausted its free trial allotment).\n\n"
                            "**How to get it running in 30 seconds:**\n"
                            "1. **Option A (Free OpenRouter)**: In the sidebar, change Provider to **OpenRouter (Free Tier)**. Get an instant free key at [openrouter.ai](https://openrouter.ai/) (no credit card) and use `deepseek/deepseek-r1:free`.\n"
                            "2. **Option B (Free Groq)**: In the sidebar, select **Groq (Ultra-Fast Free Tier)** with a free key from [console.groq.com](https://console.groq.com/).\n"
                            "3. **Option C (NVIDIA)**: Generate a fresh key at [build.nvidia.com](https://build.nvidia.com/) and paste it directly into the sidebar field."
                        )
                    elif "410" in err_text:
                        st.error(
                            f"**Model Deprecated / Gone (HTTP 410)**: `{current_model}` is no longer hosted at this endpoint. "
                            "Please choose `nvidia/llama-3.1-nemotron-70b-instruct` from the model list in the sidebar."
                        )
                    else:
                        st.error(f"Inference error: {err_text}")

            if completion is not None:
                try:
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

                    response_placeholder.markdown(full_content)

                    if enable_thinking and thought_status:
                        thought_status.update(
                            label="Lesson plan derived" if full_reasoning else "Lesson response complete",
                            state="complete",
                            expanded=auto_expand_thoughts,
                        )

                    # Persist response to SQLite database
                    db.add_message(
                        st.session_state.active_session_id,
                        "assistant",
                        full_content,
                        full_reasoning if full_reasoning else None,
                    )
                except Exception as stream_err:
                    st.error(f"Stream interruption: {stream_err}")
