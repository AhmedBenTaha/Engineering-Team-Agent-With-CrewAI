"""Import and construct the Gradio app without launching a server."""

import gradio as gr

from app import demo

assert isinstance(demo, gr.Blocks)
print("Gradio app constructed successfully; launch was not called.")
