
import streamlit as st


def apply_theme():

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #26334a;
        --muted: #66758b;
        --line: #dce5ef;
        --surface: rgba(255,255,255,.78);
        --accent: #6878d6;
        --accent-dark: #5364c2;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        color: var(--ink);
        background:
            radial-gradient(
                ellipse at 8% 4%,
                rgba(185,196,255,.55),
                transparent 35%
            ),
            radial-gradient(
                ellipse at 92% 8%,
                rgba(174,232,229,.55),
                transparent 34%
            ),
            linear-gradient(
                135deg,
                #f4f7fc 0%,
                #edf3f8 48%,
                #f8f7fc 100%
            );
        background-attachment: fixed;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 1.7rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: #26334a !important;
        letter-spacing: -.45px;
    }

    p, label, .stMarkdown,
    [data-testid="stCaptionContainer"] {
        color: #526178;
    }

    .hero {
        padding: 34px 38px;
        border-radius: 24px;
        margin-bottom: 30px;
        background: linear-gradient(
            115deg,
            rgba(255,255,255,.82),
            rgba(226,235,255,.84) 48%,
            rgba(220,246,242,.86)
        );
        border: 1px solid rgba(255,255,255,.9);
        box-shadow: 0 18px 50px rgba(72,91,130,.12);
        backdrop-filter: blur(18px);
    }

    .hero h1 {
        font-size: 44px;
        margin: 8px 0;
        color: #283653 !important;
    }

    .hero p {
        color: #61718b;
        font-size: 16px;
        max-width: 700px;
        margin-bottom: 0;
    }

    .hero-tag {
        color: #6878c9;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2px;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border: 1px solid #c7d0f5;
        border-radius: 11px;
        background: linear-gradient(
            110deg,
            #7887df,
            #70a9c8
        );
        color: white;
        font-weight: 650;
        min-height: 2.65rem;
        box-shadow: 0 5px 14px rgba(104,120,214,.16);
        transition: .18s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #8fa0e8;
        color: white;
        transform: translateY(-1px);
        background: linear-gradient(
            110deg,
            #6878d6,
            #5c9fbd
        );
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.72);
        border: 1px solid #e0e7f0;
        border-radius: 15px;
        padding: 15px 17px;
        box-shadow: 0 5px 18px rgba(70,88,120,.05);
    }

    div[data-testid="stMetricValue"] {
        color: #596bc7;
    }

    div[data-testid="stMetricLabel"] {
        color: #748198;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] textarea {
        background: rgba(255,255,255,.9) !important;
        color: #26334a !important;
        border: 1px solid #d7e0eb !important;
        border-radius: 10px !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dce5ef;
        border-radius: 13px;
        overflow: hidden;
        background: rgba(255,255,255,.86);
    }

    div[data-testid="stAlert"] {
        border-radius: 13px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,.55);
        border-color: #e0e7f0 !important;
        border-radius: 16px;
    }

    .empty-state {
        margin-top: 32px;
        padding: 52px 24px;
        text-align: center;
        background: rgba(255,255,255,.62);
        border: 1px dashed #cbd7e6;
        border-radius: 20px;
        backdrop-filter: blur(12px);
    }

    .footer {
        text-align: center;
        font-size: 10px;
        letter-spacing: 2px;
        color: #8a97aa;
        padding: 20px;
    }

    hr {
        border-color: #e0e7f0;
    }
    </style>
    """, unsafe_allow_html=True)
