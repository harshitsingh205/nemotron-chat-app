import os
import streamlit as st
from openai import OpenAI

# --- Page Configuration ---
st.set_page_config(
    page_title="Nemotron Reasoning Chat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling ---
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #718096;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .thought-container {
        border-left: 3px solid #6366f1;
        padding-left: 12px;
        color: #4b5563;
        font-family: monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar: Configuration ---
with st.sidebar:
    st.title("⚙️ Model Controls")

    # API Key Handling
    env_key = os.getenv("NVIDIA_API_KEY", "")
    api_key = st.text_input(
        "NVIDIA API Key",
        value=env_key,
        type="password",
        help="Get your key at build.nvidia.com. Can also be set as NVIDIA_API_KEY environment variable.",
    )

    st.divider()

    # Model & Template Selection
    model = st.selectbox(
        "Model",
        options=[
            "nvidia/nemotron-3-ultra-550b-a55b",
            "deepseek-ai/deepseek-r1",
            "meta/llama-3.3-70b-instruct",
        ],
        index=0,
    )

    enable_thinking = st.toggle(
        "Enable Thinking / Reasoning",
        value=True,
        help="Enables chain-of-thought extraction via chat_template_kwargs.",
    )

    auto_expand_thoughts = st.checkbox(
        "Auto-expand reasoning accordion",
        value=False,
        help="Keep past thought accordions open by default.",
    )

    st.divider()

    # Hyperparameters
    st.subheader("Hyperparameters")
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.5,
        value=1.0 if enable_thinking else 0.7,
        step=0.05,
        help="Higher values make output more random, lower values more deterministic. Reasoning models often perform best around 1.0.",
    )

    top_p = st.slider(
        "Top-P",
        min_value=0.01,
        max_value=1.0,
        value=0.95,
        step=0.01,
    )

    max_tokens = st.slider(
        "Max Tokens",
        min_value=512,
        max_value=16384,
        value=4096,
        step=512,
    )

    st.divider()

    # System Prompt
    system_prompt = st.text_area(
        "System Prompt",
        value="You are a helpful, deep-thinking AI assistant powered by NVIDIA Nemotron. Provide clear, well-structured, and rigorous answers.",
        rows=4,
    )

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Header ---
st.markdown('<div class="main-title">🧠 Nemotron Reasoning Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Explore step-by-step reasoning traces & deep thoughts powered by NVIDIA NIM API</div>', unsafe_allow_html=True)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Render Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Show reasoning accordion if present
        if msg.get("reasoning"):
            with st.expander("🧠 Thought Process / Reasoning", expanded=auto_expand_thoughts):
                st.markdown(f"```text\n{msg['reasoning']}\n```")
        st.markdown(msg["content"])

# --- User Input & Response Generation ---
user_query = st.chat_input("Ask a question, request code, or pose a complex logic puzzle...")

if user_query:
    if not api_key:
        st.error("⚠️ Please enter your NVIDIA API Key in the sidebar or set the `NVIDIA_API_KEY` environment variable.")
        st.stop()

    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Initialize client
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    # Prepare API messages
    api_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant"):
        thought_container = None
        thought_placeholder = None
        full_reasoning = ""
        full_content = ""

        # Setup streaming placeholders
        if enable_thinking:
            thought_status = st.status("🧠 Deep thinking in progress...", expanded=True)
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

                # 1. Capture Reasoning Content
                reasoning_chunk = getattr(delta, "reasoning_content", None)
                if reasoning_chunk:
                    full_reasoning += reasoning_chunk
                    if thought_placeholder:
                        thought_placeholder.markdown(f"```text\n{full_reasoning}\n```")

                # 2. Capture Content
                if delta.content is not None:
                    # Once output starts generating, update thinking status
                    if enable_thinking and full_reasoning and thought_status:
                        thought_status.update(
                            label="💡 Thought process complete",
                            state="complete",
                            expanded=auto_expand_thoughts,
                        )
                    full_content += delta.content
                    response_placeholder.markdown(full_content + "▌")

            # Finalize output render without cursor
            response_placeholder.markdown(full_content)

            # In case reasoning completed without content update
            if enable_thinking and thought_status:
                thought_status.update(
                    label="💡 Thought process complete" if full_reasoning else "No explicit reasoning trace returned",
                    state="complete",
                    expanded=auto_expand_thoughts,
                )

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_content,
                "reasoning": full_reasoning if full_reasoning else None,
            })

        except Exception as e:
            st.error(f"Error calling NVIDIA API: {e}")
