import os
import gradio as gr
from openai import OpenAI

def stream_chat(
    user_message,
    history,
    api_key,
    model,
    enable_thinking,
    temperature,
    top_p,
    max_tokens,
    system_prompt,
):
    if not api_key:
        api_key = os.getenv("NVIDIA_API_KEY", "")
        if not api_key:
            yield "", "⚠️ Please provide your NVIDIA API Key.", history
            return

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
    )

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        messages.append({"role": "user", "content": turn[0]})
        messages.append({"role": "assistant", "content": turn[1]})
    messages.append({"role": "user", "content": user_message})

    extra_body = {}
    if enable_thinking:
        extra_body["chat_template_kwargs"] = {"enable_thinking": True}

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            extra_body=extra_body if extra_body else None,
            stream=True,
        )

        full_reasoning = ""
        full_content = ""

        for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                full_reasoning += reasoning
                yield full_reasoning, full_content, history

            if delta.content is not None:
                full_content += delta.content
                yield full_reasoning, full_content, history

        # Add to history
        new_history = history + [(user_message, full_content)]
        yield full_reasoning, full_content, new_history

    except Exception as e:
        yield "", f"Error: {e}", history

with gr.Blocks(title="Nemotron Reasoning Chat") as demo:
    gr.Markdown("# 🧠 Nemotron Reasoning Chat\nExplore live thought traces & step-by-step reasoning via NVIDIA NIM.")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversation History", height=450)
            with gr.Accordion("🧠 Thought Process / Step-by-Step Reasoning", open=True):
                reasoning_output = gr.Markdown("*(Internal model thinking will stream here during generation)*")
            msg_input = gr.Textbox(label="Your Prompt", placeholder="Ask a question or enter a logic problem...", lines=2)
            with gr.Row():
                submit_btn = gr.Button("Submit", variant="primary")
                clear_btn = gr.Button("Clear Chat")

        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Controls")
            api_key_input = gr.Textbox(
                label="NVIDIA API Key",
                type="password",
                value=os.getenv("NVIDIA_API_KEY", ""),
                placeholder="nvapi-...",
            )
            model_input = gr.Dropdown(
                label="Model",
                choices=[
                    "nvidia/nemotron-3-ultra-550b-a55b",
                    "deepseek-ai/deepseek-r1",
                    "meta/llama-3.3-70b-instruct",
                ],
                value="nvidia/nemotron-3-ultra-550b-a55b",
            )
            enable_thinking_box = gr.Checkbox(label="Enable Thinking / Reasoning", value=True)
            temp_slider = gr.Slider(0.0, 1.5, value=1.0, step=0.05, label="Temperature")
            top_p_slider = gr.Slider(0.01, 1.0, value=0.95, step=0.01, label="Top-P")
            max_tokens_slider = gr.Slider(256, 16384, value=4096, step=256, label="Max Tokens")
            system_prompt_input = gr.Textbox(
                label="System Prompt",
                value="You are a helpful, deep-thinking AI assistant. Provide clear, well-structured reasoning.",
                lines=3,
            )

    def respond(msg, hist, key, mod, think, temp, top_p_val, max_tok, sys_p):
        for r, c, h in stream_chat(msg, hist, key, mod, think, temp, top_p_val, max_tok, sys_p):
            yield r, h

    submit_btn.click(
        respond,
        inputs=[
            msg_input,
            chatbot,
            api_key_input,
            model_input,
            enable_thinking_box,
            temp_slider,
            top_p_slider,
            max_tokens_slider,
            system_prompt_input,
        ],
        outputs=[reasoning_output, chatbot],
    ).then(lambda: "", None, msg_input)

    clear_btn.click(lambda: ([], ""), None, [chatbot, reasoning_output])

if __name__ == "__main__":
    demo.launch()
