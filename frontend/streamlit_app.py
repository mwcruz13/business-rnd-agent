import streamlit as st

from components import FrontendApiError
from components import get_health
from components import get_run_state
from components import parse_edit_payload
from components import render_artifacts
from components import render_checkpoint_editor
from components import render_run_summary
from components import resume_run
from components import start_run


DEFAULT_EDITOR_KEY = "checkpoint_edit_payload"


def _init_session_state() -> None:
    st.session_state.setdefault("active_session_id", None)
    st.session_state.setdefault("run_state", None)


st.set_page_config(page_title="BMI Consultant App", layout="wide")
_init_session_state()

st.markdown(
    """
    <style>
    :root {
        --bmi-ink: #1f3127;
        --bmi-muted: #506258;
        --bmi-panel: rgba(255, 255, 255, 0.86);
        --bmi-panel-strong: #ffffff;
        --bmi-border: rgba(43, 59, 47, 0.14);
        --bmi-accent: #274032;
        --bmi-accent-soft: #d9eadf;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(188, 224, 208, 0.45), transparent 28%),
            radial-gradient(circle at top right, rgba(230, 196, 154, 0.32), transparent 24%),
            linear-gradient(180deg, #f6f2ea 0%, #eef3ef 55%, #f7f5f0 100%);
        color: var(--bmi-ink);
    }
    .stApp,
    .stApp p,
    .stApp li,
    .stApp label,
    .stApp span,
    .stApp div,
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4 {
        color: var(--bmi-ink);
    }
    .stCaption,
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp [data-testid="stMarkdownContainer"] small {
        color: var(--bmi-muted) !important;
    }
    .hero-card {
        padding: 1.25rem 1.4rem;
        border: 1px solid var(--bmi-border);
        border-radius: 18px;
        background: var(--bmi-panel);
        box-shadow: 0 10px 30px rgba(48, 68, 58, 0.08);
        backdrop-filter: blur(10px);
    }
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        background: var(--bmi-accent-soft);
        color: var(--bmi-accent);
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.35rem;
    }
    .stApp [data-testid="stMetric"] {
        background: var(--bmi-panel);
        border: 1px solid var(--bmi-border);
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
    }
    .stApp [data-testid="stMetricLabel"] *,
    .stApp [data-testid="stMetricValue"] * {
        color: var(--bmi-ink) !important;
    }
    .stApp [data-testid="stExpander"] {
        background: var(--bmi-panel);
        border: 1px solid var(--bmi-border);
        border-radius: 16px;
        overflow: hidden;
    }
    .stApp [data-testid="stExpander"] summary,
    .stApp [data-testid="stExpander"] summary * {
        color: var(--bmi-ink) !important;
        background: transparent !important;
    }
    .stApp [data-baseweb="input"],
    .stApp [data-baseweb="base-input"],
    .stApp [data-baseweb="select"],
    .stApp [data-baseweb="select"] > div,
    .stApp [data-baseweb="popover"],
    .stApp [role="listbox"],
    .stApp [role="option"],
    .stApp [data-testid="stTextArea"] textarea,
    .stApp [data-testid="stFileUploaderDropzone"],
    .stApp [data-testid="stSelectbox"] > div,
    .stApp [data-testid="stTextInput"] input {
        background: var(--bmi-panel-strong) !important;
        color: var(--bmi-ink) !important;
        border-color: var(--bmi-border) !important;
    }
    .stApp [data-testid="stFileUploaderDropzone"] * {
        color: var(--bmi-ink) !important;
    }
    .stApp textarea::placeholder,
    .stApp input::placeholder {
        color: #6b7d73 !important;
        opacity: 1;
    }
    .stApp [data-testid="stSelectbox"] label,
    .stApp [data-testid="stSelectbox"] div,
    .stApp [data-testid="stSelectbox"] span,
    .stApp [data-baseweb="select"] *,
    .stApp [role="listbox"] *,
    .stApp [role="option"] * {
        color: var(--bmi-ink) !important;
    }
    .stApp [data-testid="stRadio"] label,
    .stApp [data-testid="stCheckbox"] label,
    .stApp [data-testid="stToggle"] label {
        color: var(--bmi-ink) !important;
    }
    .stApp [data-testid="stRadio"] > div {
        background: var(--bmi-panel) !important;
        border: 1px solid var(--bmi-border);
        border-radius: 14px;
        padding: 0.5rem 0.75rem;
    }
    .stApp [data-testid="stRadio"] [role="radiogroup"] {
        background: transparent !important;
    }
    .stApp [data-testid="stRadio"] [role="radio"] {
        background: var(--bmi-panel-strong) !important;
        border: 1px solid var(--bmi-border) !important;
        border-radius: 999px !important;
        padding: 0.25rem 0.75rem !important;
        color: var(--bmi-ink) !important;
    }
    .stApp [data-testid="stRadio"] [role="radio"][aria-checked="true"] {
        background: var(--bmi-accent-soft) !important;
        border-color: rgba(39, 64, 50, 0.28) !important;
    }
    .stApp [data-testid="stRadio"] [role="radio"] * {
        color: var(--bmi-ink) !important;
    }
    .stApp .stButton > button,
    .stApp [data-testid="baseButton-secondary"],
    .stApp [data-testid="baseButton-primary"] {
        background: var(--bmi-panel-strong) !important;
        color: var(--bmi-ink) !important;
        border-radius: 12px;
        border: 1px solid var(--bmi-border);
        box-shadow: none !important;
    }
    .stApp .stButton > button:hover,
    .stApp [data-testid="baseButton-secondary"]:hover,
    .stApp [data-testid="baseButton-primary"]:hover {
        background: #f0f5f1 !important;
        color: var(--bmi-ink) !important;
        border-color: rgba(39, 64, 50, 0.24) !important;
    }
    .stApp .stButton > button[kind="primary"],
    .stApp button[data-testid="baseButton-primary"] {
        background: #e2eee5 !important;
        color: #1d2d24 !important;
        border-color: rgba(39, 64, 50, 0.24) !important;
    }
    .stApp .stButton > button p,
    .stApp .stButton > button span,
    .stApp .stButton > button div,
    .stApp [data-testid="baseButton-secondary"] *,
    .stApp [data-testid="baseButton-primary"] * {
        color: inherit !important;
    }
    .stApp [data-testid="stCodeBlock"],
    .stApp [data-testid="stCodeBlock"] pre,
    .stApp [data-testid="stCodeBlock"] code,
    .stApp [data-testid="stJson"],
    .stApp [data-testid="stJson"] pre,
    .stApp [data-testid="stJson"] code,
    .stApp [data-testid="stJson"] div,
    .stApp [data-testid="stJson"] span,
    .stApp pre,
    .stApp code {
        background: var(--bmi-panel-strong) !important;
        color: var(--bmi-ink) !important;
        border-color: var(--bmi-border) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <h1 style="margin-bottom:0.25rem;">BMI Consultant App</h1>
        <p style="margin-bottom:0.35rem; color:#4d5e54;">Human-in-the-loop execution for the 8-step BMI workflow with backend-managed checkpoints.</p>
        <span class="status-pill">Streamlit client over FastAPI workflow runtime</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

health_col, refresh_col = st.columns([5, 1])
with health_col:
    try:
        health = get_health()
        st.success(f"Backend reachable: {health}")
    except FrontendApiError as error:
        st.error(f"Backend API error: {error}")
    except Exception as exc:
        st.warning(f"Backend not reachable yet: {exc}")
with refresh_col:
    if st.button("Refresh", use_container_width=True):
        session_id = st.session_state.get("active_session_id")
        if session_id:
            try:
                st.session_state["run_state"] = get_run_state(session_id)
            except FrontendApiError as error:
                st.error(str(error))

left_col, right_col = st.columns([1.1, 1.2], gap="large")

with left_col:
    st.subheader("Start Workflow")
    input_mode = st.radio("Input source", options=["Upload file", "Paste text"], horizontal=True)
    llm_backend = st.selectbox("LLM backend", options=["azure", "ollama"], index=0)
    pause_at_checkpoints = st.toggle("Pause at mandatory checkpoints", value=True)
    uploaded = None
    pasted_text = ""

    if input_mode == "Upload file":
        uploaded = st.file_uploader("Upload a text or CSV input", type=["txt", "csv"])
        if uploaded is not None:
            st.caption(f"Selected: {uploaded.name} ({uploaded.size} bytes)")
    else:
        pasted_text = st.text_area(
            "Paste Voice of Customer input",
            height=180,
            placeholder="Paste VoC notes, interview synthesis, customer comments, or CJM text here.",
        )

    if st.button("Run Workflow", type="primary", use_container_width=True):
        try:
            if input_mode == "Paste text":
                run_state = start_run(
                    input_text=pasted_text,
                    input_format="text",
                    llm_backend=llm_backend,
                    pause_at_checkpoints=pause_at_checkpoints,
                )
            else:
                if uploaded is None:
                    raise ValueError("Upload a .txt or .csv file before starting the workflow")

                decoded = uploaded.getvalue().decode("utf-8")
                run_state = start_run(
                    input_text=decoded,
                    input_format="csv" if uploaded.name.lower().endswith(".csv") else "text",
                    llm_backend=llm_backend,
                    pause_at_checkpoints=pause_at_checkpoints,
                )

            st.session_state["active_session_id"] = run_state.get("session_id")
            st.session_state["run_state"] = run_state
            st.success("Workflow started")
        except (FrontendApiError, ValueError, UnicodeDecodeError) as error:
            st.error(str(error))

    if st.session_state.get("active_session_id"):
        st.caption(f"Active session: {st.session_state['active_session_id']}")
        if st.button("Reload Session State", use_container_width=True):
            try:
                st.session_state["run_state"] = get_run_state(st.session_state["active_session_id"])
            except FrontendApiError as error:
                st.error(str(error))

with right_col:
    st.subheader("Workflow State")
    run_state = st.session_state.get("run_state")
    if not run_state:
        st.info("No workflow session loaded yet.")
    else:
        render_run_summary(run_state)
        render_artifacts(run_state)

        if run_state.get("run_status") == "paused" and run_state.get("pending_checkpoint"):
            st.write("")
            render_checkpoint_editor(run_state, editor_key=DEFAULT_EDITOR_KEY)
            action_cols = st.columns(3)

            if action_cols[0].button("Approve", use_container_width=True):
                try:
                    updated_state = resume_run(run_state["session_id"], decision="approve")
                    st.session_state["run_state"] = updated_state
                    st.success("Checkpoint approved")
                    st.rerun()
                except FrontendApiError as error:
                    st.error(str(error))

            if action_cols[1].button("Edit", use_container_width=True):
                try:
                    edit_state = parse_edit_payload(st.session_state[DEFAULT_EDITOR_KEY])
                    updated_state = resume_run(run_state["session_id"], decision="edit", edit_state=edit_state)
                    st.session_state["run_state"] = updated_state
                    st.success("Checkpoint edited and resumed")
                    st.rerun()
                except (FrontendApiError, ValueError) as error:
                    st.error(str(error))

            if action_cols[2].button("Retry", use_container_width=True):
                try:
                    updated_state = resume_run(run_state["session_id"], decision="retry")
                    st.session_state["run_state"] = updated_state
                    st.success("Checkpoint step retried")
                    st.rerun()
                except FrontendApiError as error:
                    st.error(str(error))
        elif run_state.get("run_status") == "completed":
            st.success("Workflow completed. Final experiment artifacts are available above.")
