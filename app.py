import os
import glob
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

    .status-badge {
        display: inline-block;
        padding: 2px 6px;
        font-size: 0.70rem;
        font-weight: 600;
        border-radius: 4px;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
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
        margin-bottom: 12px;
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

# --- Ensure Local Storage Directory Exists ---
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "saved_sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# --- Teaching & Pedagogy Presets ---
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
if "messages" not in st.session_state:
    st.session_state.messages = []

if "study_notes" not in st.session_state:
    st.session_state.study_notes = ""

if "timer_seconds" not in st.session_state:
    st.session_state.timer_seconds = 25 * 60

if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = ""

# --- Sidebar: Workspace & Controls ---
with st.sidebar:
    st.markdown("### Workspace Controls")

    # API Key Configuration
    st.markdown("#### API Key Management")

    # Determine default/fallback key
    default_key = ""
    try:
        if hasattr(st, "secrets") and "NVIDIA_API_KEY" in st.secrets:
            default_key = st.secrets["NVIDIA_API_KEY"]
    except Exception:
        pass
    if not default_key:
        default_key = os.getenv("NVIDIA_API_KEY", "")

    current_key_val = st.session_state.custom_api_key if st.session_state.custom_api_key else default_key

    entered_key = st.text_input(
        "NVIDIA API Key",
        value=current_key_val,
        type="password",
        help="Paste your personal key here at any time. It takes effect immediately.",
    )

    if entered_key != st.session_state.custom_api_key:
        st.session_state.custom_api_key = entered_key

    active_key = st.session_state.custom_api_key if st.session_state.custom_api_key else default_key

    if active_key:
        if active_key == default_key and default_key:
            st.markdown('<span class="status-badge">Default System Key Loaded</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge-active">Personal Key Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge">No API Key Set</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Context Window & Memory Depth
    st.markdown("#### Context Window (Memory Depth)")
    context_option = st.select_slider(
        "Conversation History Included",
        options=[2, 4, 6, 10, 16, 24, "Full History"],
        value=10,
        help="Controls how many previous dialogue turns are sent to the model. Smaller windows reduce token costs; larger windows maintain longer context.",
    )

    st.markdown("---")

    # Focus Study Timer
    st.markdown("#### Focus Study Timer")
    timer_preset = st.selectbox(
        "Duration Preset",
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

    # Teaching Persona & Style
    st.markdown("#### Teaching Mode")
    chosen_preset_name = st.selectbox(
        "Pedagogical Style",
        options=list(TEACHING_PRESETS.keys()),
        index=0,
    )

    system_prompt = st.text_area(
        "Instructor Guidelines",
        value=TEACHING_PRESETS[chosen_preset_name],
        height=130,
    )

    st.markdown("---")

    # Model & Reasoning Parameters
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

    with st.expander("Advanced Hyperparameters"):
        temperature = st.slider("Temperature", 0.0, 1.5, 1.0 if enable_thinking else 0.7, 0.05)
        top_p = st.slider("Top-P", 0.01, 1.0, 0.95, 0.01)
        max_tokens = st.slider("Max Output Tokens", 512, 16384, 4096, 512)

    st.markdown("---")

    # Chat Records: Save, Load & Export
    st.markdown("#### Chat Storage & History")

    # 1. Save Current Session Locally
    save_col1, save_col2 = st.columns([2, 1])
    with save_col1:
        session_title = st.text_input("Session Topic", placeholder="e.g. Recursion Lesson", label_visibility="collapsed")
    with save_col2:
        if st.button("Save", use_container_width=True):
            if st.session_state.messages:
                clean_title = "".join(c for c in session_title if c.isalnum() or c in (" ", "_", "-")).strip()
                if not clean_title:
                    clean_title = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                filename = f"{clean_title}.json"
                filepath = os.path.join(SESSIONS_DIR, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.messages, f, indent=2)
                st.success(f"Saved: {clean_title}")
                st.rerun()
            else:
                st.warning("No messages to save yet.")

    # 2. Load Existing Saved Session
    saved_files = glob.glob(os.path.join(SESSIONS_DIR, "*.json"))
    if saved_files:
        session_names = [os.path.basename(f).replace(".json", "") for f in saved_files]
        selected_session = st.selectbox("Load Saved Lesson", options=["Select session..."] + session_names)
        if selected_session != "Select session...":
            if st.button("Restore Selected Lesson", use_container_width=True):
                target_file = os.path.join(SESSIONS_DIR, f"{selected_session}.json")
                with open(target_file, "r", encoding="utf-8") as f:
                    st.session_state.messages = json.load(f)
                st.rerun()

    # 3. Import Session from JSON file
    uploaded_session = st.file_uploader("Upload Past Session (.json)", type=["json"], label_visibility="collapsed")
    if uploaded_session is not None:
        if st.button("Load Uploaded File", use_container_width=True):
            try:
                loaded_data = json.load(uploaded_session)
                if isinstance(loaded_data, list):
                    st.session_state.messages = loaded_data
                    st.success("Lesson restored successfully.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading JSON file: {e}")

    # 4. Export Buttons
    if st.session_state.messages:
        md_export = f"# Study Session Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        for idx, m in enumerate(st.session_state.messages):
            role_label = "Student" if m["role"] == "user" else "Nemotron Instructor"
            md_export += f"### {role_label}\n\n"
            if m.get("reasoning"):
                md_export += f"<details><summary>Reasoning Process</summary>\n\n```text\n{m['reasoning']}\n```\n</details>\n\n"
            md_export += f"{m['content']}\n\n---\n\n"

        st.download_button(
            label="Export as Markdown (.md)",
            data=md_export,
            file_name=f"lesson_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        json_export = json.dumps(st.session_state.messages, indent=2)
        st.download_button(
            label="Export as JSON (.json)",
            data=json_export,
            file_name=f"lesson_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
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
                Interactive Coding Professor - Intuitive Explanations, Deep Concepts & Architecture
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Study Tabs ---
chat_tab, scratchpad_tab, guide_tab = st.tabs(["Interactive Classroom", "Study Notes & Scratchpad", "Teaching Methodology"])

with scratchpad_tab:
    st.markdown("#### Session Notes & Code Scratchpad")
    st.caption("Jot down notes, key takeaways, or algorithmic patterns during your lecture. Notes persist across questions.")
    st.session_state.study_notes = st.text_area(
        "Notes Content",
        value=st.session_state.study_notes,
        height=320,
        placeholder="e.g. Memory Layout of Pointers: Variable has an address and a value...",
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
    st.markdown("#### How Your AI Teacher Explains Topics")
    st.markdown(
        """
        - **1. Analogies First**: Complex abstractions are anchored in familiar physical metaphors before equations or syntax appear.
        - **2. The 'Why'**: Explains why computer scientists invented this solution, and what breaks without it.
        - **3. Trace the Reasoning**: Expand the **Model Reasoning** accordion on any response to see how the teacher analyzes your question before explaining it.
        - **4. Save & Revisit**: Use the sidebar **Save** button to store your lessons under topics like *Dynamic Programming* or *Memory Management* and reload them anytime.
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
    user_query = st.chat_input("Enter any topic you want to learn (e.g. Recursion, Pointers, Concurrency, Graph DFS)...")

    if user_query:
        if not active_key:
            st.error("Please provide an NVIDIA API Key in the sidebar.")
            st.stop()

        # Append and display user query
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Initialize client
        client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=active_key,
        )

        # Apply Context Window Trimming
        if context_option == "Full History":
            selected_history = st.session_state.messages
        else:
            num_messages_to_keep = int(context_option) * 2
            selected_history = st.session_state.messages[-num_messages_to_keep:]

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
                                label="Lesson plan derived",
                                state="complete",
                                expanded=auto_expand_thoughts,
                            )
                        full_content += delta.content
                        response_placeholder.markdown(full_content + "▌")

                # Clean render
                response_placeholder.markdown(full_content)

                if enable_thinking and thought_status:
                    thought_status.update(
                        label="Lesson plan derived" if full_reasoning else "No explicit reasoning trace returned",
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
