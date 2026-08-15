import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.loop import run_daily_check, ask_agent
from tools.sheets import format_sheet_for_llm, get_unique_companies

# --- Page config ---
st.set_page_config(
    page_title="Networking Agent",
    page_icon="🤝",
    layout="wide"
)

# --- Minimal styling ---
st.markdown("""
<style>
    .block-container { max-width: 800px; }
    h1 { font-size: 1.8rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("Networking Agent")
st.caption("Reads your Google Sheet. Tells you who to DM, follow up with, and who can refer you.")

# --- Session state ---
if "daily_report" not in st.session_state:
    st.session_state.daily_report = None
if "sheet_data" not in st.session_state:
    st.session_state.sheet_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Daily check ---
col1, col2 = st.columns([1, 3])
with col1:
    run_check = st.button("Run daily check", type="primary", use_container_width=True)
with col2:
    st.caption("Pulls your sheet, analyzes all contacts, gives you today's action items.")

if run_check:
    with st.spinner("Reading your Google Sheet and analyzing contacts..."):
        try:
            st.session_state.sheet_data = format_sheet_for_llm()
            st.session_state.daily_report = run_daily_check()
            st.session_state.chat_history = []  # Reset chat on new check
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")

# --- Show report ---
if st.session_state.daily_report:
    st.markdown("---")
    st.markdown(st.session_state.daily_report)

    # --- Show company list for reference ---
    with st.expander("All companies in your sheet"):
        try:
            companies = get_unique_companies()
            st.write(", ".join(companies))
        except Exception:
            st.write("Could not load companies.")

    # --- Follow-up chat ---
    st.markdown("---")
    st.subheader("Ask a follow-up")
    st.caption("e.g. 'Who at Merck should I prioritize?' or 'Draft a follow-up message for the BMS people'")

    # Show chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if question := st.chat_input("Ask about your network..."):
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = ask_agent(question, st.session_state.sheet_data)
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})