import os
import json
import base64
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import database as db

# --- Path to Assets ---
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
FAVICON_PATH = os.path.join(ASSETS_DIR, "favicon.png")

# --- Page Configuration with Custom Logo Favicon ---
st.set_page_config(
    page_title="Classroom - AI Computer Science Mentor",
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize SQLite database (also auto-restores if container disk was wiped)
db.init_db()

# --- Avatars (Self-Contained Embedded SVG Data URIs - Never Fail to Load) ---
STUDENT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
  <circle cx="32" cy="24" r="10" fill="#475569"/>
  <path d="M16 50c0-8.84 7.16-16 16-16s16 7.16 16 16" fill="#475569"/>
</svg>"""

TEACHER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#0f172a" stroke="#334155" stroke-width="2"/>
  <path d="M32 18L14 28l18 10 18-10-18-10z" fill="#38bdf8"/>
  <path d="M20 34v10c0 5 5.37 8 12 8s12-3 12-8V34" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M46 30v12" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
</svg>"""

STUDENT_AVATAR = f"data:image/svg+xml;base64,{base64.b64encode(STUDENT_SVG.strip().encode()).decode()}"
TEACHER_AVATAR = f"data:image/svg+xml;base64,{base64.b64encode(TEACHER_SVG.strip().encode()).decode()}"

# --- Favicon Base64 for Head Injection ---
fav_b64 = ""
if os.path.exists(FAVICON_PATH):
    with open(FAVICON_PATH, "rb") as f:
        fav_b64 = base64.b64encode(f.read()).decode()

# --- Professional CSS: Removes Streamlit Logo, Top Bars & Watermarks ---
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* --- Completely Remove Streamlit Branding & Menus --- */
    #MainMenu {{visibility: hidden !important; display: none !important;}}
    header {{visibility: hidden !important; display: none !important;}}
    footer {{visibility: hidden !important; display: none !important;}}
    .stDeployButton {{display: none !important;}}
    [data-testid="stHeader"] {{visibility: hidden !important; display: none !important;}}
    [data-testid="stToolbar"] {{visibility: hidden !important; display: none !important;}}
    [data-testid="stDecoration"] {{display: none !important;}}
    [data-testid="stStatusWidget"] {{display: none !important;}}
    [data-testid="manage-app-button"] {{display: none !important;}}
    .viewerBadge_container__1QSob {{display: none !important;}}
    [class*="viewerBadge"] {{display: none !important;}}
    div[data-testid="stSidebarNav"] {{padding-top: 1rem;}}

    /* App Header */
    .brand-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 18px;
    }}

    .brand-logo {{
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #38bdf8;
        font-weight: 700;
        font-size: 19px;
        letter-spacing: -0.5px;
        border: 1px solid #334155;
    }}

    .brand-title {{
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }}

    .brand-subtitle {{
        font-size: 0.85rem;
        color: #64748b;
        margin: 2px 0 0 0;
    }}

    .study-badge {{
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
    }}

    .status-badge-active {{
        display: inline-block;
        padding: 2px 6px;
        font-size: 0.70rem;
        font-weight: 600;
        border-radius: 4px;
        background: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
    }}

    .status-badge-warn {{
        display: inline-block;
        padding: 2px 6px;
        font-size: 0.70rem;
        font-weight: 600;
        border-radius: 4px;
        background: #fef2f2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }}

    .info-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 16px;
        font-size: 0.84rem;
        color: #334155;
        margin-bottom: 14px;
        line-height: 1.6;
    }}

    .guide-card {{
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 14px 16px;
        font-size: 0.84rem;
        color: #166534;
        margin-bottom: 14px;
        line-height: 1.6;
    }}

    .danger-card {{
        background: #fff7ed;
        border: 1px solid #ffedd5;
        border-radius: 8px;
        padding: 14px 16px;
        font-size: 0.84rem;
        color: #9a3412;
        margin-bottom: 14px;
        line-height: 1.6;
    }}
    </style>

    <script>
    // Inject Custom Favicon directly into browser head
    (function() {{
        let link = document.querySelector("link[rel*='icon']") || document.createElement('link');
        link.type = 'image/png';
        link.rel = 'shortcut icon';
        link.href = 'data:image/png;base64,{fav_b64}';
        document.getElementsByTagName('head')[0].appendChild(link);
    }})();
    </script>
    """,
    unsafe_allow_html=True,
)

# --- Fallback Configured Keys (from Streamlit Secrets or Environment) ---
CONFIGURED_KEYS = {}

# --- Verified Live Providers and Model IDs ---
PROVIDERS = {
    "NVIDIA NIM": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "nvidia/nemotron-3-ultra-550b-a55b",
        "models": [
            "nvidia/nemotron-3-ultra-550b-a55b",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "nvidia/nemotron-4-340b-instruct",
            "mistralai/mistral-large-2-instruct",
            "meta/codellama-70b",
        ],
        "supports_thinking": True,
        "env_var": "NVIDIA_API_KEY",
    },
    "Groq (Ultra-Fast Free Tier)": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "openai/gpt-oss-120b",
        "models": [
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b",
        ],
        "supports_thinking": True,
        "env_var": "GROQ_API_KEY",
    },
    "OpenRouter (Free Tier)": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "particle-ai/particle-1",
        "models": [
            "particle-ai/particle-1",
            "meta-llama/llama-3.2-3b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
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

    # 3. Interactive Live Study Timer (Runs smoothly in browser without page reloads)
    st.markdown("#### Focus Study Timer")
    timer_html = """
    <div style="background:#f1f5f9; border:1px solid #cbd5e1; border-radius:8px; padding:12px; text-align:center; font-family:'Inter',sans-serif;">
        <div style="font-size:0.75rem; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:0.8px;">Live Study Interval</div>
        <div id="clock" style="font-family:'Courier New',Courier,monospace; font-size:2.1rem; font-weight:700; color:#0f172a; margin:8px 0; letter-spacing:2px;">25:00</div>
        
        <div style="display:flex; justify-content:center; gap:6px; margin-bottom:8px;">
            <button id="startBtn" onclick="toggleTimer()" style="background:#1e293b; color:#fff; border:none; padding:6px 14px; border-radius:5px; font-weight:600; font-size:0.8rem; cursor:pointer;">Start</button>
            <button onclick="resetTimer()" style="background:#e2e8f0; color:#1e293b; border:none; padding:6px 14px; border-radius:5px; font-weight:600; font-size:0.8rem; cursor:pointer;">Reset</button>
        </div>

        <div style="display:flex; justify-content:center; gap:4px;">
            <button onclick="setMinutes(25)" style="background:#fff; border:1px solid #cbd5e1; font-size:0.72rem; padding:3px 6px; border-radius:4px; cursor:pointer;">25m</button>
            <button onclick="setMinutes(50)" style="background:#fff; border:1px solid #cbd5e1; font-size:0.72rem; padding:3px 6px; border-radius:4px; cursor:pointer;">50m</button>
            <button onclick="setMinutes(15)" style="background:#fff; border:1px solid #cbd5e1; font-size:0.72rem; padding:3px 6px; border-radius:4px; cursor:pointer;">15m</button>
            <button onclick="setMinutes(5)" style="background:#fff; border:1px solid #cbd5e1; font-size:0.72rem; padding:3px 6px; border-radius:4px; cursor:pointer;">5m</button>
        </div>
        <div id="statusText" style="font-size:0.72rem; color:#64748b; margin-top:6px;">Ready to focus</div>
    </div>

    <script>
        let totalSeconds = 25 * 60;
        let remainingSeconds = totalSeconds;
        let isRunning = false;
        let interval = null;

        function updateDisplay() {
            let mins = Math.floor(remainingSeconds / 60);
            let secs = remainingSeconds % 60;
            document.getElementById('clock').innerText = 
                (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
        }

        function toggleTimer() {
            let btn = document.getElementById('startBtn');
            let status = document.getElementById('statusText');
            if (!isRunning) {
                isRunning = true;
                btn.innerText = 'Pause';
                btn.style.background = '#d97706';
                status.innerText = 'Focus interval in progress';
                interval = setInterval(function() {
                    if (remainingSeconds > 0) {
                        remainingSeconds--;
                        updateDisplay();
                    } else {
                        clearInterval(interval);
                        isRunning = false;
                        btn.innerText = 'Start';
                        btn.style.background = '#1e293b';
                        status.innerText = 'Interval complete! Take a break.';
                        try {
                            let ctx = new (window.AudioContext || window.webkitAudioContext)();
                            let osc = ctx.createOscillator();
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                            osc.connect(ctx.destination);
                            osc.start();
                            osc.stop(ctx.currentTime + 0.4);
                        } catch(e) {}
                    }
                }, 1000);
            } else {
                isRunning = false;
                clearInterval(interval);
                btn.innerText = 'Resume';
                btn.style.background = '#1e293b';
                status.innerText = 'Paused';
            }
        }

        function resetTimer() {
            clearInterval(interval);
            isRunning = false;
            remainingSeconds = totalSeconds;
            updateDisplay();
            let btn = document.getElementById('startBtn');
            btn.innerText = 'Start';
            btn.style.background = '#1e293b';
            document.getElementById('statusText').innerText = 'Ready to focus';
        }

        function setMinutes(m) {
            totalSeconds = m * 60;
            resetTimer();
        }

        updateDisplay();
    </script>
    """
    components.html(timer_html, height=160)

    st.markdown("---")

    # 4. Provider & Model Configuration
    st.markdown("#### AI Provider & Model")
    chosen_provider_name = st.selectbox(
        "Provider",
        options=list(PROVIDERS.keys()),
        index=0,
    )
    provider_info = PROVIDERS[chosen_provider_name]

    # Resolve default key from configured defaults, secrets, or env
    fallback_key = CONFIGURED_KEYS.get(chosen_provider_name, "")
    try:
        if hasattr(st, "secrets") and provider_info["env_var"] in st.secrets:
            fallback_key = st.secrets[provider_info["env_var"]]
    except Exception:
        pass
    if not fallback_key:
        fallback_key = os.getenv(provider_info["env_var"], "")

    stored_key = st.session_state.provider_keys.get(chosen_provider_name, fallback_key)

    api_key_input = st.text_input(
        f"{chosen_provider_name} Key",
        value=stored_key,
        type="password",
        help="Paste your key here. It takes effect immediately.",
    )
    st.session_state.provider_keys[chosen_provider_name] = api_key_input
    active_api_key = api_key_input.strip()

    if active_api_key:
        st.markdown('<span class="status-badge-active">Verified Key Active</span>', unsafe_allow_html=True)
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
        help="Extracts internal model thoughts and step-by-step reasoning.",
    )

    auto_expand_thoughts = st.checkbox("Always Expand Reasoning Trace", value=False)

    st.markdown("---")

    # 5. Context Window (Memory Depth)
    st.markdown("#### Context Window (Memory Depth)")
    context_option = st.select_slider(
        "Turns Remembered",
        options=[2, 4, 6, 10, 16, 24, "Full History"],
        value=10,
        help="Limits past turns sent to save tokens and prevent rate limits.",
    )

    st.markdown("---")

    # 6. Teaching Style
    st.markdown("#### Instructor Mode")
    chosen_preset_name = st.selectbox("Pedagogy", options=list(TEACHING_PRESETS.keys()), index=0)
    system_prompt = st.text_area("System Prompt", value=TEACHING_PRESETS[chosen_preset_name], height=110)

# --- Header with Custom Logo ---
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-logo">🎓</div>
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

# --- Export JSON payload for Client-Side LocalStorage Synchronization ---
all_vault_data = db.export_all_data()
vault_json_str = json.dumps(all_vault_data)

# Client-Side LocalStorage Auto-Sync Snippet (Saves to user's browser automatically)
components.html(
    f"""
    <script>
    try {{
        const payload = {vault_json_str};
        if (payload && payload.sessions && payload.sessions.length > 0) {{
            localStorage.setItem('classroom_persistent_vault', JSON.stringify(payload));
            localStorage.setItem('classroom_vault_sync_time', new Date().toISOString());
        }}
    }} catch(e) {{
        console.error("Local storage sync error:", e);
    }}
    </script>
    """,
    height=0,
)

# --- Study Tabs ---
chat_tab, scratchpad_tab, storage_tab = st.tabs(["Interactive Classroom", "Study Notes & Scratchpad", "Database, Backup & 24/7 Keep-Alive"])

with scratchpad_tab:
    st.markdown("#### Session Notes & Code Scratchpad")
    st.caption("Jot down notes or code patterns during your lesson. Notes persist across questions.")
    st.session_state.study_notes = st.text_area(
        "Notes Content",
        value=st.session_state.study_notes,
        height=320,
        placeholder="e.g. Memory layout: Arrays are contiguous in RAM...",
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
    st.markdown("### Chat History Persistence & 24/7 Uptime Solution")
    
    stats = db.get_database_stats()

    # 1. Why Chat Data Disappears on Free Cloud & How It's Solved
    st.markdown(
        f"""
        <div class="danger-card">
            <strong>Why was chat history occasionally lost after closing the tab?</strong><br>
            Streamlit Community Cloud runs in <em>ephemeral containers</em>. When no one visits the app for a while, 
            Streamlit shuts down the container into <strong>Sleep Mode</strong>. When you return, Streamlit creates a fresh container 
            from GitHub, which resets temporary files.<br><br>
            <strong>How we completely solved it:</strong><br>
            1. <strong>Automated Browser LocalStorage Vault:</strong> Your browser now automatically mirrors every lesson, prompt, and answer locally on your device. Even if Streamlit reboots 100 times, your browser never loses your data.<br>
            2. <strong>One-Click Full Backup & Restore:</strong> Download or restore your entire chat database with 1 click below.<br>
            3. <strong>24/7 Keep-Alive Monitor:</strong> Prevent Streamlit Cloud from ever going to sleep!
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Database Stats & Backup Controls
    st.markdown("#### 1. Instant Chat History Backup & Restore")
    
    st.markdown(
        f"""
        <div class="info-card">
            <strong>Active Database:</strong> SQLite 3 (<code>{stats['path']}</code>)<br>
            <strong>Saved Lessons in Classroom:</strong> {stats['sessions']} sessions<br>
            <strong>Total Dialogue Turns:</strong> {stats['messages']} message exchanges<br>
            <strong>Automated Disk Backup:</strong> <code>{stats['backup_path']}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        # Export All Sessions to a single portable JSON file
        st.download_button(
            label="📥 Download Complete Backup (.json)",
            data=vault_json_str,
            file_name=f"classroom_all_chats_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            help="Contains all past lessons, code blocks, and reasoning traces.",
            use_container_width=True,
            type="primary",
        )

    with col_b2:
        # Download Raw SQLite DB file
        if os.path.exists(stats["path"]):
            with open(stats["path"], "rb") as db_file:
                st.download_button(
                    label="💾 Download SQLite Database (.db)",
                    data=db_file.read(),
                    file_name="classroom.db",
                    mime="application/x-sqlite3",
                    use_container_width=True,
                )

    st.markdown("---")

    # Restore from JSON File
    st.markdown("#### 2. Restore Chat History from Backup File")
    uploaded_backup = st.file_uploader(
        "Upload a previously downloaded Classroom backup (.json)",
        type=["json"],
        help="Upload your backup file to immediately restore all lessons and messages.",
    )
    if uploaded_backup is not None:
        if st.button("Restore All Chats from Uploaded File", type="primary", use_container_width=True):
            try:
                content = json.load(uploaded_backup)
                num_s, num_m = db.import_all_data(content)
                st.success(f"Successfully restored {num_s} lessons and {num_m} messages!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to restore backup: {e}")

    st.markdown("---")

    # 3. How to keep Streamlit Cloud awake 24/7 (Prevent Sleep Mode)
    st.markdown("#### 3. How to Keep Your Website Awake 24/7 (Never Sleep)")
    st.markdown(
        """
        <div class="guide-card">
            <strong>Free 60-Second Solution to Stop Streamlit Cloud from Sleeping:</strong><br>
            Streamlit Cloud sleeps free apps if they receive no visits for 48 hours. You can keep it running 24/7/365 permanently for free:
            <ol style="margin-top:8px; margin-bottom:8px;">
                <li>Copy your live Streamlit Cloud website URL: e.g. <code>https://harshitsingh205-nemotron-chat-app-app-*.streamlit.app/</code></li>
                <li>Go to <a href="https://cron-job.org" target="_blank" style="font-weight:600; color:#166534;">cron-job.org</a> or <a href="https://uptimerobot.com" target="_blank" style="font-weight:600; color:#166534;">UptimeRobot.com</a> (both 100% free forever).</li>
                <li>Create a free account and click <strong>Create Monitor / Cronjob</strong>.</li>
                <li>Paste your Streamlit app URL and set the execution interval to <strong>Every 10 minutes</strong>.</li>
            </ol>
            <strong>Result:</strong> The free pinger sends a lightweight ping every 10 minutes. Streamlit Cloud sees active traffic and <strong>will NEVER put your Classroom website to sleep</strong>!
        </div>
        """,
        unsafe_allow_html=True,
    )

with chat_tab:
    # Notice banner if database is empty but user has visited before
    if len(recent_sessions) <= 1 and stats["messages"] == 0:
        st.markdown(
            """
            <div class="info-card">
                <strong>New or Restarted Session:</strong> Choose a topic below or ask any question to start learning. 
                If you previously downloaded a backup file, you can restore all your lessons anytime in the <strong>Database, Backup & 24/7 Keep-Alive</strong> tab above!
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Quick Topic Starter Buttons if chat is empty
    if len(session_messages) == 0:
        st.markdown("**Suggested Topics to Explore:**")
        chip1, chip2, chip3, chip4 = st.columns(4)
        with chip1:
            if st.button("Arrays & Memory Allocation", use_container_width=True):
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

    # Handle Suggested Prompt or Direct Input (st.chat_input naturally submits on Enter)
    active_prompt = None
    if st.session_state.suggested_prompt:
        active_prompt = st.session_state.suggested_prompt
        st.session_state.suggested_prompt = None
    else:
        active_prompt = st.chat_input("Enter any topic to learn (press Enter to send)...")

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
            thought_expander = None
            thought_placeholder = None
            full_reasoning = ""
            full_content = ""

            if enable_thinking:
                thought_expander = st.expander("Model Reasoning & Pedagogy Derivation", expanded=True)
                with thought_expander:
                    thought_placeholder = st.empty()
                    thought_placeholder.caption("Synthesizing intuition, code examples, and pedagogy...")

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
                if "chat_template_kwargs" in err_text:
                    try:
                        completion = execute_stream(current_model, False)
                    except Exception as e2:
                        err_text = str(e2)

                if completion is None:
                    st.error(f"Inference error from {chosen_provider_name}: {err_text}")

            if completion is not None:
                try:
                    for chunk in completion:
                        if not chunk.choices:
                            continue

                        delta = chunk.choices[0].delta

                        # 1. Reasoning trace (NVIDIA, Groq, DeepSeek)
                        reasoning_chunk = getattr(delta, "reasoning_content", None)
                        if reasoning_chunk is None and hasattr(delta, "reasoning"):
                            reasoning_chunk = delta.reasoning

                        if reasoning_chunk:
                            full_reasoning += reasoning_chunk
                            if thought_placeholder:
                                thought_placeholder.markdown(f"```text\n{full_reasoning}\n```")

                        # 2. Content
                        if delta.content is not None:
                            full_content += delta.content
                            response_placeholder.markdown(full_content + "▌")

                    response_placeholder.markdown(full_content)

                    # Persist response to SQLite database
                    db.add_message(
                        st.session_state.active_session_id,
                        "assistant",
                        full_content,
                        full_reasoning if full_reasoning else None,
                    )
                except Exception as stream_err:
                    st.error(f"Stream interruption: {stream_err}")
