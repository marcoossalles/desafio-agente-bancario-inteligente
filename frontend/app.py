import streamlit as st

from api_client import BankingAPIError, stream_chat


st.set_page_config(
    page_title="Banco Ágil",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
        :root {
            --agil-purple: #820ad1;
            --agil-purple-dark: #4b006e;
            --agil-purple-soft: #ead7f7;
            --agil-surface: #ffffff;
            --agil-background: #f6f3f7;
            --agil-text: #211b24;
            --agil-muted: #706777;
        }

        .stApp {
            background:
                radial-gradient(circle at 50% -12rem, #d9a8f7 0, transparent 34rem),
                linear-gradient(180deg, #f3e8fa 0, var(--agil-background) 25rem);
            color: var(--agil-text);
        }

        header[data-testid="stHeader"],
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
        }

        .block-container {
            max-width: 980px;
            padding: 1.5rem 2rem 5.5rem;
        }

        .agil-welcome {
            margin: min(14vh, 7rem) auto 0;
            max-width: 720px;
            padding: 1rem;
            text-align: left;
        }

        .agil-welcome-label {
            color: var(--agil-purple);
            font-size: 0.85rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            margin-bottom: 0.9rem;
            text-transform: uppercase;
        }

        .agil-welcome h2 {
            color: var(--agil-purple-dark);
            font-size: clamp(2.3rem, 4vw, 3.6rem);
            font-weight: 650;
            letter-spacing: -0.055em;
            line-height: 1.06;
            margin: 0;
        }

        .agil-spark {
            color: var(--agil-purple);
            display: inline-block;
            font-size: 0.82em;
            margin-right: 0.2rem;
            transform: translateY(-0.04em);
        }

        [data-testid="stChatMessage"] {
            background: var(--agil-surface);
            border: 1px solid rgba(74, 43, 86, 0.08);
            border-radius: 20px 20px 20px 6px;
            box-shadow: 0 8px 28px rgba(45, 22, 54, 0.07);
            margin: 0 0 1rem;
            max-width: 82%;
            padding: 0.5rem 0.8rem;
        }

        [data-testid="stChatMessage"] p {
            font-size: 1rem;
            line-height: 1.55;
        }

        [data-testid="stChatMessage"]:has(
            [aria-label="Chat message from user"]
        ) {
            background: linear-gradient(135deg, #820ad1, #6710a1);
            border: none;
            border-radius: 20px 20px 6px 20px;
            color: white;
            margin-left: auto;
            max-width: 72%;
        }

        [data-testid="stChatMessage"]:has(
            [aria-label="Chat message from user"]
        ) p {
            color: white;
        }

        [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] {
            background: rgba(255, 255, 255, 0.2);
        }

        [data-testid="stChatInput"] {
            background: white;
            border: 1px solid rgba(130, 10, 209, 0.20);
            border-radius: 18px;
            box-shadow: 0 14px 45px rgba(61, 27, 75, 0.14);
            min-height: 58px;
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: var(--agil-purple);
            box-shadow: 0 14px 45px rgba(130, 10, 209, 0.18);
        }

        [data-testid="stBottom"] > div {
            background: linear-gradient(180deg, transparent, var(--agil-background) 55%);
            padding-bottom: 0.8rem;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] {
            margin-left: auto;
            margin-right: auto;
            max-width: 916px;
        }

        .st-key-test_data_action [data-testid="stPopoverButton"],
        .st-key-new_conversation_action .stButton button {
            align-items: center;
            background: var(--agil-purple) !important;
            border: 1px solid var(--agil-purple) !important;
            border-radius: 999px !important;
            box-shadow: 0 8px 22px rgba(130, 10, 209, 0.22) !important;
            box-sizing: border-box;
            color: white !important;
            display: flex;
            font-weight: 700;
            height: 42px;
            justify-content: center;
            padding: 0 1rem;
            width: 100%;
        }

        .st-key-test_data_action [data-testid="stPopoverButton"]:hover,
        .st-key-new_conversation_action .stButton button:hover {
            background: var(--agil-purple-dark) !important;
            border-color: var(--agil-purple-dark) !important;
            color: white !important;
            transform: translateY(-1px);
        }

        .st-key-test_data_action [data-testid="stPopoverButton"] p,
        .st-key-test_data_action [data-testid="stPopoverButton"] svg {
            color: white !important;
        }

        .st-key-test_data_action,
        .st-key-new_conversation_action {
            position: fixed;
            top: 1.5rem;
            width: 170px;
            z-index: 1000;
        }

        .st-key-test_data_action {
            left: 2rem;
        }

        .st-key-new_conversation_action {
            right: 2rem;
        }

        [data-testid="stPopoverBody"] {
            border: 1px solid rgba(130, 10, 209, 0.12);
            border-radius: 18px;
            box-shadow: 0 18px 55px rgba(60, 25, 74, 0.16);
            max-width: min(360px, calc(100vw - 2rem));
            min-width: 320px;
        }

        [data-testid="stAlert"] {
            border-radius: 16px;
        }

        @media (max-width: 700px) {
            .block-container {
                padding: 0.8rem 0.8rem 5rem;
            }

            .st-key-test_data_action,
            .st-key-new_conversation_action {
                top: 0.8rem;
                width: 138px;
            }

            .st-key-test_data_action {
                left: 0.8rem;
            }

            .st-key-new_conversation_action {
                right: 0.8rem;
            }

            .st-key-test_data_action [data-testid="stPopoverButton"],
            .st-key-new_conversation_action .stButton button {
                font-size: 0.78rem;
                height: 40px;
                padding: 0 0.65rem;
            }

            .agil-welcome {
                margin-top: 12vh;
                padding: 1rem 0.5rem;
            }

            .agil-welcome h2 {
                font-size: 2.15rem;
            }

            [data-testid="stChatMessage"] {
                max-width: 92%;
            }

            [data-testid="stChatMessage"]:has(
                [aria-label="Chat message from user"]
            ) {
                max-width: 86%;
            }
        }

    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("thread_id", None)
    st.session_state.setdefault("finished", False)
    st.session_state.setdefault("pending_prompt", None)


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.thread_id = None
    st.session_state.finished = False
    st.session_state.pending_prompt = None


initialize_session()

with st.container(key="test_data_action"):
    with st.popover("Dados de teste"):
        st.caption("Escolha um cliente fictício.")
        customer_tabs = st.tabs(["Cliente 1", "Cliente 2", "Cliente 3"])
        test_customers = (
            ("11111111111", "15/05/1990"),
            ("22222222222", "20/10/1985"),
            ("33333333333", "10/02/1998"),
        )

        for customer_tab, (cpf, birth_date) in zip(
            customer_tabs,
            test_customers,
            strict=True,
        ):
            with customer_tab:
                st.caption("CPF")
                st.code(cpf, language=None)
                st.caption("Nascimento")
                st.code(birth_date, language=None)

with st.container(key="new_conversation_action"):
    if st.button(
        "＋ Nova conversa",
        key="new_conversation",
        use_container_width=True,
    ):
        reset_conversation()
        st.rerun()

if not st.session_state.messages:
    st.markdown(
        """
        <section class="agil-welcome">
            <div class="agil-welcome-label">Boas-vindas ao Banco Ágil</div>
            <h2><span class="agil-spark">✦</span>Simples para você.<br>
            Ágil como deve ser.</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )

for saved_message in st.session_state.messages:
    avatar = "💜" if saved_message["role"] == "assistant" else "👤"
    with st.chat_message(saved_message["role"], avatar=avatar):
        st.markdown(saved_message["content"])

pending_prompt = st.session_state.pending_prompt

if pending_prompt:
    stream_result = {}

    try:
        with st.chat_message("assistant", avatar="💜"):
            with st.spinner("Lia está respondendo..."):
                response_text = st.write_stream(
                    stream_chat(
                        message=pending_prompt,
                        thread_id=st.session_state.thread_id,
                        result=stream_result,
                    )
                )

    except BankingAPIError as error:
        response_text = str(error)
        st.error(response_text)

    st.session_state.messages.append(
        {"role": "assistant", "content": response_text}
    )
    st.session_state.thread_id = stream_result.get(
        "thread_id",
        st.session_state.thread_id,
    )
    st.session_state.finished = stream_result.get("finished", False)
    st.session_state.pending_prompt = None
    st.rerun()

if st.session_state.messages and st.session_state.finished:
    st.success(
        "Este atendimento foi encerrado. Use “Nova conversa” "
        "para iniciar outra conversa."
    )

prompt = st.chat_input(
    "Como posso ajudar você hoje?",
    disabled=(
        st.session_state.finished
        or st.session_state.pending_prompt is not None
    ),
    key="conversation_prompt",
)

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    st.session_state.pending_prompt = prompt
    st.rerun()
