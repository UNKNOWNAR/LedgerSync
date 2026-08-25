"""
Streamlit UI for the Transaction Reconciliation Tool.

Features
--------
- Upload widgets for both CSVs
- Threshold sliders (date gap, amount variance %, merchant similarity)
- LLM toggle
- "Run Reconciliation" button
- Metric cards: match rate, counts
- Exception table with LLM reasoning
- Partial match table with discrepancy notes + approve/reject toggles
- Download buttons for all reports
"""

from __future__ import annotations

import io
import json
import logging
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from reconciler.models import MatchResult, MatchStatus, ReconciliationConfig
from reconciler.pipeline import run_pipeline
from reconciler.reporting import generate_summary_metrics, write_all_reports

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Transaction Reconciliation Tool",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --bg-primary: #09090b;
        --bg-elevated: rgba(255,255,255,0.04);
        --bg-card: rgba(255,255,255,0.06);
        --bg-card-hover: rgba(255,255,255,0.09);
        --border-subtle: rgba(255,255,255,0.08);
        --border-hover: rgba(255,255,255,0.14);
        --text-primary: #fafafa;
        --text-secondary: rgba(255,255,255,0.6);
        --text-tertiary: rgba(255,255,255,0.35);
        --accent: #818cf8;
        --accent-bright: #a78bfa;
        --accent-glow: rgba(129,140,248,0.15);
        --accent-glow-strong: rgba(129,140,248,0.3);
        --green: #34d399;
        --green-bg: rgba(52,211,153,0.12);
        --green-border: rgba(52,211,153,0.25);
        --amber: #fbbf24;
        --amber-bg: rgba(251,191,36,0.12);
        --amber-border: rgba(251,191,36,0.25);
        --red: #f87171;
        --red-bg: rgba(248,113,113,0.12);
        --red-border: rgba(248,113,113,0.25);
        --blue: #60a5fa;
        --blue-bg: rgba(96,165,250,0.12);
        --blue-border: rgba(96,165,250,0.25);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --shadow-card: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
        --shadow-card-hover: 0 8px 30px rgba(0,0,0,0.4), 0 0 40px var(--accent-glow);
        --transition-fast: 0.18s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        --transition-smooth: 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        --transition-spring: 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* ── Animated background ──────────────────────────────── */
    .stApp {
        background: var(--bg-primary);
        min-height: 100vh;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background:
            radial-gradient(ellipse 600px 400px at 20% 20%, rgba(99,102,241,0.08), transparent),
            radial-gradient(ellipse 500px 350px at 80% 80%, rgba(139,92,246,0.06), transparent),
            radial-gradient(ellipse 400px 300px at 50% 50%, rgba(56,189,248,0.04), transparent);
        animation: bgDrift 20s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes bgDrift {
        0%   { transform: translate(0, 0) rotate(0deg); }
        33%  { transform: translate(2%, -1%) rotate(1deg); }
        66%  { transform: translate(-1%, 2%) rotate(-0.5deg); }
        100% { transform: translate(1%, -2%) rotate(0.5deg); }
    }

    /* ── Entrance animations ──────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.96); }
        to   { opacity: 1; transform: scale(1); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-12px); }
        to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 8px var(--accent-glow); }
        50%      { box-shadow: 0 0 20px var(--accent-glow-strong); }
    }
    @keyframes borderGlow {
        0%, 100% { border-color: var(--border-subtle); }
        50%      { border-color: var(--border-hover); }
    }
    @keyframes countUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ── Sidebar ──────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: rgba(9,9,11,0.85) !important;
        backdrop-filter: blur(24px) saturate(1.2);
        -webkit-backdrop-filter: blur(24px) saturate(1.2);
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        animation: slideInLeft var(--transition-smooth) ease both;
    }

    /* ── Hero header ─────────────────────────────────────── */
    .hero-container {
        text-align: center;
        padding: 3rem 0 2rem 0;
        animation: fadeInUp 0.6s ease both;
        position: relative;
    }
    .hero-container::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 120px;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
    }
    .hero-icon {
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        animation: fadeIn 0.8s ease both;
        filter: drop-shadow(0 0 12px var(--accent-glow-strong));
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #e0e7ff 0%, #818cf8 40%, #a78bfa 60%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.4rem 0;
        line-height: 1.15;
    }
    .hero-sub {
        color: var(--text-tertiary);
        font-size: 0.88rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        margin: 0;
    }

    /* ── Metric cards ─────────────────────────────────────── */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.3rem 1rem;
        text-align: center;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition:
            transform var(--transition-spring),
            box-shadow var(--transition-smooth),
            border-color var(--transition-smooth),
            background var(--transition-smooth);
        animation: fadeInUp 0.5s ease both;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, var(--accent) 50%, transparent 100%);
        opacity: 0;
        transition: opacity var(--transition-smooth);
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-card-hover);
        border-color: var(--border-hover);
        background: var(--bg-card-hover);
    }
    .metric-card:hover::before {
        opacity: 1;
    }
    .mc-delay-1 { animation-delay: 0.05s; }
    .mc-delay-2 { animation-delay: 0.10s; }
    .mc-delay-3 { animation-delay: 0.15s; }
    .mc-delay-4 { animation-delay: 0.20s; }
    .mc-delay-5 { animation-delay: 0.25s; }
    .mc-delay-6 { animation-delay: 0.30s; }

    .metric-card .mc-icon {
        font-size: 1.4rem;
        margin-bottom: 0.3rem;
        display: block;
        opacity: 0.7;
    }
    .metric-card .mc-label {
        color: var(--text-tertiary);
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }
    .metric-card .mc-value {
        color: var(--text-primary);
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.02em;
        animation: countUp 0.4s ease both;
    }
    .metric-card .mc-sub {
        color: var(--text-tertiary);
        font-size: 0.68rem;
        font-weight: 400;
        margin-top: 0.4rem;
        letter-spacing: 0.01em;
    }

    /* ── Section headers ──────────────────────────────────── */
    .section-header {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding-bottom: 0.6rem;
        margin: 2rem 0 1rem 0;
        border-bottom: 1px solid var(--border-subtle);
        animation: fadeInUp 0.4s ease both;
        position: relative;
    }
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 40px;
        height: 1px;
        background: var(--accent);
    }

    /* ── Status badges ────────────────────────────────────── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3em;
        padding: 0.25em 0.7em;
        border-radius: 99px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        transition: transform var(--transition-fast), box-shadow var(--transition-fast);
    }
    .badge:hover { transform: scale(1.05); }
    .badge-exact {
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid var(--green-border);
    }
    .badge-fuzzy {
        background: var(--blue-bg);
        color: var(--blue);
        border: 1px solid var(--blue-border);
    }
    .badge-partial {
        background: var(--amber-bg);
        color: var(--amber);
        border: 1px solid var(--amber-border);
    }
    .badge-exception {
        background: var(--red-bg);
        color: var(--red);
        border: 1px solid var(--red-border);
    }

    /* ── Buttons ───────────────────────────────────────────── */
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.65rem 2rem;
        font-weight: 600;
        font-size: 0.92rem;
        letter-spacing: 0.01em;
        transition:
            transform var(--transition-spring),
            box-shadow var(--transition-smooth),
            filter var(--transition-smooth);
        box-shadow: 0 4px 16px rgba(99,102,241,0.3), 0 1px 3px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    div[data-testid="stButton"] > button::after {
        content: '';
        position: absolute;
        top: 0; left: -100%; right: 0; bottom: 0;
        width: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        transition: left 0.5s ease;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 8px 28px rgba(99,102,241,0.4), 0 0 40px rgba(99,102,241,0.15);
        filter: brightness(1.05);
    }
    div[data-testid="stButton"] > button:hover::after {
        left: 100%;
    }
    div[data-testid="stButton"] > button:active {
        transform: translateY(0) scale(0.99);
        box-shadow: 0 2px 8px rgba(99,102,241,0.3);
    }

    /* ── Download buttons ─────────────────────────────────── */
    div[data-testid="stDownloadButton"] > button {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition:
            transform var(--transition-spring),
            box-shadow var(--transition-smooth),
            border-color var(--transition-smooth),
            background var(--transition-smooth) !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        transform: translateY(-2px) !important;
        background: var(--bg-card-hover) !important;
        border-color: var(--accent) !important;
        box-shadow: 0 4px 16px var(--accent-glow) !important;
    }
    div[data-testid="stDownloadButton"] > button:active {
        transform: translateY(0) scale(0.98) !important;
    }

    /* ── Dataframe ─────────────────────────────────────────── */
    .stDataFrame {
        border-radius: var(--radius-md);
        overflow: hidden;
        animation: scaleIn 0.4s ease both;
        border: 1px solid var(--border-subtle);
    }

    /* ── Upload area ───────────────────────────────────────── */
    [data-testid="stFileUploadDropzone"] {
        border: 1.5px dashed rgba(129,140,248,0.3) !important;
        border-radius: var(--radius-md) !important;
        background: rgba(129,140,248,0.03) !important;
        transition: all var(--transition-smooth) !important;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: rgba(129,140,248,0.5) !important;
        background: rgba(129,140,248,0.06) !important;
        box-shadow: 0 0 20px rgba(129,140,248,0.08) !important;
    }

    /* ── Upload card ───────────────────────────────────────── */
    .upload-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.4rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: border-color var(--transition-smooth), box-shadow var(--transition-smooth);
        animation: fadeInUp 0.5s ease both;
    }
    .upload-card:hover {
        border-color: var(--border-hover);
        box-shadow: var(--shadow-card);
    }
    .upload-card-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.1rem;
    }
    .upload-card-sub {
        font-size: 0.72rem;
        color: var(--text-tertiary);
    }

    /* ── Tabs ──────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: var(--bg-elevated);
        border-radius: var(--radius-md);
        padding: 3px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.82rem;
        padding: 0.5rem 1rem;
        transition: all var(--transition-fast);
    }
    .stTabs [aria-selected="true"] {
        background: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ── Expander ──────────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md) !important;
        transition: border-color var(--transition-smooth), box-shadow var(--transition-smooth);
        animation: fadeInUp 0.4s ease both;
        margin-bottom: 0.5rem;
    }
    [data-testid="stExpander"]:hover {
        border-color: var(--border-hover);
        box-shadow: var(--shadow-card);
    }
    [data-testid="stExpander"] summary {
        font-weight: 500;
        font-size: 0.88rem;
    }

    /* ── LLM reasoning callout ─────────────────────────────── */
    .llm-callout {
        background: linear-gradient(135deg, rgba(129,140,248,0.08), rgba(167,139,250,0.06));
        border-left: 3px solid var(--accent);
        padding: 0.85rem 1.1rem;
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        margin-top: 0.75rem;
        animation: fadeIn 0.3s ease both;
        font-size: 0.88rem;
        line-height: 1.55;
        color: var(--text-secondary);
    }
    .llm-callout strong {
        color: var(--accent-bright);
    }

    /* ── Approval badges ───────────────────────────────────── */
    .approval-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35em;
        padding: 0.35em 0.85em;
        border-radius: 99px;
        font-size: 0.82rem;
        font-weight: 600;
        animation: scaleIn var(--transition-spring) ease both;
    }
    .approval-approved {
        background: var(--green-bg);
        color: var(--green);
        border: 1px solid var(--green-border);
    }
    .approval-rejected {
        background: var(--red-bg);
        color: var(--red);
        border: 1px solid var(--red-border);
    }

    /* ── Empty state ───────────────────────────────────────── */
    .empty-state {
        text-align: center;
        padding: 5rem 2rem;
        animation: fadeInUp 0.6s ease both;
    }
    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        display: inline-block;
        opacity: 0.3;
        animation: borderGlow 3s ease-in-out infinite;
        filter: drop-shadow(0 0 8px var(--accent-glow));
    }
    .empty-state-text {
        color: var(--text-tertiary);
        font-size: 0.92rem;
        font-weight: 400;
        line-height: 1.6;
    }
    .empty-state-text strong {
        color: var(--text-secondary);
        font-weight: 600;
    }

    /* ── Divider ───────────────────────────────────────────── */
    .gradient-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-subtle), transparent);
        margin: 1.5rem 0;
        border: none;
    }

    /* ── Spinner ───────────────────────────────────────────── */
    .stSpinner > div { border-top-color: var(--accent) !important; }

    /* ── Slider ────────────────────────────────────────────── */
    [data-testid="stSlider"] .st-bx { background: var(--accent) !important; }

    /* ── Toggle ────────────────────────────────────────────── */
    .stCheckbox { color: var(--text-secondary); }

    /* ── Typography ────────────────────────────────────────── */
    h1 { color: var(--text-primary); }
    h2 {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: -0.01em;
    }
    h3 {
        color: var(--text-primary);
        font-size: 0.92rem;
        font-weight: 600;
    }
    /* Scope text styling to markdown blocks to avoid breaking Streamlit widgets */
    .stMarkdown p, .stMarkdown li {
        color: var(--text-secondary);
        font-size: 0.88rem;
    }
    .stMarkdown { color: var(--text-secondary); }

    /* ── Sidebar section labels ─────────────────────────────── */
    .sidebar-section {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.2rem 0 0.3rem 0;
    }
    .sidebar-section-line {
        flex: 1;
        height: 1px;
        background: var(--border-subtle);
    }

    /* ── Success / info banner ──────────────────────────────── */
    .stSuccess, .stInfo {
        border-radius: var(--radius-md) !important;
        animation: scaleIn 0.3s ease both;
    }

    /* ── Record comparison card ─────────────────────────────── */
    .record-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1rem;
        font-size: 0.82rem;
    }
    .record-card-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.6rem;
    }
    .record-row {
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .record-row:last-child { border-bottom: none; }
    .record-key {
        color: var(--text-tertiary);
        font-weight: 500;
        font-size: 0.78rem;
    }
    .record-val {
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.78rem;
        font-variant-numeric: tabular-nums;
    }

    /* ── Confidence meter ───────────────────────────────────── */
    .confidence-meter {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    .confidence-bar {
        width: 48px;
        height: 4px;
        background: var(--bg-elevated);
        border-radius: 99px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.6s ease;
    }

    /* ── Version tag ────────────────────────────────────────── */
    .version-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.2rem 0.55rem;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: 99px;
        font-size: 0.65rem;
        color: var(--text-tertiary);
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .version-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--green);
        animation: pulseGlow 2s ease-in-out infinite;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
<div class="hero-container">
  <div class="hero-icon">🔄</div>
  <div class="hero-title">Transaction Reconciliation</div>
  <p class="hero-sub">Exact matching · Fuzzy scoring · LLM reasoning</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding:1rem 0 0.5rem 0;">'
        '<span style="font-size:1.6rem;">⚙️</span>'
        '<div style="font-size:1rem; font-weight:700; color:var(--text-primary); margin-top:0.2rem; letter-spacing:-0.01em;">Configuration</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Date Proximity<span class="sidebar-section-line"></span></div>', unsafe_allow_html=True)
    date_gap = st.slider(
        "Max settlement lag (days)",
        min_value=1, max_value=7, value=3, step=1,
        help="Records within this many days apart are fuzzy-match candidates.",
    )

    st.markdown('<div class="sidebar-section">Amount Variance<span class="sidebar-section-line"></span></div>', unsafe_allow_html=True)
    amount_variance = st.slider(
        "Max amount difference (%)",
        min_value=0.5, max_value=10.0, value=2.0, step=0.5,
        help="Records within this % amount difference are fuzzy-match candidates.",
    )

    st.markdown('<div class="sidebar-section">Merchant Similarity<span class="sidebar-section-line"></span></div>', unsafe_allow_html=True)
    merchant_sim = st.slider(
        "Min merchant name similarity (%)",
        min_value=60, max_value=100, value=80, step=5,
        help="rapidfuzz token_sort_ratio threshold.",
    )

    st.markdown('<div class="sidebar-section">LLM Reasoning<span class="sidebar-section-line"></span></div>', unsafe_allow_html=True)
    llm_enabled = st.toggle(
        "Enable LLM reasoning (Claude)",
        value=bool(os.environ.get("ANTHROPIC_API_KEY")),
        help="Requires ANTHROPIC_API_KEY environment variable.",
    )
    if llm_enabled and not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY not set. LLM will fall back to rule-based scoring.")

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; padding:0.5rem 0;">'
        '<span class="version-tag"><span class="version-dot"></span> v1.0 · Streamlit</span>'
        '</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main — file upload
# ---------------------------------------------------------------------------

col_gw, col_bank = st.columns(2)

with col_gw:
    st.markdown(
        '<div class="upload-card">'
        '<div class="upload-card-title">Payment Gateway CSV</div>'
        '<div class="upload-card-sub">transaction_id, amount, date, merchant_name, reference_number</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    gw_file = st.file_uploader(
        "Upload payment_gateway.csv",
        type=["csv"],
        key="gw_upload",
        label_visibility="collapsed",
    )
    if gw_file:
        st.success(f"Uploaded: {gw_file.name} ({gw_file.size:,} bytes)")

with col_bank:
    st.markdown(
        '<div class="upload-card" style="animation-delay:0.08s">'
        '<div class="upload-card-title">Bank Settlement CSV</div>'
        '<div class="upload-card-sub">transaction_id, amount, date, merchant_name, reference_number</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    bank_file = st.file_uploader(
        "Upload bank_settlement.csv",
        type=["csv"],
        key="bank_upload",
        label_visibility="collapsed",
    )
    if bank_file:
        st.success(f"Uploaded: {bank_file.name} ({bank_file.size:,} bytes)")

# ---------------------------------------------------------------------------
# Run button
# ---------------------------------------------------------------------------

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
run_col, _ = st.columns([1, 3])
with run_col:
    run_clicked = st.button("Run Reconciliation", use_container_width=True)

# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

if run_clicked:
    if not gw_file or not bank_file:
        st.error("Please upload both CSV files before running reconciliation.")
        st.stop()

    config = ReconciliationConfig(
        date_gap_days=date_gap,
        amount_variance_pct=amount_variance,
        merchant_similarity_threshold=float(merchant_sim),
        min_candidate_score=0.50,
        llm_enabled=llm_enabled,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        gw_path = tmp / "payment_gateway.csv"
        bank_path = tmp / "bank_settlement.csv"
        gw_path.write_bytes(gw_file.read())
        bank_path.write_bytes(bank_file.read())

        with st.spinner("Running reconciliation pipeline..."):
            try:
                result = run_pipeline(gw_path, bank_path, config)
                out_dir = tmp / "outputs"
                report_paths = write_all_reports(result, out_dir)
                metrics = generate_summary_metrics(result)

                st.session_state["result"] = result
                st.session_state["metrics"] = metrics
                st.session_state["report_paths"] = report_paths
                if "approvals" not in st.session_state:
                    st.session_state["approvals"] = {}

                st.success("Reconciliation complete!")
            except ValueError as exc:
                st.error(f"Configuration error: {exc}")
                st.stop()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Pipeline error: {exc}")
                logging.exception("Pipeline error")
                st.stop()

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------

if "result" not in st.session_state:
    st.markdown(
        """
<div class="empty-state">
  <div class="empty-state-icon">📂</div>
  <div class="empty-state-text">
    Upload both files and click <strong>Run Reconciliation</strong> to begin
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

result = st.session_state["result"]
metrics = st.session_state["metrics"]
report_paths = st.session_state["report_paths"]

# ---------------------------------------------------------------------------
# Metric cards
# ---------------------------------------------------------------------------

st.markdown('<div class="section-header">Summary Metrics</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)

_METRIC_ICONS = {
    "Match Rate": "📊",
    "Exact": "🎯",
    "Fuzzy": "🔍",
    "Partial": "⚠️",
    "Exceptions": "❌",
    "Ingest Errors": "⛔",
}


def metric_card(col, label: str, value, sub: str = "", delay: int = 1):
    icon = _METRIC_ICONS.get(label, "📈")
    col.markdown(
        f"""
<div class="metric-card mc-delay-{delay}">
  <div class="mc-icon">{icon}</div>
  <div class="mc-label">{label}</div>
  <div class="mc-value">{value}</div>
  <div class="mc-sub">{sub}</div>
</div>
""",
        unsafe_allow_html=True,
    )


metric_card(c1, "Match Rate", f"{metrics['match_rate_pct']}%", "of gateway records", 1)
metric_card(c2, "Exact", metrics["exact_matches"], "same reference", 2)
metric_card(c3, "Fuzzy", metrics["fuzzy_llm_matches"] + metrics["fuzzy_rule_matches"], "LLM + rule-based", 3)
metric_card(c4, "Partial", metrics["partial_matches"], "need review", 4)
metric_card(c5, "Exceptions", metrics["exceptions"], "no match found", 5)
metric_card(c6, "Ingest Errors", metrics["ingestion_errors"], "bad rows", 6)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tab layout
# ---------------------------------------------------------------------------

tab_partial, tab_exceptions, tab_matched, tab_audit = st.tabs([
    f"Partial Matches ({len(result.partial_matches)})",
    f"Exceptions ({len(result.exceptions)})",
    f"Matched ({len(result.matched)})",
    "Audit Trail",
])

# ---------------------------------------------------------------------------
# Helper: record card HTML
# ---------------------------------------------------------------------------


def _record_card_html(tx, label: str) -> str:
    if tx is None:
        return f'<div class="record-card"><div class="record-card-label">{label}</div><div style="color:var(--text-tertiary); font-size:0.8rem;">No record</div></div>'

    rows = [
        ("ID", tx.transaction_id),
        ("Amount", f"₹{tx.amount:,.2f}"),
        ("Date", str(tx.date)),
        ("Merchant", tx.merchant_name),
        ("Reference", tx.reference_number),
    ]
    rows_html = "".join(
        f'<div class="record-row"><span class="record-key">{k}</span><span class="record-val">{v}</span></div>'
        for k, v in rows
    )
    return f'<div class="record-card"><div class="record-card-label">{label}</div>{rows_html}</div>'


def _confidence_html(conf: float) -> str:
    pct = int(conf * 100)
    if conf >= 0.85:
        color = "var(--green)"
    elif conf >= 0.6:
        color = "var(--amber)"
    else:
        color = "var(--red)"
    return (
        f'<div class="confidence-meter">'
        f'<span style="font-weight:600; color:{color}; font-size:0.88rem; font-variant-numeric:tabular-nums;">{pct}%</span>'
        f'<div class="confidence-bar"><div class="confidence-fill" style="width:{pct}%; background:{color};"></div></div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Helper: format a MatchResult row as a flat dict for a dataframe
# ---------------------------------------------------------------------------

def _fmt_tx(tx, prefix: str) -> dict:
    if tx is None:
        return {f"{prefix}_id": "—", f"{prefix}_amount": "—", f"{prefix}_date": "—",
                f"{prefix}_merchant": "—", f"{prefix}_ref": "—"}
    return {
        f"{prefix}_id": tx.transaction_id,
        f"{prefix}_amount": f"₹{tx.amount:,.2f}",
        f"{prefix}_date": str(tx.date),
        f"{prefix}_merchant": tx.merchant_name,
        f"{prefix}_ref": tx.reference_number,
    }

def match_to_row(m: MatchResult) -> dict:
    row = {}
    row.update(_fmt_tx(m.gateway_tx, "gw"))
    row.update(_fmt_tx(m.bank_tx, "bank"))
    row["status"] = m.status.value
    row["confidence"] = f"{m.confidence:.0%}"
    row["discrepancies"] = " | ".join(m.discrepancy_notes) if m.discrepancy_notes else "—"
    row["llm_reasoning"] = m.llm_reasoning or "—"
    row["llm_available"] = "✅" if m.llm_available else "⚠️ Rule-based"
    return row


# ---------------------------------------------------------------------------
# Tab: Partial Matches
# ---------------------------------------------------------------------------

with tab_partial:
    if not result.partial_matches:
        st.info("No partial matches — all fuzzy candidates were either confirmed or rejected.")
    else:
        st.markdown(
            '<div class="section-header">Partial Matches — Require Manual Review</div>',
            unsafe_allow_html=True,
        )
        st.caption("Use the Approve / Reject toggles to manually review each fuzzy match.")

        if "approvals" not in st.session_state:
            st.session_state["approvals"] = {}

        for i, m in enumerate(result.partial_matches):
            gw_id = m.gateway_tx.transaction_id if m.gateway_tx else f"pm_{i}"
            with st.expander(
                f"#{i+1} · Confidence {m.confidence:.0%} · {m.discrepancy_notes[0] if m.discrepancy_notes else ''}",
                expanded=False,
            ):
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown(
                        _record_card_html(m.gateway_tx, "Gateway Record"),
                        unsafe_allow_html=True,
                    )
                with c_right:
                    st.markdown(
                        _record_card_html(m.bank_tx, "Bank Record"),
                        unsafe_allow_html=True,
                    )

                if m.discrepancy_notes:
                    st.markdown("**Discrepancies:**")
                    for note in m.discrepancy_notes:
                        st.markdown(f"- {note}")

                if m.llm_reasoning:
                    st.markdown(
                        f'<div class="llm-callout">'
                        f'<strong>LLM Reasoning:</strong> {m.llm_reasoning}'
                        f'{"  <em style=\"color:var(--amber);\">(rule-based fallback)</em>" if not m.llm_available else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                approval = st.session_state["approvals"].get(gw_id, "pending")
                col_a, col_r, col_s = st.columns([1, 1, 3])
                with col_a:
                    if st.button(
                        "Approve",
                        key=f"approve_{i}",
                        type="primary" if approval == "approved" else "secondary",
                    ):
                        st.session_state["approvals"][gw_id] = "approved"
                        st.rerun()
                with col_r:
                    if st.button(
                        "Reject",
                        key=f"reject_{i}",
                        type="primary" if approval == "rejected" else "secondary",
                    ):
                        st.session_state["approvals"][gw_id] = "rejected"
                        st.rerun()
                with col_s:
                    if approval != "pending":
                        cls = "approval-approved" if approval == "approved" else "approval-rejected"
                        label = "Approved" if approval == "approved" else "Rejected"
                        st.markdown(
                            f'<span class="approval-badge {cls}">{label}</span>',
                            unsafe_allow_html=True,
                        )

# ---------------------------------------------------------------------------
# Tab: Exceptions
# ---------------------------------------------------------------------------

with tab_exceptions:
    if not result.exceptions:
        st.info("No exceptions — all records were matched!")
    else:
        st.markdown(
            '<div class="section-header">Exceptions — No Matching Record Found</div>',
            unsafe_allow_html=True,
        )

        exc_rows = []
        for m in result.exceptions:
            tx = m.gateway_tx or m.bank_tx
            source = "gateway" if m.gateway_tx else ("bank" if m.bank_tx else "ingestion error")
            exc_rows.append({
                "Source": source.title(),
                "Transaction ID": tx.transaction_id if tx else "N/A",
                "Amount": f"₹{tx.amount:,.2f}" if tx else "N/A",
                "Date": str(tx.date) if tx else "N/A",
                "Merchant": tx.merchant_name if tx else "N/A",
                "Reference": tx.reference_number if tx else "N/A",
                "Reason": " | ".join(m.discrepancy_notes),
                "LLM Reasoning": m.llm_reasoning or "—",
            })

        df = pd.DataFrame(exc_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Tab: Matched
# ---------------------------------------------------------------------------

with tab_matched:
    if not result.matched:
        st.warning("No matched records found.")
    else:
        st.markdown(
            '<div class="section-header">Matched Transactions</div>',
            unsafe_allow_html=True,
        )

        match_rows = []
        for m in result.matched:
            match_rows.append({
                "Status": m.status.value.replace("_", " ").title(),
                "Confidence": f"{m.confidence:.0%}",
                "GW Transaction ID": m.gateway_tx.transaction_id if m.gateway_tx else "—",
                "Bank Transaction ID": m.bank_tx.transaction_id if m.bank_tx else "—",
                "Amount (GW)": f"₹{m.gateway_tx.amount:,.2f}" if m.gateway_tx else "—",
                "Amount (Bank)": f"₹{m.bank_tx.amount:,.2f}" if m.bank_tx else "—",
                "Date (GW)": str(m.gateway_tx.date) if m.gateway_tx else "—",
                "Date (Bank)": str(m.bank_tx.date) if m.bank_tx else "—",
                "Merchant": m.gateway_tx.merchant_name if m.gateway_tx else "—",
                "Reference": m.gateway_tx.reference_number if m.gateway_tx else "—",
                "Notes": " | ".join(m.discrepancy_notes) if m.discrepancy_notes else "—",
            })

        df = pd.DataFrame(match_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Tab: Audit trail preview
# ---------------------------------------------------------------------------

with tab_audit:
    st.markdown(
        '<div class="section-header">Audit Trail</div>', unsafe_allow_html=True
    )
    st.caption("Every reconciliation decision is recorded here with timestamp, confidence, and reasoning.")

    all_matches = result.matched + result.partial_matches + result.exceptions
    audit_rows = []
    for m in all_matches:
        gw_id = m.gateway_tx.transaction_id if m.gateway_tx else "—"
        bank_id = m.bank_tx.transaction_id if m.bank_tx else "—"
        audit_rows.append({
            "GW TX ID": gw_id,
            "Bank TX ID": bank_id,
            "Decision": m.status.value,
            "Confidence": f"{m.confidence:.0%}",
            "Rule Score": f"{m.rule_score:.0%}",
            "LLM": "Yes" if m.llm_available else "Rule-based",
            "Reasoning": (m.llm_reasoning[:120] + "...") if len(m.llm_reasoning) > 120 else m.llm_reasoning or "—",
            "Timestamp": str(m.matched_at) if m.matched_at else "—",
        })

    if audit_rows:
        st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Download section
# ---------------------------------------------------------------------------

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Download Reports</div>', unsafe_allow_html=True)

dl1, dl2, dl3, dl4 = st.columns(4)


def _read_file(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    return b""


with dl1:
    data = _read_file(report_paths.get("exceptions_csv", Path("nonexistent")))
    st.download_button(
        "Exceptions CSV",
        data=data,
        file_name="exceptions.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dl2:
    data = _read_file(report_paths.get("exception_report_md", Path("nonexistent")))
    st.download_button(
        "Exception Report",
        data=data,
        file_name="exception_report.md",
        mime="text/markdown",
        use_container_width=True,
    )

with dl3:
    data = _read_file(report_paths.get("audit_trail_jsonl", Path("nonexistent")))
    st.download_button(
        "Audit Trail",
        data=data,
        file_name="audit_trail.jsonl",
        mime="application/json",
        use_container_width=True,
    )

with dl4:
    data = _read_file(report_paths.get("matched_csv", Path("nonexistent")))
    st.download_button(
        "Matched Records",
        data=data,
        file_name="matched.csv",
        mime="text/csv",
        use_container_width=True,
    )
