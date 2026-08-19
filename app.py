"""
==============================================================================
Lucile Sport — AI Auto Parts Sales Chatbot (Main Entry Point)
==============================================================================
Gradio web interface runner for Lucile Sport AI sales representative.
Run with:
    python app.py
==============================================================================
"""

from core.frontend_ui import create_app

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
