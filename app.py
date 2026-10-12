"""Streamlit Entrypoint Alias: runs streamlit_app.py seamlessly."""
import os
import runpy

if __name__ == "__main__" or "__file__" in globals():
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streamlit_app.py")
    runpy.run_path(target, run_name="__main__")
