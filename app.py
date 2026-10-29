import streamlit as st
import streamlit.components.v1 as components

try:
    st._config.set_option("server.maxUploadSize", 500)
    st._config.set_option("server.maxMessageSize", 500)
except Exception:
    pass
import os
import json
import importlib
import ai_engine
importlib.reload(ai_engine)
from database import get_user_data, save_user_data
from ai_engine import (
    ask_gemini,
    generate_twin_question,
    analyze_exam_sheet,
    extract_exam_scores,
    get_youtube_transcript,
    generate_flashcards_list,
    generate_hap_ozet_structured,
    generate_lgs_quiz_list,
    solve_page_questions_structured,
    get_ai_lgs_topics,
    generate_custom_lgs_test,
    generate_sinotest_activity,
    MEB_8_SINIF_KONULARI,
)
from gtts import gTTS
import pypdf
import pandas as pd
from PIL import Image
import datetime

st.set_page_config(
    page_title="LGS Karargahı", 
    page_icon="🎯", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

_mobil_pdf_yukleyici = components.declare_component(
    "mobil_pdf_yukleyici",
    url="https://sinemalir.github.io/lgs-karargahi/uploader.html",
)

# --- MODERN, TEMİZ VE KULLANICI DOSTU ÖZEL CSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 55%, #eef2ff 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    /* Boş oluşan karargah-card divlerini gizle */
    .karargah-card:empty {
        display: none !important;
    }
    .karargah-card {
        background: white;
        padding: 22px;
        border-radius: 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        margin-bottom: 18px;
        border: 1px solid #e2e8f0;
    }
    /* Sadece gerçek bordered container'ları (st.container(border=True)) kart yap, kolonları (stColumn) hariç tut */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 18px !important;
        border: 1.5px solid #e2e8f0 !important;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
        padding: 16px !important;
        margin-bottom: 12px;
    }
    div[data-testid="stColumn"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="column"] > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stColumn"] > div > div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="column"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin-bottom: 0 !important;
        border-radius: 0 !important;
    }
    /* Üst Bar */
    .top-bar {
        background: white;
        padding: 14px 22px;
        border-radius: 18px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 900;
        background: linear-gradient(90deg, #4f46e5, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .user-pill {
        background: #f5f3ff;
        color: #5b21b6;
        padding: 6px 14px;
        border-radius: 99px;
        font-size: 13.5px;
        font-weight: 700;
        border: 1px solid #ddd6fe;
    }
    /* Hero Kartı (Soft İndigo & Lavanta Tonu) */
    .hero-card {
        background: linear-gradient(135deg, #5b6cf9 0%, #7c69ef 55%, #9381ff 100%);
        color: white !important;
        padding: 26px;
        border-radius: 24px;
        box-shadow: 0 10px 24px rgba(91, 108, 249, 0.18);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .hero-card h2, .hero-card span, .hero-card div {
        color: #ffffff !important;
    }
    .hero-card p {
        color: #eef2ff !important;
        font-size: 15px;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.22);
        color: #ffffff !important;
        padding: 5px 12px;
        border-radius: 99px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    /* Hızlı Erişim İstasyon Kartları */
    .station-card {
        background: #f8fafc;
        border: 1.5px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        height: 100%;
        transition: all 0.2s ease;
    }
    .station-card:hover {
        border-color: #6366f1;
        background: #eff6ff;
        transform: translateY(-2px);
    }
    .station-icon {
        font-size: 26px;
        margin-bottom: 8px;
    }
    .station-title {
        font-size: 15px;
        font-weight: 800;
        color: #1e293b !important;
        margin-bottom: 4px;
    }
    .station-desc {
        font-size: 12.5px;
        color: #64748b !important;
        line-height: 1.4;
    }
    /* Radyo Menüsünü Simetrik ve Hizalı 3x2 Grid Sekme Haline Getirme */
    div[role="radiogroup"] {
        background: white;
        padding: 10px;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[role="radiogroup"] > label {
        background: #f8fafc;
        padding: 10px 12px !important;
        min-height: 48px !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        white-space: nowrap !important;
    }
    div[role="radiogroup"] > label:hover {
        background: #eff6ff;
        border-color: #93c5fd;
    }
    @media (max-width: 640px) {
        div[role="radiogroup"] {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
        font-weight: 800;
    }
    /* Başlık Puntoları Biraz Küçültüldü (Daha Ferah Kullanıcı Deneyimi) */
    div[data-testid="stMarkdownContainer"] h1, h1 { font-size: 1.55rem !important; line-height: 1.3 !important; }
    div[data-testid="stMarkdownContainer"] h2, h2 { font-size: 1.32rem !important; line-height: 1.3 !important; }
    div[data-testid="stMarkdownContainer"] h3, h3 { font-size: 1.15rem !important; line-height: 1.35 !important; }
    div[data-testid="stMarkdownContainer"] h4, h4 { font-size: 1.0rem !important; line-height: 1.35 !important; }
    div[data-testid="stMarkdownContainer"] h5, h5 { font-size: 0.92rem !important; }
    @media (max-width: 640px) {
        div[data-testid="stMarkdownContainer"] h1, h1 { font-size: 1.35rem !important; }
        div[data-testid="stMarkdownContainer"] h2, h2 { font-size: 1.18rem !important; }
        div[data-testid="stMarkdownContainer"] h3, h3 { font-size: 1.05rem !important; }
        div[data-testid="stMarkdownContainer"] h4, h4 { font-size: 0.95rem !important; }
        .brand-title { font-size: 20px !important; }
        .top-bar { padding: 10px 14px !important; }
        .hero-card { padding: 18px !important; }
        .hero-card h2 { font-size: 1.25rem !important; }
    }
    /* 📱 Mobilde Yana Taşmayı Engelle */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    .block-container, [data-testid="stMainBlockContainer"] {
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    @media (max-width: 640px) {
        .block-container, [data-testid="stMainBlockContainer"] {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }
    }
    div[data-testid="stColumn"], div[data-testid="column"] {
        min-width: 0 !important;
    }
    img, iframe, video, svg, canvas {
        max-width: 100% !important;
    }
    div[data-testid="stMarkdownContainer"] {
        overflow-wrap: break-word;
    }
    div[data-testid="stMarkdownContainer"] pre, div[data-testid="stMarkdownContainer"] code {
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    div[data-testid="stMarkdownContainer"] table {
        display: block;
        max-width: 100%;
        overflow-x: auto;
    }
    p, label, li, div[data-testid="stMarkdownContainer"] {
        color: #334155;
    }
    /* Tüm Buton Konteynerleri Mobilde de %100 Tam Genişlik Olsun */
    .stButton,
    div[data-testid="stButton"],
    .stDownloadButton,
    div[data-testid="stDownloadButton"],
    div[data-testid="stPopover"] {
        width: 100% !important;
    }
    /* Tüm Butonlar, Download Butonu ve 📋 Menü (Popover) Butonu Soft İndigo-Lavanta Gradyan Stilde */
    .stButton > button,
    .stDownloadButton > button,
    div[data-testid="stPopover"] button,
    [data-testid="stPopover"] > div > button {
        width: 100% !important;
        background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 3px 10px rgba(99, 102, 241, 0.18) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button p, .stButton > button span, .stButton > button div,
    .stDownloadButton > button p, .stDownloadButton > button span, .stDownloadButton > button div,
    div[data-testid="stPopover"] button p, div[data-testid="stPopover"] button span,
    div[data-testid="stPopover"] button div, div[data-testid="stPopover"] button svg {
        background: transparent !important;
        color: white !important;
        fill: white !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stPopover"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(99, 102, 241, 0.28) !important;
    }
    /* Mobilde Önceki/Sonraki Sayfa Barı ve PDF Kart Butonları Alt Alta Düşmesin, Yan Yana Kalsın */
    div[data-testid="stHorizontalBlock"]:has(.st-key-pdf_prev_top),
    div[data-testid="stHorizontalBlock"]:has(.st-key-pdf_prev_bot),
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-pdf_prev_top) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-pdf_prev_bot) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-open_"]) > div[data-testid="stColumn"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 0% !important;
    }
    /* PDF İstasyonu "Bu Sayfayla Ne Yapmak İstersin?" Butonları Mobilde Okunaklı Dikey Blok */
    .st-key-act_coz button,
    .st-key-act_ikiz button,
    .st-key-act_ozet button {
        white-space: normal !important;
        word-break: normal !important;
        line-height: 1.3 !important;
    }
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"]:has(.st-key-act_coz) {
            display: flex !important;
            flex-direction: column !important;
            gap: 10px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-act_coz) > div[data-testid="stColumn"] {
            width: 100% !important;
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
        .st-key-act_coz button,
        .st-key-act_ikiz button,
        .st-key-act_ozet button {
            min-height: 48px !important;
            font-size: 14px !important;
            font-weight: 800 !important;
            white-space: normal !important;
            word-break: normal !important;
            line-height: 1.35 !important;
            padding: 10px 14px !important;
            border-radius: 14px !important;
            text-align: center !important;
        }
    }
    /* Popover Açılır Menü İçeriği Beyaz Zemin Üzerine Temiz Görünüm */
    div[data-testid="stPopoverBody"] {
        background: white !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        padding: 12px !important;
    }
    /* Tüm Input, NumberInput, Selectbox ve Etiketler İçin Ferah Açık Tema */
    div[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] p {
        white-space: nowrap !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #334155 !important;
        margin-bottom: 2px !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-testid="stNumberInputContainer"] {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }
    div[data-testid="stNumberInputContainer"] input,
    div[data-baseweb="input"] input,
    textarea {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        text-align: center !important;
        -webkit-text-fill-color: #0f172a !important;
        padding: 8px 6px !important;
    }
    div[data-baseweb="input"] input[type="text"],
    div[data-baseweb="input"] input[type="password"],
    textarea {
        text-align: left !important;
        padding: 8px 12px !important;
    }
    /* Dar kutularda rakamları sıkıştıran +/- step butonlarını gizle, rakamlar tam görünsün */
    button[data-testid="stNumberInputStepDown"],
    button[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInputContainer"] button {
        display: none !important;
    }
    /* Disabled (Boş sayısı) kutusu da temiz açık gri görünsün */
    div[data-testid="stNumberInputContainer"]:has(input:disabled) {
        background-color: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
    }
    div[data-testid="stNumberInputContainer"] input:disabled {
        background-color: #f1f5f9 !important;
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }
</style>
""", unsafe_allow_html=True)

# Kullanıcılar
KULLANICILAR = {
    "ada": {"sifre": "1234", "ad": "Ada 🚀"},
    "sevval": {"sifre": "5678", "ad": "Şevval ⭐"}
}

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.6, 2.8, 0.6])
    with col2:
        with st.container(border=True):
            st.markdown("<div style='text-align: center; padding: 10px 0;'>", unsafe_allow_html=True)
            st.markdown("<div><span style='font-size: 30px; margin-right: 6px;'>🎯</span><span class='brand-title' style='font-size: 30px;'>LGS Karargahı</span></div>", unsafe_allow_html=True)
            st.caption("Hedefe Giden En Akıllı Çalışma İstasyonu")
            st.markdown("</div>", unsafe_allow_html=True)
            
            secilen_kullanici = st.selectbox("👩‍🎓 Öğrenci Seçin", ["Ada", "Şevval"])
            sifre = st.text_input("🔑 Gizli Şifre", type="password")
            
            if st.button("🚀 Karargaha Giriş Yap"):
                k_key = "sevval" if secilen_kullanici == "Şevval" else secilen_kullanici.lower()
                if KULLANICILAR[k_key]["sifre"] == sifre:
                    st.session_state.user = k_key
                    st.rerun()
                else:
                    st.error("Şifre hatalı!")
    st.stop()


current_user = st.session_state.user
user_display_name = KULLANICILAR[current_user]["ad"]

# Sayfa En Üst Çapası (Yukarı Kaydır Butonu İçin)
st.markdown("<div id='sayfa-basi'></div>", unsafe_allow_html=True)

# İstasyonlar Menüsü ve Navigasyon Geçmişi (Geri Butonu Desteği)
ISTASYONLAR = [
    "🏠 Ana Sayfa", 
    "📚 PDF Havuzu", 
    "⚡ Hızlı Öğren (Video/Kaynak)", 
    "🤖 Soru Çöz & İkiz", 
    "📷 Deneme Analizi", 
    "❌ Hata & Gelişim"
]
if "aktif_istasyon" not in st.session_state:
    st.session_state.aktif_istasyon = "🏠 Ana Sayfa"
if "nav_gecmisi" not in st.session_state:
    st.session_state.nav_gecmisi = ["🏠 Ana Sayfa"]
if "onceki_secim" not in st.session_state:
    st.session_state.onceki_secim = "🏠 Ana Sayfa"

def istasyona_git(hedef):
    mevcut = st.session_state.get("aktif_istasyon", "🏠 Ana Sayfa")
    if hedef != mevcut:
        st.session_state.nav_gecmisi.append(mevcut)
    st.session_state.aktif_istasyon = hedef
    st.session_state.onceki_secim = hedef
    st.session_state.hedef_scroll = "sayfa-basi" if hedef == "🏠 Ana Sayfa" else "istasyon-baslangic"

def geri_git():
    if len(st.session_state.nav_gecmisi) > 0:
        hedef = st.session_state.nav_gecmisi.pop()
        st.session_state.aktif_istasyon = hedef
        st.session_state.onceki_secim = hedef
    else:
        st.session_state.aktif_istasyon = "🏠 Ana Sayfa"
        st.session_state.onceki_secim = "🏠 Ana Sayfa"
    st.session_state.hedef_scroll = "sayfa-basi" if st.session_state.aktif_istasyon == "🏠 Ana Sayfa" else "istasyon-baslangic"

def radyodan_degisti():
    yeni = st.session_state.aktif_istasyon
    eski = st.session_state.get("onceki_secim", "🏠 Ana Sayfa")
    if yeni != eski:
        st.session_state.nav_gecmisi.append(eski)
        st.session_state.onceki_secim = yeni

# Üst Mobil Bar: Marka + Hızlı Menü + Çıkış
st.markdown(f"""
    <div class='top-bar'>
        <div><span style='font-size: 24px; margin-right: 6px;'>🎯</span><span class='brand-title'>LGS Karargahı</span></div>
        <span class='user-pill'>🛡️ {user_display_name}</span>
    </div>
""", unsafe_allow_html=True)

# Mobil Hızlı Kontrol Çubuğu (⬅️ Geri | 🏠 Ana Sayfa | 📋 Menü | 🚪 Çıkış) — Tek Satır
m_col1, m_col2, m_col3, m_col4 = st.columns([0.9, 1.38, 1.12, 0.9], gap="small")
with m_col1:
    st.button("⬅️ Geri", on_click=geri_git, use_container_width=True, key="mob_back_btn")
with m_col2:
    st.button("🏠 Ana Sayfa", on_click=istasyona_git, args=("🏠 Ana Sayfa",), use_container_width=True, key="mob_home_btn")
with m_col3:
    with st.popover("📋 Menü", use_container_width=True):
        st.markdown("**📍 İstasyon Seç:**")
        for ist in ISTASYONLAR:
            st.button(ist, on_click=istasyona_git, args=(ist,), key=f"pop_{ist}", use_container_width=True)
with m_col4:
    if st.button("🚪 Çıkış", use_container_width=True, key="mob_exit_btn"):
        st.session_state.user = None
        st.rerun()

# 5 İstasyon İçin Soft Renkli, Kompakt Tıklanabilir Buton Izgarası (Alttaki Ana Sayfa Butonu Kaldırıldı)
ISTASYON_KISA_AD = [
    ("📚 PDF Havuzu", "📚 PDF Havuzu"),
    ("⚡ Hızlı Öğren", "⚡ Hızlı Öğren (Video/Kaynak)"),
    ("⚡ SinoTest", "🤖 Soru Çöz & İkiz"),
    ("📷 Deneme Analizi", "📷 Deneme Analizi"),
    ("❌ Hata & Gelişim", "❌ Hata & Gelişim"),
]

st.markdown("""
<style>
    /* Üstteki 4'lü Kontrol Çubuğu (Geri | Ana Sayfa | Menü | Çıkış) Mobilde de Tek Satırda Yan Yana Kalsın */
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) > div[data-testid="stColumn"] {
        min-width: 0 !important;
        width: auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) > div[data-testid="stColumn"]:nth-child(1) { flex: 0.9 1 0% !important; }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) > div[data-testid="stColumn"]:nth-child(2) { flex: 1.42 1 0% !important; }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) > div[data-testid="stColumn"]:nth-child(3) { flex: 1.15 1 0% !important; }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) > div[data-testid="stColumn"]:nth-child(4) { flex: 0.9 1 0% !important; }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) button {
        min-height: 40px !important;
        padding: 7px 6px !important;
        border-radius: 11px !important;
        white-space: nowrap !important;
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%) !important;
        border: 1.5px solid #c7d2fe !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) button p,
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) button span,
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) button div,
    div[data-testid="stHorizontalBlock"]:has(.st-key-mob_back_btn) button svg {
        font-size: 12.5px !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        letter-spacing: -0.2px !important;
        color: #4338ca !important;
        fill: #4338ca !important;
    }

    /* İstasyon Satırları da Mobilde Alt Alta Düşmesin ( Kompakt 2 Satır ) */
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-ist_btn_"]) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has([class*="st-key-ist_btn_"]) > div[data-testid="stColumn"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 0% !important;
    }

    /* 5 İstasyon Butonu İçin Ayrı Soft Pastel Renkler ve Tam Hizalama */
    div[class*="st-key-ist_btn_"] button {
        min-height: 44px !important;
        padding: 8px 6px !important;
        border-radius: 12px !important;
        font-size: 13px !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        box-shadow: 0 2px 7px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.2s ease !important;
    }
    div[class*="st-key-ist_btn_"] button p,
    div[class*="st-key-ist_btn_"] button span {
        font-size: 12.5px !important;
        white-space: nowrap !important;
    }
    div[class*="st-key-ist_btn_"] button:hover {
        transform: translateY(-2px) !important;
        filter: brightness(0.98) !important;
    }
    /* 0: PDF Havuzu - Soft Lavanta */
    .st-key-ist_btn_0 button {
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%) !important;
        border: 1.5px solid #ddd6fe !important;
    }
    .st-key-ist_btn_0 button p, .st-key-ist_btn_0 button span, .st-key-ist_btn_0 button div {
        color: #5b21b6 !important;
    }
    /* 1: Hızlı Öğren - Soft Kayısı / Krem */
    .st-key-ist_btn_1 button {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
        border: 1.5px solid #fde68a !important;
    }
    .st-key-ist_btn_1 button p, .st-key-ist_btn_1 button span, .st-key-ist_btn_1 button div {
        color: #b45309 !important;
    }
    /* 2: SinoTest - Soft Nane Yeşili */
    .st-key-ist_btn_2 button {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
        border: 1.5px solid #a7f3d0 !important;
    }
    .st-key-ist_btn_2 button p, .st-key-ist_btn_2 button span, .st-key-ist_btn_2 button div {
        color: #047857 !important;
    }
    /* 3: Deneme Analizi - Soft Pudra / Gül */
    .st-key-ist_btn_3 button {
        background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%) !important;
        border: 1.5px solid #fecdd3 !important;
    }
    .st-key-ist_btn_3 button p, .st-key-ist_btn_3 button span, .st-key-ist_btn_3 button div {
        color: #be123c !important;
    }
    /* 4: Hata & Gelişim - Soft Gökyüzü Mavisi */
    .st-key-ist_btn_4 button {
        background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%) !important;
        border: 1.5px solid #c7d2fe !important;
    }
    .st-key-ist_btn_4 button p, .st-key-ist_btn_4 button span, .st-key-ist_btn_4 button div {
        color: #3730a3 !important;
    }
</style>
""", unsafe_allow_html=True)

with st.container(border=True):
    r1_c1, r1_c2, r1_c3 = st.columns(3, gap="small")
    r2_c1, r2_c2 = st.columns(2, gap="small")
    grid_cols = [r1_c1, r1_c2, r1_c3, r2_c1, r2_c2]
    for idx, (gorunen_ad, tam_hedef) in enumerate(ISTASYON_KISA_AD):
        aktif_mi = (st.session_state.aktif_istasyon == tam_hedef)
        etiket = f"✨ {gorunen_ad}" if aktif_mi else gorunen_ad
        with grid_cols[idx]:
            st.button(
                etiket,
                key=f"ist_btn_{idx}",
                on_click=istasyona_git,
                args=(tam_hedef,),
                use_container_width=True
            )

menu = st.session_state.aktif_istasyon

# 📍 Seçili (Aktif) İstasyon Butonunu Soft ama Belirgin İndigo-Lavanta Renginde Göster
_aktif_selector = ".st-key-mob_home_btn button"
for _i, (_g, _hedef) in enumerate(ISTASYON_KISA_AD):
    if _hedef == menu:
        _aktif_selector = f".st-key-ist_btn_{_i} button"
        break
st.markdown(f"""
<style>
    {_aktif_selector} {{
        background: linear-gradient(135deg, #5b6cf9 0%, #7c69ef 100%) !important;
        border: 1.5px solid #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.20), 0 5px 12px rgba(99, 102, 241, 0.25) !important;
        transform: translateY(-1px);
    }}
    {_aktif_selector} p, {_aktif_selector} span, {_aktif_selector} div {{
        color: #ffffff !important;
        font-weight: 800 !important;
    }}
</style>
""", unsafe_allow_html=True)


# Sağ Altta Yüzen (Floating) "⬆️ Yukarı Çık" ve "🏠 Ana Menü" Mobil Aksiyon Butonları
st.markdown("""
<style>
    .floating-nav {
        position: fixed;
        bottom: 22px;
        right: 18px;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .fab-btn {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
        text-decoration: none !important;
        padding: 12px 16px;
        border-radius: 99px;
        font-weight: 800;
        font-size: 13.5px;
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.28);
        display: flex;
        align-items: center;
        gap: 6px;
        border: 2px solid rgba(255,255,255,0.85);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .fab-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 22px rgba(99, 102, 241, 0.38);
    }
    @media (max-width: 640px) {
        .floating-nav {
            bottom: 12px !important;
            right: 12px !important;
        }
        .fab-btn {
            width: 38px !important;
            height: 38px !important;
            padding: 0 !important;
            border-radius: 50% !important;
            justify-content: center !important;
            font-size: 16px !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
        }
        .fab-btn .fab-txt {
            display: none !important;
        }
    }
</style>
<div class="floating-nav">
    <a href="#sayfa-basi" class="fab-btn" title="En Üste Çık"><span>⬆️</span><span class="fab-txt"> Yukarı Çık</span></a>
</div>
""", unsafe_allow_html=True)

# ----------------- MODÜLLER -----------------
st.markdown("<div id='istasyon-baslangic'></div>", unsafe_allow_html=True)

if menu == "🏠 Ana Sayfa":
    st.markdown(f"""
        <div class='hero-card'>
            <div class='hero-badge'>🌟 GÜNÜN KOMUTA MERKEZİ</div>
            <h2 style='margin: 0; font-size: 26px; font-weight: 900;'>Hoş geldin, {user_display_name}! ✨</h2>
            <p>Bugün hangi istasyonda çalışmak istersin? Aşağıdaki istasyon kartlarından birine tıklayarak hemen başla!</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Tıklanabilir Hızlı İstasyon Kartları (2x2 Grid)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>📚</div>
                <div class='station-title'>Dijital PDF Kütüphanesi</div>
                <div class='station-desc' style='margin-bottom: 12px;'>Yüklenen testleri sayfa sayfa aç, soruları interaktif çöz ve ikiz soru meydan okuması başlat.</div>
            """, unsafe_allow_html=True)
            st.button("📚 Kütüphaneyi Aç →", on_click=istasyona_git, args=("📚 PDF Havuzu",), key="go_pdf", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>⚡</div>
                <div class='station-title'>SinoTest & İkiz Soru</div>
                <div class='station-desc' style='margin-bottom: 12px;'>Dersi, konuyu, zorluğu ve soru sayısını (5-10-20) seçip hızlı test çöz veya fotoğraftan ikiz soru üret.</div>
            """, unsafe_allow_html=True)
            st.button("⚡ SinoTest'e Git →", on_click=istasyona_git, args=("🤖 Soru Çöz & İkiz",), key="go_soru", use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>⚡</div>
                <div class='station-title'>Hızlı Öğren & 3D Flashcard</div>
                <div class='station-desc' style='margin-bottom: 12px;'>Konu yaz veya YouTube videosu ekle; 3D çevirmeli kartlar, podcast ve mini testlerle öğren.</div>
            """, unsafe_allow_html=True)
            st.button("⚡ Hızlı Öğren'e Git →", on_click=istasyona_git, args=("⚡ Hızlı Öğren (Video/Kaynak)",), key="go_hizli", use_container_width=True)

        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>📷</div>
                <div class='station-title'>Deneme Optik & Karnem</div>
                <div class='station-desc' style='margin-bottom: 12px;'>6 ders deneme sonuç belgeni yükle, zayıf kazanımlarını ve haftalık gelişimini gör.</div>
            """, unsafe_allow_html=True)
            st.button("📷 Deneme Analizine Git →", on_click=istasyona_git, args=("📷 Deneme Analizi",), key="go_deneme", use_container_width=True)
        
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
    
    # Günlük Çalışma Rutini & İlerleme Çubuğu
    with st.container(border=True):
        st.markdown("#### 🔥 Günlük Görev Listesi")
        st.caption("Görevlerini tamamladıkça günlük enerji çubuğun dolar!")
        g1 = st.checkbox("📖 En az 20 paragraf sorusu çözüldü")
        g2 = st.checkbox("🧠 Hata defteri ve yanlışlar gözden geçirildi")
        g3 = st.checkbox("⚡ En az 1 adet İkiz Soru veya Mini Test çözüldü")
        tamamlanan = sum([g1, g2, g3])
        st.progress(tamamlanan / 3.0, text=f"Günlük Hedef İlerlemesi: {tamamlanan} / 3 Görev Tamamlandı 🎯")
        if tamamlanan == 3:
            st.balloons()
            st.success("🏆 Harikasın! Bugünün tüm LGS görevlerini eksiksiz tamamladın!")

elif menu == "📚 PDF Havuzu":
    import fitz  # PyMuPDF
    import re as _re
    from pathlib import Path
    
    pdf_lib_dir = Path("pdf_kutuphanesi")
    pdf_lib_dir.mkdir(exist_ok=True)
    
    with st.container(border=True):
        st.markdown("### 📚 Dijital PDF & Soru Kütüphanesi")
        st.write("Yüklenen ders notları, testler ve denemeler kalıcı olarak kütüphaneye kaydedilir. İstediğin kaynağın adını değiştirebilir ve tıklayıp hemen açabilirsin!")
        
        with st.expander("➕ Kütüphaneye Yeni PDF / Test Yükle", expanded=True):
            ders_etiketi = st.selectbox("Hangi Ders?", ["Matematik", "Fen Bilimleri", "Türkçe", "T.C. İnkılap Tarihi", "Din Kültürü", "İngilizce", "Genel Deneme"], key="lib_ders")
            ozel_kaynak_adi = st.text_input(
                "✏️ Kaynak Adı (İsteğe bağlı — boş bırakırsan dosya adı kullanılır):",
                placeholder="Örn: Çarpanlar ve Katlar Test 1",
                key="lib_custom_name"
            )
            ws_ack = st.session_state.get("ws_pdf_ack", "")
            yuklenen_ws = _mobil_pdf_yukleyici(ack=ws_ack, height=120, key="lib_ws_pdf_uploader")
            if isinstance(yuklenen_ws, dict) and yuklenen_ws.get("upload_id") and yuklenen_ws.get("b64"):
                import base64 as _b64
                up_id = str(yuklenen_ws.get("upload_id", ""))
                up_name = str(yuklenen_ws.get("name", "Kaynak.pdf"))
                c_idx = int(yuklenen_ws.get("chunk_index", 0))
                t_chunks = max(1, int(yuklenen_ws.get("total_chunks", 1)))
                b64_str = yuklenen_ws.get("b64", "")
                islenen_anahtar = f"{up_id}:{c_idx}"

                if st.session_state.get("son_islenen_ws_parca") != islenen_anahtar:
                    ham_isim = ozel_kaynak_adi.strip() if ozel_kaynak_adi.strip() else Path(up_name).stem
                    temiz_isim = _re.sub(r'[<>:"/\\|?*]', '-', ham_isim).strip() or "Kaynak"
                    hedef_dosya = pdf_lib_dir / f"[{ders_etiketi}] {temiz_isim}.pdf"
                    tmp_dosya = pdf_lib_dir / f".tmp_{up_id}.part"
                    parca_bytes = _b64.b64decode(b64_str)

                    if t_chunks == 1:
                        hedef_dosya.write_bytes(parca_bytes)
                        st.session_state.son_islenen_ws_parca = islenen_anahtar
                        st.session_state.ws_pdf_ack = f"{up_id}:done"
                        st.session_state.secili_pdf = str(hedef_dosya)
                        st.session_state.pdf_sayfa_no = 1
                        st.session_state.pdf_num_top = 1
                        st.session_state.pdf_cozum_kartlari = None
                        st.session_state.pdf_ikiz_quiz = None
                        st.session_state.pdf_ozet_kart = None
                        st.session_state.hedef_scroll = "acik-kitap-alani"
                        st.rerun()
                    else:
                        mode = "wb" if c_idx == 0 else "ab"
                        with open(tmp_dosya, mode) as f_out:
                            f_out.write(parca_bytes)
                        st.session_state.son_islenen_ws_parca = islenen_anahtar
                        if c_idx + 1 >= t_chunks:
                            if hedef_dosya.exists():
                                hedef_dosya.unlink(missing_ok=True)
                            tmp_dosya.rename(hedef_dosya)
                            st.session_state.ws_pdf_ack = f"{up_id}:done"
                            st.session_state.secili_pdf = str(hedef_dosya)
                            st.session_state.pdf_sayfa_no = 1
                            st.session_state.pdf_num_top = 1
                            st.session_state.pdf_cozum_kartlari = None
                            st.session_state.pdf_ikiz_quiz = None
                            st.session_state.pdf_ozet_kart = None
                            st.session_state.hedef_scroll = "acik-kitap-alani"
                            st.rerun()
                        else:
                            st.session_state.ws_pdf_ack = f"{up_id}:{c_idx}"
                            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📖 Kütüphanedeki Kaynaklar")
        
        kayitli_pdfler = sorted(pdf_lib_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not kayitli_pdfler:
            st.info("Kütüphanede henüz kayıtlı bir PDF yok. Yukarıdaki '➕ Kütüphaneye Yeni PDF / Test Yükle' bölümünden ilk kaynağını ekleyebilirsin!")
        else:
            cols = st.columns(2)
            for idx, pdf_path in enumerate(kayitli_pdfler):
                col = cols[idx % 2]
                with col:
                    boyut_mb = pdf_path.stat().st_size / (1024 * 1024)
                    secili_mi = (st.session_state.get("secili_pdf") == str(pdf_path))
                    kart_stili = "border: 2px solid #2563eb; background: #eff6ff;" if secili_mi else "border: 1.5px solid #e2e8f0; background: #f8fafc;"
                    st.markdown(f"""
                    <div style='{kart_stili} padding: 14px; border-radius: 14px; margin-bottom: 8px;'>
                        <div style='font-size: 14.5px; font-weight: 800; color: #1e293b; line-height: 1.35; word-break: break-word;'>📕 {pdf_path.stem}</div>
                        <div style='font-size: 12px; color: #64748b; margin-top: 4px;'>Boyut: {boyut_mb:.1f} MB</div>
                    </div>
                    """, unsafe_allow_html=True)
                    c_ac, c_ad, c_sil = st.columns([2.2, 1.5, 0.9], gap="small")
                    with c_ac:
                        if st.button("📖 Aç", key=f"open_{idx}", use_container_width=True):
                            st.session_state.secili_pdf = str(pdf_path)
                            st.session_state.pdf_sayfa_no = 1
                            st.session_state.pdf_num_top = 1
                            st.session_state.pdf_cozum_kartlari = None
                            st.session_state.pdf_ikiz_quiz = None
                            st.session_state.pdf_ozet_kart = None
                            st.session_state.hedef_scroll = "acik-kitap-alani"
                            st.rerun()
                    with c_ad:
                        with st.popover("✏️ İsim", use_container_width=True):
                            yeni_isim_gir = st.text_input("Yeni Kaynak Adı:", value=pdf_path.stem, key=f"ren_in_{idx}")
                            if st.button("✅ Kaydet", key=f"ren_save_{idx}", use_container_width=True):
                                temiz_yeni = _re.sub(r'[<>:"/\\|?*]', '-', yeni_isim_gir.strip())
                                if temiz_yeni:
                                    yeni_yol = pdf_lib_dir / f"{temiz_yeni}.pdf"
                                    if yeni_yol != pdf_path:
                                        pdf_path.rename(yeni_yol)
                                        if st.session_state.get("secili_pdf") == str(pdf_path):
                                            st.session_state.secili_pdf = str(yeni_yol)
                                    st.rerun()
                    with c_sil:
                        if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                            if st.session_state.get("secili_pdf") == str(pdf_path):
                                st.session_state.secili_pdf = None
                            pdf_path.unlink(missing_ok=True)
                            st.rerun()
            
            # SEÇİLEN PDF'İ OKUMA VE ÇALIŞMA EKRANI
            secili_yol = st.session_state.get("secili_pdf")
            if secili_yol and Path(secili_yol).exists():
                aktif_pdf = Path(secili_yol)
                doc = fitz.open(str(aktif_pdf))
                toplam_sayfa = max(1, len(doc))
                
                if "pdf_sayfa_no" not in st.session_state:
                    st.session_state.pdf_sayfa_no = 1
                st.session_state.pdf_sayfa_no = max(1, min(toplam_sayfa, int(st.session_state.pdf_sayfa_no)))
                st.session_state.pdf_num_top = st.session_state.pdf_sayfa_no
                
                def _pdf_sayfa_git(hedef_sayfa, maks_sayfa=toplam_sayfa):
                    yeni_s = max(1, min(maks_sayfa, int(hedef_sayfa)))
                    st.session_state.pdf_sayfa_no = yeni_s
                    st.session_state.pdf_num_top = yeni_s
                    st.session_state.pdf_cozum_kartlari = None
                    st.session_state.pdf_ikiz_quiz = None
                    st.session_state.pdf_ozet_kart = None
                    st.session_state.hedef_scroll = "acik-kitap-alani"

                def _pdf_num_degisti(maks_sayfa=toplam_sayfa):
                    secilen = st.session_state.get("pdf_num_top", st.session_state.pdf_sayfa_no)
                    _pdf_sayfa_git(secilen, maks_sayfa)
                
                st.markdown("<div id='acik-kitap-alani'></div>", unsafe_allow_html=True)
                st.markdown("---")
                
                # Mobil Uyumlu Kompakt Açık Kaynak Başlık Kartı (Soft Pastel Ton)
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%); color: #312e81; border: 1.5px solid #c7d2fe; border-radius: 16px; padding: 12px 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <div style="font-size: 14.5px; font-weight: 800; line-height: 1.35; flex: 1; color: #312e81;">📖 {aktif_pdf.stem}</div>
                    <span style="background: #6366f1; color: white; font-size: 12.5px; font-weight: 800; padding: 4px 12px; border-radius: 99px; white-space: nowrap;">
                        Sayfa {st.session_state.pdf_sayfa_no} / {toplam_sayfa}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                # Üst Sayfa Geçiş Çubuğu (Mobilde Tek Satırda Yan Yana Kalır)
                nav1, nav2, nav3 = st.columns([1.1, 1, 1.1], gap="small")
                with nav1:
                    st.button(
                        "⬅️ Önceki",
                        key="pdf_prev_top",
                        use_container_width=True,
                        disabled=(st.session_state.pdf_sayfa_no <= 1),
                        on_click=_pdf_sayfa_git,
                        args=(st.session_state.pdf_sayfa_no - 1, toplam_sayfa),
                    )
                with nav2:
                    st.number_input(
                        "Sayfa",
                        min_value=1,
                        max_value=toplam_sayfa,
                        label_visibility="collapsed",
                        key="pdf_num_top",
                        on_change=_pdf_num_degisti,
                        args=(toplam_sayfa,),
                    )
                with nav3:
                    st.button(
                        "Sonraki ➡️",
                        key="pdf_next_top",
                        use_container_width=True,
                        disabled=(st.session_state.pdf_sayfa_no >= toplam_sayfa),
                        on_click=_pdf_sayfa_git,
                        args=(st.session_state.pdf_sayfa_no + 1, toplam_sayfa),
                    )
                
                # Aktif Sayfayı Yüksek Çözünürlüklü Görsel Olarak Göster
                sayfa_index = st.session_state.pdf_sayfa_no - 1
                page = doc.load_page(sayfa_index)
                pix = page.get_pixmap(dpi=150)
                sayfa_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                st.image(sayfa_img, use_container_width=True)
                
                # Alt Hızlı Sayfa Geçiş + PDF İndir Çubuğu (Mobilde Tek Satırda Yan Yana)
                b_nav1, b_nav2, b_nav3 = st.columns([1, 1.1, 1], gap="small")
                with b_nav1:
                    st.button(
                        "⬅️ Önceki",
                        key="pdf_prev_bot",
                        use_container_width=True,
                        disabled=(st.session_state.pdf_sayfa_no <= 1),
                        on_click=_pdf_sayfa_git,
                        args=(st.session_state.pdf_sayfa_no - 1, toplam_sayfa),
                    )
                with b_nav2:
                    with open(aktif_pdf, "rb") as f_dl:
                        st.download_button("📥 PDF İndir", data=f_dl, file_name=aktif_pdf.name, mime="application/pdf", use_container_width=True)
                with b_nav3:
                    st.button(
                        "Sonraki ➡️",
                        key="pdf_next_bot",
                        use_container_width=True,
                        disabled=(st.session_state.pdf_sayfa_no >= toplam_sayfa),
                        on_click=_pdf_sayfa_git,
                        args=(st.session_state.pdf_sayfa_no + 1, toplam_sayfa),
                    )
                
                # Bu Sayfa Üzerinde İnteraktif Yapay Zeka İşlemleri (Tam Genişlik Mobil Uyumlu)
                st.markdown("#### 🎮 Bu Sayfayla Ne Yapmak İstersin?")
                b_coz, b_ikiz, b_ozet = st.columns(3, gap="small")
                with b_coz:
                    if st.button("🧠 Soruları İnteraktif Çöz", key="act_coz", use_container_width=True):
                        with st.spinner(f"Sayfa {st.session_state.pdf_sayfa_no} inceleniyor, adım adım çözüm kartları hazırlanıyor..."):
                            st.session_state.pdf_cozum_kartlari = solve_page_questions_structured(sayfa_img)
                            st.session_state.pdf_ikiz_quiz = None
                            st.session_state.pdf_ozet_kart = None
                            st.session_state.hedef_scroll = "pdf-aksiyon-sonuc"
                with b_ikiz:
                    if st.button("🎯 İkiz Soru Meydan Okuması", key="act_ikiz", use_container_width=True):
                        with st.spinner("Bu sayfadaki soruların MEB ikizleri hazırlanıyor..."):
                            st.session_state.pdf_ikiz_quiz = generate_lgs_quiz_list(image=sayfa_img)
                            st.session_state.pdf_cozum_kartlari = None
                            st.session_state.pdf_ozet_kart = None
                            st.session_state.hedef_scroll = "pdf-aksiyon-sonuc"
                with b_ozet:
                    if st.button("🚀 Sayfayı Hap Özetle", key="act_ozet", use_container_width=True):
                        with st.spinner("Sayfadaki kazanımlar infografik özete dönüştürülüyor..."):
                            st.session_state.pdf_ozet_kart = generate_hap_ozet_structured(image=sayfa_img)
                            st.session_state.pdf_cozum_kartlari = None
                            st.session_state.pdf_ikiz_quiz = None
                            st.session_state.hedef_scroll = "pdf-aksiyon-sonuc"
                
                st.markdown("<div id='pdf-aksiyon-sonuc'></div>", unsafe_allow_html=True)
            
                # 1) İNTERAKTİF ADIM ADIM SORU ÇÖZÜM KARTLARI (OPTİK FORM MANTIĞI: İşaretle -> Bitir ve Gönder -> Doğru/Yanlış ve Çözümler)
                if st.session_state.get("pdf_cozum_kartlari"):
                    st.markdown("---")
                    st.markdown("#### 🧩 İnteraktif Soru Çözüm İstasyonu *(Şıkları işaretle, en altta '🏁 Testi Bitir ve Gönder'e basınca doğru/yanlışlar ve çözümler açılsın!)*")
                    cozum_json = json.dumps(st.session_state.pdf_cozum_kartlari, ensure_ascii=False)
                    cozum_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; }}
                        .sol-wrap {{ font-family: 'Inter', -apple-system, sans-serif; padding: 4px 2px; display: flex; flex-direction: column; gap: 14px; }}
                        .sol-scorebar {{
                            background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            position: sticky;
                            top: 0;
                            z-index: 10;
                        }}
                        .sol-card {{
                            background: white;
                            border: 2px solid #e0e7ff;
                            border-radius: 18px;
                            padding: 16px;
                            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.06);
                        }}
                        .sol-header {{
                            display: flex;
                            align-items: stretch;
                            gap: 10px;
                            margin-bottom: 12px;
                        }}
                        .sol-num {{
                            background: linear-gradient(90deg, #2563eb, #7c3aed);
                            color: white;
                            font-weight: 800;
                            font-size: 13px;
                            padding: 8px 10px;
                            border-radius: 12px;
                            white-space: nowrap;
                            flex: 0 0 104px;
                            width: 104px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                            box-shadow: 0 3px 8px rgba(37, 99, 235, 0.18);
                        }}
                        .sol-kazanim {{
                            background: #eff6ff;
                            border: 1.5px solid #bfdbfe;
                            color: #1d4ed8;
                            font-size: 12.5px;
                            font-weight: 700;
                            padding: 8px 12px;
                            border-radius: 12px;
                            flex: 1 1 auto;
                            min-width: 0;
                            line-height: 1.35;
                            display: flex;
                            align-items: center;
                            text-align: left;
                            word-break: break-word;
                        }}
                        .sol-pick-label {{
                            font-size: 12.5px;
                            font-weight: 700;
                            color: #475569;
                            margin-bottom: 8px;
                        }}
                        .sol-abcd-row {{
                            display: grid;
                            grid-template-columns: repeat(4, 1fr);
                            gap: 8px;
                            margin-bottom: 10px;
                        }}
                        .sol-sik-btn {{
                            background: #f8fafc;
                            border: 2px solid #cbd5e1;
                            border-radius: 12px;
                            padding: 10px 0;
                            font-size: 14.5px;
                            font-weight: 800;
                            color: #1e293b;
                            cursor: pointer;
                            text-align: center;
                            transition: all 0.15s ease;
                        }}
                        .sol-sik-btn:hover {{ border-color: #3b82f6; background: #eff6ff; }}
                        .sol-sik-btn.selected {{
                            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
                            border-color: #1e3a8a !important;
                            color: #ffffff !important;
                            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
                        }}
                        .sol-sik-btn.correct {{
                            background: #dcfce7 !important;
                            border-color: #16a34a !important;
                            color: #14532d !important;
                        }}
                        .sol-sik-btn.wrong {{
                            background: #fee2e2 !important;
                            border-color: #dc2626 !important;
                            color: #7f1d1d !important;
                        }}
                        .sol-status {{
                            display: none;
                            padding: 9px 12px;
                            border-radius: 10px;
                            font-size: 13.5px;
                            font-weight: 800;
                            margin-bottom: 10px;
                            text-align: center;
                        }}
                        .sol-status.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .sol-status.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .sol-status.empty {{ background: #f1f5f9; color: #475569; border: 1.5px solid #cbd5e1; }}
                        .sol-btn-row {{
                            display: flex;
                            gap: 8px;
                            flex-wrap: wrap;
                            margin-bottom: 6px;
                        }}
                        .sol-action-btn {{
                            border: none;
                            padding: 10px 14px;
                            border-radius: 11px;
                            font-size: 13px;
                            font-weight: 800;
                            cursor: pointer;
                            flex: 1 1 190px;
                            width: 100%;
                            text-align: left;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        }}
                        .sol-action-btn::after {{ content: '▾'; font-size: 12px; opacity: 0.7; }}
                        .btn-hint {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
                        .btn-steps {{ background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; display: none; }}
                        .sol-submit-btn {{
                            background: linear-gradient(90deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            border-radius: 14px;
                            padding: 15px 20px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            width: 100%;
                            box-shadow: 0 6px 18px rgba(22, 163, 74, 0.25);
                            margin-top: 6px;
                        }}
                        .sol-submit-btn:hover {{ filter: brightness(0.96); }}
                        .sol-panel {{
                            display: none;
                            margin-top: 10px;
                            padding: 14px;
                            border-radius: 12px;
                            font-size: 14px;
                            line-height: 1.5;
                        }}
                        .panel-hint {{ background: #fffbeb; border-left: 5px solid #f59e0b; color: #78350f; }}
                        .panel-steps {{ background: #f8fafc; border-left: 5px solid #4f46e5; color: #1e293b; }}
                        .step-item {{
                            padding: 8px 10px;
                            margin-bottom: 6px;
                            background: white;
                            border-radius: 8px;
                            border: 1px solid #e2e8f0;
                            font-weight: 600;
                        }}
                    </style>
                    <div class="sol-wrap">
                        <div class="sol-scorebar" id="sol-top-bar">
                            <span>📝 Optik Cevap Formu</span>
                            <span id="sol-score-txt">İşaretlenen: 0 / {len(st.session_state.pdf_cozum_kartlari)}</span>
                        </div>
                        <div id="sol-root" style="display:flex; flex-direction:column; gap:14px;"></div>
                        <button class="sol-submit-btn" id="sol-submit-btn" onclick="submitPageOptik()">🏁 Testi Bitir ve Gönder (Cevapları Kontrol Et)</button>
                    </div>
                    <script>
                        const items = {cozum_json};
                        const root = document.getElementById('sol-root');
                        const userPicks = {{}};
                        let isSubmitted = false;

                        items.forEach((item, idx) => {{
                            const card = document.createElement('div');
                            card.className = 'sol-card';
                            const rawNo = String(item.soru_no || (idx + 1)).trim();
                            const numMatch = rawNo.match(/\\d+/);
                            const stdSoruNo = numMatch ? ('Soru ' + numMatch[0]) : rawNo;
                            const rawAns = String(item.dogru_sik || 'A').trim().toUpperCase();
                            const ansMatch = rawAns.match(/[ABCD]/);
                            const cleanAns = ansMatch ? ansMatch[0] : 'A';
                            item._cleanAns = cleanAns;
                            const stepsHtml = (item.adimlar || []).map(s => `<div class="step-item">👉 ${{s}}</div>`).join('');
                            const sikBtns = ['A', 'B', 'C', 'D'].map(harf =>
                                `<button class="sol-sik-btn" id="sik-${{idx}}-${{harf}}" onclick="pickSik(${{idx}}, '${{harf}}')">${{harf}}</button>`
                            ).join('');

                            card.innerHTML = `
                                <div class="sol-header">
                                    <span class="sol-num">📌 ${{stdSoruNo}}</span>
                                    <span class="sol-kazanim">🎯 ${{item.kazanim || 'LGS Kazanımı'}}</span>
                                </div>
                                <div class="sol-pick-label" id="lbl-${{idx}}">👇 Cevabını işaretle:</div>
                                <div class="sol-abcd-row">${{sikBtns}}</div>
                                <div class="sol-status" id="st-${{idx}}"></div>
                                <div class="sol-btn-row">
                                    <button class="sol-action-btn btn-hint" onclick="toggleP('sh-${{idx}}')"><span>💡 İpucunu Göster</span></button>
                                    <button class="sol-action-btn btn-steps" id="btn-ss-${{idx}}" onclick="toggleP('ss-${{idx}}')"><span>👣 Adım Adım Çözümü Gör</span></button>
                                </div>
                                <div class="sol-panel panel-hint" id="sh-${{idx}}"><b>💡 Püf Nokta:</b> ${{item.ipucu || ''}}</div>
                                <div class="sol-panel panel-steps" id="ss-${{idx}}">${{stepsHtml}}</div>
                            `;
                            root.appendChild(card);
                        }});

                        window.pickSik = function(idx, secilen) {{
                            if (isSubmitted) return;
                            userPicks[idx] = secilen;
                            ['A', 'B', 'C', 'D'].forEach(h => {{
                                const b = document.getElementById(`sik-${{idx}}-${{h}}`);
                                if (b) {{
                                    b.classList.remove('selected');
                                    b.innerText = h;
                                }}
                            }});
                            const activeBtn = document.getElementById(`sik-${{idx}}-${{secilen}}`);
                            if (activeBtn) {{
                                activeBtn.classList.add('selected');
                                activeBtn.innerText = secilen + ' ✓';
                            }}
                            const count = Object.keys(userPicks).length;
                            document.getElementById('sol-score-txt').innerText = `İşaretlenen: ${{count}} / ${{items.length}}`;
                        }};

                        window.submitPageOptik = function() {{
                            if (isSubmitted) return;
                            isSubmitted = true;
                            let dCount = 0;
                            let yCount = 0;
                            let bCount = 0;

                            items.forEach((item, idx) => {{
                                const dogru = item._cleanAns;
                                const secilen = userPicks[idx];
                                const stBox = document.getElementById(`st-${{idx}}`);
                                const stepBtn = document.getElementById(`btn-ss-${{idx}}`);
                                const dogruBtn = document.getElementById(`sik-${{idx}}-${{dogru}}`);

                                ['A', 'B', 'C', 'D'].forEach(h => {{
                                    const b = document.getElementById(`sik-${{idx}}-${{h}}`);
                                    if (b) b.classList.remove('selected');
                                }});

                                if (!secilen) {{
                                    bCount++;
                                    if (dogruBtn) {{
                                        dogruBtn.classList.add('correct');
                                        dogruBtn.innerText = dogru + ' ✔️';
                                    }}
                                    stBox.className = 'sol-status empty';
                                    stBox.innerHTML = `⭕ <b>BOŞ BIRAKILDI</b> &nbsp;|&nbsp; Doğru Cevap: <b>${{dogru}}</b>`;
                                }} else if (secilen === dogru) {{
                                    dCount++;
                                    const secBtn = document.getElementById(`sik-${{idx}}-${{secilen}}`);
                                    secBtn.classList.add('correct');
                                    secBtn.innerText = secilen + ' ✅';
                                    stBox.className = 'sol-status ok';
                                    stBox.innerHTML = `🎉 <b>DOĞRU!</b> (${{dogru}} şıkkı)`;
                                }} else {{
                                    yCount++;
                                    const secBtn = document.getElementById(`sik-${{idx}}-${{secilen}}`);
                                    secBtn.classList.add('wrong');
                                    secBtn.innerText = secilen + ' ❌';
                                    if (dogruBtn) {{
                                        dogruBtn.classList.add('correct');
                                        dogruBtn.innerText = dogru + ' ✔️';
                                    }}
                                    stBox.className = 'sol-status err';
                                    stBox.innerHTML = `❌ <b>YANLIŞ!</b> Senin Cevabın: <b>${{secilen}}</b> &nbsp;|&nbsp; Doğru Cevap: <b>${{dogru}}</b>`;
                                }}
                                stBox.style.display = 'block';
                                stepBtn.style.display = 'flex';
                            }});

                            document.getElementById('sol-score-txt').innerHTML = `✅ Doğru: ${{dCount}} &nbsp;|&nbsp; ❌ Yanlış: ${{yCount}} &nbsp;|&nbsp; ⭕ Boş: ${{bCount}}`;
                            const subBtn = document.getElementById('sol-submit-btn');
                            subBtn.innerHTML = `🏆 Sonuç: ${{dCount}} Doğru, ${{yCount}} Yanlış, ${{bCount}} Boş (Çözümler Açıldı!)`;
                            subBtn.style.background = 'linear-gradient(90deg, #2563eb 0%, #7c3aed 100%)';
                            document.getElementById('sol-top-bar').scrollIntoView({{ behavior: 'smooth' }});
                        }};

                        window.toggleP = function(id) {{
                            const el = document.getElementById(id);
                            el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                        }};
                    </script>
                    """
                    components.html(cozum_html, height=min(820, len(st.session_state.pdf_cozum_kartlari) * 290 + 110), scrolling=True)

                # 2) BU SAYFADAN İNTERAKTİF İKİZ SORU MEYDAN OKUMASI (OPTİK MANTIĞI)
                if st.session_state.get("pdf_ikiz_quiz"):
                    st.markdown("---")
                    st.markdown("#### 🎯 Bu Sayfanın İkiz Soru Arenası *(Şıkları işaretle, en altta '🏁 Testi Bitir ve Gönder'e bas!)*")
                    q_data = st.session_state.pdf_ikiz_quiz
                    q_json = json.dumps(q_data, ensure_ascii=False)
                    ikiz_html = f"""
                    <style>
                        .q-container {{ font-family: 'Inter', sans-serif; padding: 4px; }}
                        .q-scorebar {{
                            background: linear-gradient(90deg, #4f46e5 0%, #9333ea 100%);
                            color: white; padding: 12px 18px; border-radius: 14px;
                            font-weight: 800; font-size: 14px; margin-bottom: 16px;
                            display: flex; justify-content: space-between;
                        }}
                        .q-card {{
                            background: #ffffff; border: 2px solid #e2e8f0; border-radius: 18px;
                            padding: 18px; margin-bottom: 18px; box-shadow: 0 6px 16px rgba(0,0,0,0.04);
                        }}
                        .q-badge {{
                            display: inline-block; background: #dbeafe; color: #1d4ed8;
                            font-weight: 800; font-size: 12px; padding: 4px 10px; border-radius: 8px; margin-bottom: 10px;
                        }}
                        .q-text {{ font-size: 15px; font-weight: 700; color: #1e293b; line-height: 1.5; margin-bottom: 14px; }}
                        .q-options {{ display: flex; flex-direction: column; gap: 8px; }}
                        .q-opt {{
                            background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 12px;
                            padding: 11px 14px; font-size: 14px; font-weight: 700; color: #334155;
                            cursor: pointer; text-align: left;
                        }}
                        .q-opt.selected {{
                            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
                            border-color: #1e3a8a !important;
                            color: #ffffff !important;
                        }}
                        .q-opt.correct {{ background: #dcfce7 !important; border-color: #16a34a !important; color: #14532d !important; }}
                        .q-opt.wrong {{ background: #fee2e2 !important; border-color: #dc2626 !important; color: #7f1d1d !important; }}
                        .q-actions {{ display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }}
                        .q-btn-small {{
                            background: #fef3c7; border: 1px solid #fde68a; padding: 9px 14px; border-radius: 10px;
                            font-size: 13px; font-weight: 800; color: #92400e; cursor: pointer;
                        }}
                        .q-btn-sol {{
                            background: #e0e7ff; border: 1px solid #c7d2fe; padding: 9px 14px; border-radius: 10px;
                            font-size: 13px; font-weight: 800; color: #3730a3; cursor: pointer; display: none;
                        }}
                        .q-submit {{
                            background: linear-gradient(90deg, #16a34a 0%, #059669 100%);
                            color: white; border: none; border-radius: 14px; padding: 14px 20px;
                            font-size: 15px; font-weight: 900; width: 100%; cursor: pointer;
                        }}
                        .q-box {{ display: none; margin-top: 10px; padding: 12px; border-radius: 12px; font-size: 13.5px; }}
                        .q-hint-box {{ background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }}
                        .q-sol-box {{ background: #f0fdf4; color: #166534; border: 1px solid #86efac; }}
                    </style>
                    <div class="q-container">
                        <div class="q-scorebar" id="p-top-bar">
                            <span>⚡ İkiz Soru Meydan Okuması</span>
                            <span id="p-score">İşaretlenen: 0 / {len(q_data)}</span>
                        </div>
                        <div id="p-quiz-root"></div>
                        <button class="q-submit" id="p-sub-btn" onclick="subPQuiz()">🏁 Testi Bitir ve Gönder</button>
                    </div>
                    <script>
                        const qs = {q_json};
                        const picks = {{}};
                        let done = false;
                        const rt = document.getElementById('p-quiz-root');
                        qs.forEach((q, qIdx) => {{
                            const card = document.createElement('div');
                            card.className = 'q-card';
                            const opts = (q.secenekler || []).map((opt, oIdx) =>
                                `<button class="q-opt" id="popt-${{qIdx}}-${{oIdx}}" onclick="selPOpt(${{qIdx}}, ${{oIdx}})">${{opt}}</button>`
                            ).join('');
                            card.innerHTML = `
                                <div class="q-badge">🔥 İkiz Soru ${{qIdx + 1}}</div>
                                <div class="q-text">${{q.soru}}</div>
                                <div class="q-options">${{opts}}</div>
                                <div class="q-actions">
                                    <button class="q-btn-small" onclick="togPBox('phint-${{qIdx}}')">💡 İpucu Al</button>
                                    <button class="q-btn-sol" id="pbtn-sol-${{qIdx}}" onclick="togPBox('psol-${{qIdx}}')">📖 Çözümü Gör</button>
                                </div>
                                <div class="q-box q-hint-box" id="phint-${{qIdx}}"><b>💡 İpucu:</b> ${{q.ipucu || ''}}</div>
                                <div class="q-box q-sol-box" id="psol-${{qIdx}}"><b>✅ Çözüm:</b> ${{q.cozum || ''}}</div>
                            `;
                            rt.appendChild(card);
                        }});
                        window.selPOpt = function(qIdx, oIdx) {{
                            if (done) return;
                            picks[qIdx] = oIdx;
                            (qs[qIdx].secenekler || []).forEach((_, idx) => {{
                                const b = document.getElementById(`popt-${{qIdx}}-${{idx}}`);
                                if (b) b.classList.remove('selected');
                            }});
                            const cur = document.getElementById(`popt-${{qIdx}}-${{oIdx}}`);
                            if (cur) cur.classList.add('selected');
                            document.getElementById('p-score').innerText = `İşaretlenen: ${{Object.keys(picks).length}} / ${{qs.length}}`;
                        }};
                        window.subPQuiz = function() {{
                            if (done) return;
                            done = true;
                            let scD = 0, scY = 0, scB = 0;
                            qs.forEach((q, qIdx) => {{
                                const cIdx = q.dogru_index || 0;
                                const uIdx = picks[qIdx];
                                const cBtn = document.getElementById(`popt-${{qIdx}}-${{cIdx}}`);
                                const solBtn = document.getElementById(`pbtn-sol-${{qIdx}}`);
                                (q.secenekler || []).forEach((_, idx) => {{
                                    const b = document.getElementById(`popt-${{qIdx}}-${{idx}}`);
                                    if (b) b.classList.remove('selected');
                                }});
                                if (uIdx === undefined) {{
                                    scB++;
                                    if (cBtn) {{ cBtn.classList.add('correct'); cBtn.innerHTML += ' &nbsp; ✔️ <b>Doğru Cevap</b>'; }}
                                }} else if (uIdx === cIdx) {{
                                    scD++;
                                    const uBtn = document.getElementById(`popt-${{qIdx}}-${{uIdx}}`);
                                    if (uBtn) {{ uBtn.classList.add('correct'); uBtn.innerHTML += ' &nbsp; ✅ <b>DOĞRU!</b>'; }}
                                }} else {{
                                    scY++;
                                    const uBtn = document.getElementById(`popt-${{qIdx}}-${{uIdx}}`);
                                    if (uBtn) {{ uBtn.classList.add('wrong'); uBtn.innerHTML += ' &nbsp; ❌ <b>YANLIŞ!</b>'; }}
                                    if (cBtn) {{ cBtn.classList.add('correct'); cBtn.innerHTML += ' &nbsp; ✔️ <b>Doğru Cevap</b>'; }}
                                }}
                                if (solBtn) solBtn.style.display = 'inline-block';
                            }});
                            document.getElementById('p-score').innerHTML = `✅ Doğru: ${{scD}} | ❌ Yanlış: ${{scY}} | ⭕ Boş: ${{scB}}`;
                            const sb = document.getElementById('p-sub-btn');
                            sb.innerHTML = `🏆 Sonuç: ${{scD}} Doğru, ${{scY}} Yanlış, ${{scB}} Boş (Çözümler Açıldı!)`;
                            sb.style.background = 'linear-gradient(90deg, #2563eb 0%, #7c3aed 100%)';
                        }};
                        window.togPBox = function(id) {{
                            const el = document.getElementById(id);
                            el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                        }};
                    </script>
                    """
                    components.html(ikiz_html, height=len(q_data) * 350 + 120, scrolling=True)

                # 3) BU SAYFANIN İNFOGRAFİK HAP ÖZETİ
                if st.session_state.get("pdf_ozet_kart"):
                    ozet_d = st.session_state.pdf_ozet_kart
                    st.markdown("---")
                    baslik_str = str(ozet_d.get("baslik", "Sayfa Özeti")).replace("<", "&lt;").replace(">", "&gt;")
                    taktik_str = str(ozet_d.get("altin_taktik", "")).replace("<", "&lt;").replace(">", "&gt;")
                    p_ozet_html = f"""
                    <style>
                        .ozet-wrap {{ font-family: 'Inter', sans-serif; padding: 6px 2px; }}
                        .ozet-title {{
                            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                            color: white; padding: 16px 20px; border-radius: 16px;
                            font-size: 18px; font-weight: 800; margin-bottom: 14px;
                        }}
                        .ozet-grid {{ display: flex; flex-direction: column; gap: 12px; }}
                        .ozet-item {{
                            background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
                            border-left: 6px solid #4f46e5; border-radius: 14px; padding: 16px;
                            cursor: pointer;
                        }}
                        .ozet-item-head {{ font-size: 15px; font-weight: 800; color: #1e1b4b; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }}
                        .ozet-item-body {{ font-size: 14px; color: #334155; line-height: 1.5; font-weight: 500; }}
                        .taktik-box {{
                            margin-top: 16px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                            border: 2px dashed #d97706; border-radius: 16px; padding: 16px; color: #78350f;
                        }}
                    </style>
                    <div class="ozet-wrap">
                        <div class="ozet-title">🚀 {baslik_str}</div>
                        <div class="ozet-grid">
                    """
                    for m in ozet_d.get("maddeler", []):
                        em = str(m.get("emoji", "⚡"))
                        mb = str(m.get("baslik", "")).replace("<", "&lt;").replace(">", "&gt;")
                        md = str(m.get("detay", "")).replace("<", "&lt;").replace(">", "&gt;")
                        p_ozet_html += f"""
                        <div class="ozet-item" onclick="this.style.borderLeftColor='#10b981'; this.style.background='#ecfdf5';">
                            <div class="ozet-item-head"><span>{em}</span> {mb} <span style="margin-left:auto; font-size:11px; color:#6366f1;">(Anladım ✓ tıkla)</span></div>
                            <div class="ozet-item-body">{md}</div>
                        </div>
                        """
                    p_ozet_html += f"""
                        </div>
                        <div class="taktik-box">
                            <div style="font-weight:900; font-size:14px;">🏆 BU SAYFANIN ALTIN TAKTİĞİ</div>
                            <div style="font-weight:700; font-size:14.5px; margin-top:4px;">{taktik_str}</div>
                        </div>
                    </div>
                    """
                    components.html(p_ozet_html, height=430, scrolling=True)
                doc.close()

elif menu == "⚡ Hızlı Öğren (Video/Kaynak)":
    st.markdown("<div class='karargah-card'>", unsafe_allow_html=True)
    st.markdown("### ⚡ Hızlı Öğren & Kaynak İstasyonu")
    st.write("Konu başlığı yazarak, YouTube video linki yapıştırarak veya PDF yükleyerek anında özet, flashcard ve soru üretebilirsin!")
    
    secim_turu = st.radio("Kaynak Türü", ["Konu / Metin Yaz", "YouTube Video Linki", "PDF / Ders Notu"], horizontal=True)
    
    kaynak_metni = ""
    
    if secim_turu == "Konu / Metin Yaz":
        kaynak_metni = st.text_input("Çalışılacak Konu veya Metin (Örn: Katı Basıncı, DNA ve Genetik Kod, Fiilimsiler):")
    elif secim_turu == "YouTube Video Linki":
        video_url = st.text_input("YouTube Ders Videosu Linkini Yapıştır (Örn: https://youtu.be/...)")
        if video_url:
            if st.session_state.get("cached_video_url") != video_url:
                with st.spinner("Video metni okunuyor..."):
                    st.session_state.cached_video_text = get_youtube_transcript(video_url)
                    st.session_state.cached_video_url = video_url
            kaynak_metni = st.session_state.get("cached_video_text", "")
            if kaynak_metni:
                st.success("Video başarıyla okundu ve metne dönüştürüldü!")
            else:
                st.warning("Bu videonun altyazısı kapalı olduğu için video linki üzerinden doğrudan konu analizi yapılacak.")
                kaynak_metni = f"YouTube LGS ders videosu ({video_url})"
    else:
        pdf_dosya = st.file_uploader("Çalışılacak PDF veya Not Yükle", type=["pdf"])
        if pdf_dosya:
            if st.session_state.get("cached_pdf_name") != pdf_dosya.name:
                reader = pypdf.PdfReader(pdf_dosya)
                kaynak_metni = "".join([p.extract_text() or "" for p in reader.pages[:10]])
                st.session_state.cached_pdf_text = kaynak_metni
                st.session_state.cached_pdf_name = pdf_dosya.name
            kaynak_metni = st.session_state.get("cached_pdf_text", "")
            if not kaynak_metni.strip():
                st.warning("Bu PDF taranmış resimlerden oluşuyor, dosya adına göre içerik üretilecek.")
                kaynak_metni = pdf_dosya.name
            else:
                st.success("PDF başarıyla yüklendi ve okundu!")
            
    if kaynak_metni:
        st.markdown("---")
        st.markdown("### 🎯 Bu Kaynaktan Ne Üretmek İstersin?")
        
        col_b1, col_b2, col_b3 = st.columns(3, gap="small")
        with col_b1:
            if st.button("🎧 Hap Özet & Ses", use_container_width=True):
                with st.spinner("İnfografik Hap Özet ve Podcast hazırlanıyor..."):
                    ozet_data = generate_hap_ozet_structured(kaynak_metni)
                    st.session_state.hizli_ozet_data = ozet_data
                    st.session_state.hizli_flashcards = None
                    st.session_state.hizli_quiz = None
                    ses_metni = ozet_data.get("ses_metni") or " ".join([m.get("detay", "") for m in ozet_data.get("maddeler", [])])
                    tts = gTTS(text=ses_metni, lang='tr')
                    tts.save("hapis_ozet.mp3")
                    st.session_state.hizli_ses = "hapis_ozet.mp3"
                    st.session_state.hedef_scroll = "hizli-ogren-sonuc"
        with col_b2:
            if st.button("📇 Flashcard Üret", use_container_width=True):
                with st.spinner("İnteraktif Flashcard kartları tasarlanıyor..."):
                    st.session_state.hizli_flashcards = generate_flashcards_list(kaynak_metni)
                    st.session_state.hizli_ozet_data = None
                    st.session_state.hizli_quiz = None
                    st.session_state.hizli_ses = None
                    st.session_state.hedef_scroll = "hizli-ogren-sonuc"
        with col_b3:
            if st.button("📝 LGS Sorusu Üret", use_container_width=True):
                with st.spinner("İnteraktif LGS Mini Yarışması hazırlanıyor..."):
                    st.session_state.hizli_quiz = generate_lgs_quiz_list(kaynak_metni)
                    st.session_state.hizli_ozet_data = None
                    st.session_state.hizli_flashcards = None
                    st.session_state.hizli_ses = None
                    st.session_state.hedef_scroll = "hizli-ogren-sonuc"
        
        st.markdown("<div id='hizli-ogren-sonuc'></div>", unsafe_allow_html=True)

        # 1. İNFOGRAFİK HAP ÖZET GÖRÜNÜMÜ
        if st.session_state.get("hizli_ozet_data"):
            ozet_d = st.session_state.hizli_ozet_data
            st.markdown("---")
            if st.session_state.get("hizli_ses"):
                st.markdown("#### 🎙️ Podcast Modu *(Arkanı yaslan ve dinle!)*")
                st.audio(st.session_state.hizli_ses)
            
            baslik_str = str(ozet_d.get("baslik", "Hap Özet")).replace("<", "&lt;").replace(">", "&gt;")
            taktik_str = str(ozet_d.get("altin_taktik", "")).replace("<", "&lt;").replace(">", "&gt;")
            
            ozet_html = f"""
            <style>
                .ozet-wrap {{ font-family: 'Inter', sans-serif; padding: 6px 2px; }}
                .ozet-title {{
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    color: white;
                    padding: 16px 20px;
                    border-radius: 16px;
                    font-size: 18px;
                    font-weight: 800;
                    margin-bottom: 14px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .ozet-grid {{ display: flex; flex-direction: column; gap: 12px; }}
                .ozet-item {{
                    background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
                    border-left: 6px solid #4f46e5;
                    border-radius: 14px;
                    padding: 16px;
                    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08);
                    transition: transform 0.2s ease;
                    cursor: pointer;
                }}
                .ozet-item:hover {{ transform: translateX(4px); }}
                .ozet-item-head {{
                    font-size: 15px;
                    font-weight: 800;
                    color: #1e1b4b;
                    margin-bottom: 6px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .ozet-item-body {{
                    font-size: 14px;
                    color: #334155;
                    line-height: 1.5;
                    font-weight: 500;
                }}
                .taktik-box {{
                    margin-top: 16px;
                    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                    border: 2px dashed #d97706;
                    border-radius: 16px;
                    padding: 16px;
                    color: #78350f;
                }}
                .taktik-title {{ font-weight: 900; font-size: 14px; text-transform: uppercase; margin-bottom: 4px; }}
                .taktik-text {{ font-weight: 700; font-size: 14.5px; }}
            </style>
            <div class="ozet-wrap">
                <div class="ozet-title">🚀 {baslik_str}</div>
                <div class="ozet-grid">
            """
            for m in ozet_d.get("maddeler", []):
                em = str(m.get("emoji", "⚡"))
                mb = str(m.get("baslik", "")).replace("<", "&lt;").replace(">", "&gt;")
                md = str(m.get("detay", "")).replace("<", "&lt;").replace(">", "&gt;")
                ozet_html += f"""
                <div class="ozet-item" onclick="this.style.borderLeftColor='#10b981'; this.style.background='#ecfdf5';">
                    <div class="ozet-item-head"><span>{em}</span> {mb} <span style="margin-left:auto; font-size:11px; color:#6366f1;">(Okudum ✓ tıkla)</span></div>
                    <div class="ozet-item-body">{md}</div>
                </div>
                """
            ozet_html += f"""
                </div>
                <div class="taktik-box">
                    <div class="taktik-title">🏆 LGS Altın Taktik</div>
                    <div class="taktik-text">{taktik_str}</div>
                </div>
            </div>
            """
            components.html(ozet_html, height=440, scrolling=True)

        # 2. İNTERAKTİF 3D FLASHCARD GÖRÜNÜMÜ
        if st.session_state.get("hizli_flashcards"):
            st.markdown("---")
            st.markdown("#### 🎴 İnteraktif Flashcard'lar *(Cevabı görmek için kartın üzerine tıkla!)*")
            cards_data = st.session_state.hizli_flashcards
            cards_html = """
            <style>
                .fc-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                    gap: 18px;
                    font-family: 'Inter', sans-serif;
                    padding: 8px 4px;
                }
                .fc-card {
                    background-color: transparent;
                    height: 210px;
                    perspective: 1000px;
                    cursor: pointer;
                }
                .fc-inner {
                    position: relative;
                    width: 100%;
                    height: 100%;
                    text-align: center;
                    transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1);
                    transform-style: preserve-3d;
                    border-radius: 18px;
                    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
                }
                .fc-card.flipped .fc-inner {
                    transform: rotateY(180deg);
                }
                .fc-front, .fc-back {
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    box-sizing: border-box;
                    padding: 20px;
                    -webkit-backface-visibility: hidden;
                    backface-visibility: hidden;
                    border-radius: 18px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .fc-front {
                    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                    color: white;
                }
                .fc-back {
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    transform: rotateY(180deg);
                }
                .fc-badge {
                    font-size: 11px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 10px;
                    border-radius: 99px;
                    margin-bottom: 12px;
                }
                .fc-text {
                    font-size: 15px;
                    font-weight: 600;
                    line-height: 1.45;
                    overflow-y: auto;
                }
                .fc-hint {
                    margin-top: 12px;
                    font-size: 11px;
                    opacity: 0.8;
                }
            </style>
            <div class="fc-grid">
            """
            for idx, item in enumerate(cards_data, 1):
                soru_txt = str(item.get("soru", "")).replace('"', '&quot;').replace("<", "&lt;").replace(">", "&gt;")
                cevap_txt = str(item.get("cevap", "")).replace('"', '&quot;').replace("<", "&lt;").replace(">", "&gt;")
                cards_html += f"""
                <div class="fc-card" onclick="this.classList.toggle('flipped')">
                    <div class="fc-inner">
                        <div class="fc-front">
                            <div class="fc-badge">❓ Kart {idx} - Soru</div>
                            <div class="fc-text">{soru_txt}</div>
                            <div class="fc-hint">🔄 Çevirmek için tıkla</div>
                        </div>
                        <div class="fc-back">
                            <div class="fc-badge">✅ Kart {idx} - Cevap</div>
                            <div class="fc-text">{cevap_txt}</div>
                            <div class="fc-hint">🔄 Soruya dönmek için tıkla</div>
                        </div>
                    </div>
                </div>
                """
            cards_html += "</div>"
            rows = (len(cards_data) + 1) // 2
            components.html(cards_html, height=rows * 235 + 20, scrolling=True)

        # 3. İNTERAKTİF LGS SORU ARENASI (TIKLAMALI ŞIKLAR, İPUCU VE ANINDA KONTROL)
        if st.session_state.get("hizli_quiz"):
            st.markdown("---")
            st.markdown("#### 🎮 LGS Mini Soru Arenası *(Şıklara tıkla, kendini dene!)*")
            quiz_data = st.session_state.hizli_quiz
            quiz_json_str = json.dumps(quiz_data, ensure_ascii=False)
            quiz_html = f"""
            <style>
                .q-container {{ font-family: 'Inter', sans-serif; padding: 4px; }}
                .q-scorebar {{
                    background: linear-gradient(90deg, #4f46e5 0%, #9333ea 100%);
                    color: white;
                    padding: 12px 18px;
                    border-radius: 14px;
                    font-weight: 800;
                    font-size: 14px;
                    margin-bottom: 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .q-card {{
                    background: #ffffff;
                    border: 2px solid #e2e8f0;
                    border-radius: 18px;
                    padding: 18px;
                    margin-bottom: 18px;
                    box-shadow: 0 6px 16px rgba(0,0,0,0.04);
                }}
                .q-badge {{
                    display: inline-block;
                    background: #dbeafe;
                    color: #1d4ed8;
                    font-weight: 800;
                    font-size: 12px;
                    padding: 4px 10px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                }}
                .q-text {{
                    font-size: 15px;
                    font-weight: 700;
                    color: #1e293b;
                    line-height: 1.5;
                    margin-bottom: 14px;
                }}
                .q-options {{ display: flex; flex-direction: column; gap: 8px; }}
                .q-opt {{
                    background: #f8fafc;
                    border: 2px solid #cbd5e1;
                    border-radius: 12px;
                    padding: 11px 14px;
                    font-size: 14px;
                    font-weight: 600;
                    color: #334155;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-align: left;
                }}
                .q-opt:hover {{ border-color: #6366f1; background: #eef2ff; }}
                .q-opt.correct {{
                    background: #dcfce7 !important;
                    border-color: #16a34a !important;
                    color: #14532d !important;
                }}
                .q-opt.wrong {{
                    background: #fee2e2 !important;
                    border-color: #dc2626 !important;
                    color: #7f1d1d !important;
                }}
                .q-actions {{
                    display: flex;
                    gap: 10px;
                    margin-top: 12px;
                }}
                .q-btn-small {{
                    background: #f1f5f9;
                    border: none;
                    padding: 7px 12px;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 700;
                    color: #475569;
                    cursor: pointer;
                }}
                .q-btn-small:hover {{ background: #e2e8f0; }}
                .q-btn-sol {{
                    background: #e0e7ff;
                    border: 1px solid #c7d2fe;
                    padding: 8px 14px;
                    border-radius: 8px;
                    font-size: 12.5px;
                    font-weight: 800;
                    color: #3730a3;
                    cursor: pointer;
                    display: none;
                }}
                .q-box {{
                    display: none;
                    margin-top: 10px;
                    padding: 12px;
                    border-radius: 12px;
                    font-size: 13.5px;
                    line-height: 1.45;
                }}
                .q-hint-box {{ background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }}
                .q-sol-box {{ background: #f0fdf4; color: #166534; border: 1px solid #86efac; }}
            </style>
            <div class="q-container">
                <div class="q-scorebar">
                    <span>🎯 LGS Mini Meydan Okuma</span>
                    <span id="score-text">✅ Doğru: 0 &nbsp;|&nbsp; ❌ Yanlış: 0</span>
                </div>
                <div id="quiz-root"></div>
            </div>
            <script>
                const questions = {quiz_json_str};
                let scoreD = 0;
                let scoreY = 0;
                const answered = new Set();
                const root = document.getElementById('quiz-root');

                questions.forEach((q, qIdx) => {{
                    const card = document.createElement('div');
                    card.className = 'q-card';
                    
                    let optsHtml = '';
                    (q.secenekler || []).forEach((opt, oIdx) => {{
                        optsHtml += `<button class="q-opt" id="opt-${{qIdx}}-${{oIdx}}" onclick="selectOpt(${{qIdx}}, ${{oIdx}}, ${{q.dogru_index || 0}})">${{opt}}</button>`;
                    }});

                    card.innerHTML = `
                        <div class="q-badge">🔥 Soru ${{qIdx + 1}}</div>
                        <div class="q-text">${{q.soru}}</div>
                        <div class="q-options">${{optsHtml}}</div>
                        <div class="q-actions">
                            <button class="q-btn-small" onclick="toggleBox('hint-${{qIdx}}')">💡 İpucu Al</button>
                            <button class="q-btn-sol" id="btn-sol-${{qIdx}}" onclick="toggleBox('sol-${{qIdx}}')">📖 Çözümü Gör</button>
                        </div>
                        <div class="q-box q-hint-box" id="hint-${{qIdx}}"><b>💡 İpucu:</b> ${{q.ipucu || 'Sorudaki anahtar kelimelere dikkat et!'}}</div>
                        <div class="q-box q-sol-box" id="sol-${{qIdx}}"><b>✅ Adım Adım Çözüm:</b> ${{q.cozum || ''}}</div>
                    `;
                    root.appendChild(card);
                }});

                window.selectOpt = function(qIdx, oIdx, correctIdx) {{
                    if (answered.has(qIdx)) return;
                    answered.add(qIdx);
                    const btn = document.getElementById(`opt-${{qIdx}}-${{oIdx}}`);
                    const cBtn = document.getElementById(`opt-${{qIdx}}-${{correctIdx}}`);
                    const solBtn = document.getElementById(`btn-sol-${{qIdx}}`);
                    if (oIdx === correctIdx) {{
                        btn.classList.add('correct');
                        btn.innerHTML += ' &nbsp; 🎉 <b>DOĞRU!</b>';
                        scoreD++;
                    }} else {{
                        btn.classList.add('wrong');
                        btn.innerHTML += ' &nbsp; ❌ <b>YANLIŞ!</b>';
                        if (cBtn) {{
                            cBtn.classList.add('correct');
                            cBtn.innerHTML += ' &nbsp; ✔️ <b>Doğru Cevap</b>';
                        }}
                        scoreY++;
                    }}
                    solBtn.style.display = 'inline-block';
                    document.getElementById('score-text').innerHTML = `✅ Doğru: ${{scoreD}} &nbsp;|&nbsp; ❌ Yanlış: ${{scoreY}}`;
                }};

                window.toggleBox = function(id) {{
                    const el = document.getElementById(id);
                    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                }};
            </script>
            """
            components.html(quiz_html, height=len(quiz_data) * 330 + 80, scrolling=True)
                    
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "🤖 Soru Çöz & İkiz":
    import fitz
    from pathlib import Path

    # Varsayılan SinoTest State'leri
    if "cipko_ana_mod" not in st.session_state:
        st.session_state.cipko_ana_mod = "hizli_test"  # hizli_test | kaynagimdan | fotograftan
    if "cipko_konu_mod" not in st.session_state:
        st.session_state.cipko_konu_mod = "sec"  # sec | yaz
    if "cipko_ders" not in st.session_state:
        st.session_state.cipko_ders = None
    if "cipko_konu" not in st.session_state:
        st.session_state.cipko_konu = None
    if "cipko_coklu_sec" not in st.session_state:
        st.session_state.cipko_coklu_sec = False
    if "cipko_turler" not in st.session_state:
        st.session_state.cipko_turler = ["Test Oluştur"]
    if "cipko_zorluk" not in st.session_state:
        st.session_state.cipko_zorluk = "Orta"
    if "cipko_soru_sayisi" not in st.session_state:
        st.session_state.cipko_soru_sayisi = 10
    if "ai_konu_havuzu" not in st.session_state:
        st.session_state.ai_konu_havuzu = {}

    DERS_LISTESI = ["Türkçe", "Matematik", "Fen Bilimleri", "İnkılap Tarihi", "İngilizce", "Din Kültürü"]
    CALISMA_TURLERI = [
        ("📝 Test Oluştur", "Test Oluştur"),
        ("🎴 Flash Kart", "Flash Kart"),
        ("✏️ Boşluk Doldur", "Boşluk Doldur"),
        ("✅ Doğru/Yanlış", "Doğru/Yanlış"),
        ("🧩 Eşleştir", "Eşleştir"),
        ("🔀 Karıştırma", "Karıştırma"),
    ]
    ZORLUK_LISTESI = ["Kolay", "Orta", "Zor"]
    ADET_LISTESI = [5, 10, 20]

    # SinoTest Özel Mobil Pill & Segmented Bar CSS
    st.markdown("""
    <style>
        /* Üst 3'lü Segmented Bar ve Alt Barlar Mobilde Yan Yana */
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tab_0),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_sub_0),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_0),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_2),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_4),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_0),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_2),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_4),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_zor_0),
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_adet_0) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
            align-items: stretch !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tab_0) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_sub_0) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_0) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_2) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_ders_4) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_0) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_2) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tur_4) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_zor_0) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_adet_0) > div[data-testid="stColumn"] {
            min-width: 0 !important;
            flex: 1 1 0% !important;
            width: auto !important;
        }
        /* SinoTest Seçim Pill Butonları (Seçilmemiş Hal: Beyaz Yuvarlak Kapsül) */
        div[class*="st-key-cipko_"] button {
            border-radius: 999px !important;
            min-height: 44px !important;
            font-size: 13.5px !important;
            font-weight: 700 !important;
            padding: 8px 12px !important;
            transition: all 0.18s ease !important;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
            background: #ffffff !important;
            border: 1.5px solid #cbd5e1 !important;
        }
        div[class*="st-key-cipko_"] button p,
        div[class*="st-key-cipko_"] button span,
        div[class*="st-key-cipko_"] button div {
            color: #334155 !important;
            font-weight: 700 !important;
        }
        @media (max-width: 600px) {
            div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tab_0) {
                gap: 4px !important;
            }
            div[data-testid="stHorizontalBlock"]:has(.st-key-cipko_tab_0) button {
                padding: 6px 3px !important;
                font-size: 11px !important;
                min-height: 38px !important;
                white-space: nowrap !important;
                letter-spacing: -0.2px !important;
            }
        }
        /* Konu Butonları Çok Satırlı Olabilsin */
        div[class*="st-key-cipko_konu_btn_"] button {
            border-radius: 14px !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 10px 14px !important;
            min-height: 46px !important;
        }
        /* Başlat Butonu Soft Nane-Zümrüt Vurgulu */
        html body div[class*="st-key-"].st-key-cipko_start_test_btn button {
            background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
            border: 1.5px solid #059669 !important;
            box-shadow: 0 5px 14px rgba(16, 185, 129, 0.22) !important;
            min-height: 50px !important;
        }
        html body div[class*="st-key-"].st-key-cipko_start_test_btn button p,
        html body div[class*="st-key-"].st-key-cipko_start_test_btn button span,
        html body div[class*="st-key-"].st-key-cipko_start_test_btn button div {
            color: #ffffff !important;
            font-weight: 900 !important;
            font-size: 15px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Aktif Seçilen Pill Butonlarının Rengini Net Biçimde Değiştiren Yüksek Öncelikli CSS
    aktif_keys = []
    if st.session_state.cipko_ana_mod == "hizli_test":
        aktif_keys.append("cipko_tab_0")
    elif st.session_state.cipko_ana_mod == "kaynagimdan":
        aktif_keys.append("cipko_tab_1")
    else:
        aktif_keys.append("cipko_tab_2")

    if st.session_state.cipko_konu_mod == "sec":
        aktif_keys.append("cipko_sub_0")
    else:
        aktif_keys.append("cipko_sub_1")

    if st.session_state.cipko_ders in DERS_LISTESI:
        aktif_keys.append(f"cipko_ders_{DERS_LISTESI.index(st.session_state.cipko_ders)}")

    for t_idx, (_, t_val) in enumerate(CALISMA_TURLERI):
        if t_val in st.session_state.cipko_turler:
            aktif_keys.append(f"cipko_tur_{t_idx}")

    if st.session_state.cipko_coklu_sec:
        aktif_keys.append("cipko_multi_toggle")

    if st.session_state.cipko_zorluk in ZORLUK_LISTESI:
        aktif_keys.append(f"cipko_zor_{ZORLUK_LISTESI.index(st.session_state.cipko_zorluk)}")

    if st.session_state.cipko_soru_sayisi in ADET_LISTESI:
        aktif_keys.append(f"cipko_adet_{ADET_LISTESI.index(st.session_state.cipko_soru_sayisi)}")

    if st.session_state.cipko_ders and st.session_state.cipko_ders in st.session_state.ai_konu_havuzu:
        mevcut_konular = ["🌟 Tüm Konular (Genel Karma)"] + st.session_state.ai_konu_havuzu[st.session_state.cipko_ders]
        if st.session_state.cipko_konu in mevcut_konular:
            aktif_keys.append(f"cipko_konu_btn_{mevcut_konular.index(st.session_state.cipko_konu)}")

    aktif_css_kurallari = ""
    for a_key in aktif_keys:
        aktif_css_kurallari += f"""
        html body div[class*="st-key-"].st-key-{a_key} button {{
            background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%) !important;
            border: 1.5px solid #4f46e5 !important;
            box-shadow: 0 3px 10px rgba(99, 102, 241, 0.22) !important;
            transform: translateY(-1px) !important;
        }}
        html body div[class*="st-key-"].st-key-{a_key} button p,
        html body div[class*="st-key-"].st-key-{a_key} button span,
        html body div[class*="st-key-"].st-key-{a_key} button div {{
            color: #ffffff !important;
            font-weight: 800 !important;
        }}
        """
    st.markdown(f"<style>{aktif_css_kurallari}</style>", unsafe_allow_html=True)

    # =========================================================================
    # 🏆 SİNOTEST KUPA & 3 BÜYÜK HEDİYE PAKETİ ÖDÜL SİSTEMİ (POPUP VİTRİN)
    # =========================================================================
    DERS_ODUL_META = {
        "Türkçe": {"ikon": "📘", "renk": "#6366f1"},
        "Matematik": {"ikon": "📐", "renk": "#f43f5e"},
        "Fen Bilimleri": {"ikon": "🔬", "renk": "#10b981"},
        "İnkılap Tarihi": {"ikon": "🏛️", "renk": "#f59e0b"},
        "İngilizce": {"ikon": "🌍", "renk": "#8b5cf6"},
        "Din Kültürü": {"ikon": "🌿", "renk": "#14b8a6"},
    }

    HEDIYE_PAKETLERI = {
        "paket_1": {
            "no": 1,
            "kutu_baslik": "1. Hediye Paketi",
            "odul_adi": "Whopper Menü",
            "alt_baslik": "Dumanı Üstünde Dev Whopper Burger + Çıtır Patates + Buz Gibi İçecek!",
            "detay": "Burger King'den efsane Whopper Menü ödülü! Tüm derslerden 20 Kupa barajını tamamladığında bu lezzet paketini hemen seçebilirsin.",
            "tema_renk": "#dc2626",
            "tema_bg": "linear-gradient(135deg, #fff1f2 0%, #fef3c7 100%)",
            "kutu_bg": "linear-gradient(145deg, #ef4444 0%, #b91c1c 100%)",
            "kurdele": "#fbbf24",
            "ikonlar": "🍔🍟🥤",
            "svg": (
                '<svg viewBox="0 0 220 150" width="190" height="130" style="display:block;margin:0 auto;filter:drop-shadow(0 8px 16px rgba(220,38,38,0.25));">'
                '<rect x="10" y="10" width="200" height="130" rx="22" fill="#fff7ed" stroke="#f59e0b" stroke-width="3"/>'
                '<!-- Fries -->'
                '<rect x="138" y="32" width="8" height="42" rx="3" fill="#fbbf24" transform="rotate(-8 142 53)"/>'
                '<rect x="148" y="26" width="8" height="46" rx="3" fill="#f59e0b"/>'
                '<rect x="158" y="28" width="8" height="44" rx="3" fill="#fbbf24" transform="rotate(6 162 50)"/>'
                '<rect x="168" y="34" width="8" height="40" rx="3" fill="#f59e0b" transform="rotate(12 172 54)"/>'
                '<path d="M132 62 L182 62 L176 112 L138 112 Z" fill="#dc2626"/>'
                '<text x="157" y="92" font-size="11" font-weight="900" fill="#fef08a" text-anchor="middle">FRIES</text>'
                '<!-- Cola Cup -->'
                '<path d="M178 48 L202 48 L198 112 L182 112 Z" fill="#1d4ed8"/>'
                '<rect x="175" y="43" width="30" height="7" rx="3" fill="#e2e8f0"/>'
                '<path d="M190 43 L196 24 L204 24" stroke="#ef4444" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<!-- Big Whopper Burger -->'
                '<path d="M28 74 C28 42, 122 42, 122 74 Z" fill="#d97706"/>'
                '<ellipse cx="55" cy="57" rx="3" ry="1.8" fill="#fef3c7"/>'
                '<ellipse cx="75" cy="52" rx="3" ry="1.8" fill="#fef3c7"/>'
                '<ellipse cx="95" cy="58" rx="3" ry="1.8" fill="#fef3c7"/>'
                '<ellipse cx="66" cy="63" rx="3" ry="1.8" fill="#fef3c7"/>'
                '<ellipse cx="86" cy="64" rx="3" ry="1.8" fill="#fef3c7"/>'
                '<path d="M24 76 Q38 82 50 75 Q62 82 75 75 Q88 82 100 75 Q114 82 126 76" stroke="#16a34a" stroke-width="6" fill="none" stroke-linecap="round"/>'
                '<rect x="30" y="80" width="90" height="7" rx="3" fill="#ef4444"/>'
                '<polygon points="32,87 118,87 110,95 40,95" fill="#fbbf24"/>'
                '<rect x="26" y="89" width="98" height="15" rx="7" fill="#78350f"/>'
                '<rect x="30" y="105" width="90" height="13" rx="6" fill="#d97706"/>'
                '<rect x="25" y="122" width="170" height="14" rx="7" fill="#dc2626"/>'
                '<text x="110" y="132" font-size="9.5" font-weight="900" fill="#ffffff" text-anchor="middle">WHOPPER MENU</text>'
                '</svg>'
            ),
        },
        "paket_2": {
            "no": 2,
            "kutu_baslik": "2. Hediye Paketi",
            "odul_adi": "500 TL Trendyol Çeki",
            "alt_baslik": "Trendyol'da Dilediğin Alışverişte Geçerli Tam 500 TL Hediye Çeki!",
            "detay": "Tüm derslerden 20 Kupa kazandığında 500 TL değerindeki Trendyol Hediye Çeki senin oluyor! İstediğin ürünleri sepetine ekle.",
            "tema_renk": "#ea580c",
            "tema_bg": "linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)",
            "kutu_bg": "linear-gradient(145deg, #f97316 0%, #c2410c 100%)",
            "kurdele": "#fde047",
            "ikonlar": "🛍️💳✨",
            "svg": (
                '<svg viewBox="0 0 220 150" width="190" height="130" style="display:block;margin:0 auto;filter:drop-shadow(0 8px 16px rgba(234,88,12,0.25));">'
                '<defs><linearGradient id="tyGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#f97316"/><stop offset="100%" stop-color="#ea580c"/></linearGradient></defs>'
                '<rect x="14" y="16" width="192" height="118" rx="18" fill="url(#tyGrad)" stroke="#fed7aa" stroke-width="3"/>'
                '<circle cx="14" cy="75" r="10" fill="#ffffff"/>'
                '<circle cx="206" cy="75" r="10" fill="#ffffff"/>'
                '<rect x="28" y="28" width="164" height="94" rx="12" fill="none" stroke="#ffedd5" stroke-width="1.5" stroke-dasharray="5,4"/>'
                '<text x="110" y="52" font-size="15" font-weight="900" fill="#ffffff" text-anchor="middle" letter-spacing="1.5">trendyol</text>'
                '<rect x="48" y="60" width="124" height="34" rx="10" fill="#ffffff"/>'
                '<text x="110" y="83" font-size="22" font-weight="900" fill="#ea580c" text-anchor="middle">500 TL</text>'
                '<text x="110" y="111" font-size="11" font-weight="800" fill="#fef08a" text-anchor="middle">✨ HEDİYE ÇEKİ KUPONU ✨</text>'
                '</svg>'
            ),
        },
        "paket_3": {
            "no": 3,
            "kutu_baslik": "3. Hediye Paketi",
            "odul_adi": "Sen ne istersen(max bütçe 500TL)",
            "alt_baslik": "Ödülünü Kendin Belirle! (Maksimum Bütçe: 500 TL)",
            "detay": "Oyun, kitap, kulaklık, forma, kırtasiye veya bambaşka bir sürpriz... Tüm derslerden 20 Kupa topla, 500 TL bütçeye kadar ne istersen o senin olsun!",
            "tema_renk": "#7c3aed",
            "tema_bg": "linear-gradient(135deg, #f5f3ff 0%, #fef3c7 100%)",
            "kutu_bg": "linear-gradient(145deg, #8b5cf6 0%, #5b21b6 100%)",
            "kurdele": "#facc15",
            "ikonlar": "🌟👑🎉",
            "svg": (
                '<svg viewBox="0 0 220 150" width="190" height="130" style="display:block;margin:0 auto;filter:drop-shadow(0 8px 16px rgba(124,58,237,0.28));">'
                '<defs><linearGradient id="vipGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#7c3aed"/><stop offset="100%" stop-color="#4c1d95"/></linearGradient></defs>'
                '<rect x="14" y="14" width="192" height="122" rx="20" fill="url(#vipGrad)" stroke="#facc15" stroke-width="3.5"/>'
                '<!-- Crown -->'
                '<polygon points="75,62 86,34 110,50 134,34 145,62" fill="#facc15" stroke="#fef08a" stroke-width="2"/>'
                '<circle cx="86" cy="31" r="4" fill="#fef08a"/>'
                '<circle cx="110" cy="27" r="5" fill="#fde047"/>'
                '<circle cx="134" cy="31" r="4" fill="#fef08a"/>'
                '<rect x="34" y="70" width="152" height="30" rx="9" fill="#fef3c7"/>'
                '<text x="110" y="90" font-size="14" font-weight="900" fill="#5b21b6" text-anchor="middle">SEN NE İSTERSEN!</text>'
                '<rect x="56" y="106" width="108" height="20" rx="99" fill="#facc15"/>'
                '<text x="110" y="120" font-size="10.5" font-weight="900" fill="#4c1d95" text-anchor="middle">MAX BÜTÇE: 500 TL</text>'
                '</svg>'
            ),
        },
    }

    aktif_kullanici_kupa = st.session_state.get("user") or "misafir"
    kayitli_odul_verisi = get_user_data(aktif_kullanici_kupa, "sinotest_oduller").get("profil", {})
    if "sinotest_profil" not in st.session_state or not st.session_state.sinotest_profil:
        varsayilan_sayaclar = {d: 0 for d in DERS_LISTESI}
        varsayilan_sayaclar.update(kayitli_odul_verisi.get("ders_sayaclari", {}))
        st.session_state.sinotest_profil = {
            "toplam_kupa": int(kayitli_odul_verisi.get("toplam_kupa", 0)),
            "ders_sayaclari": varsayilan_sayaclar,
            "kazanilan_oduller": list(kayitli_odul_verisi.get("kazanilan_oduller", [])),
            "secilen_hediye_paketi": kayitli_odul_verisi.get("secilen_hediye_paketi", ""),
        }
    if "secilen_hediye_paketi" not in st.session_state.sinotest_profil:
        st.session_state.sinotest_profil["secilen_hediye_paketi"] = kayitli_odul_verisi.get("secilen_hediye_paketi", "")

    def sinotest_ilerleme_kaydet(ders_adi, eklenen_soru_sayisi, kazanilan_kupa):
        prof = st.session_state.sinotest_profil
        if ders_adi not in prof["ders_sayaclari"]:
            prof["ders_sayaclari"][ders_adi] = 0
        eski_sayi = int(prof["ders_sayaclari"][ders_adi])
        # Her etkinlik o dersin 20'lik kupa barajına doğrudan katkı sağlar
        yeni_sayi = eski_sayi + int(eklenen_soru_sayisi)
        prof["ders_sayaclari"][ders_adi] = yeni_sayi
        prof["toplam_kupa"] = int(prof["toplam_kupa"]) + int(kazanilan_kupa)

        yeni_odul_mesaji = None
        if eski_sayi < 20 and yeni_sayi >= 20:
            rozet_metni = f"🏆 {ders_adi}: 20/20 Kupa Tamamlandı!"
            if rozet_metni not in prof["kazanilan_oduller"]:
                prof["kazanilan_oduller"].append(rozet_metni)
            prof["toplam_kupa"] += 10
            yeni_odul_mesaji = rozet_metni

        save_user_data(aktif_kullanici_kupa, "sinotest_oduller", "profil", prof)
        return yeni_odul_mesaji

    prof_aktif = st.session_state.sinotest_profil
    tamamlanan_ders_adedi = sum(1 for d in DERS_LISTESI if int(prof_aktif["ders_sayaclari"].get(d, 0)) >= 20)
    tum_dersler_20_mi = (tamamlanan_ders_adedi == len(DERS_LISTESI))
    secili_paket_key = prof_aktif.get("secilen_hediye_paketi", "")
    toplam_hedef_kupa = len(DERS_LISTESI) * 20  # 6 ders x 20 = 120 Kupa
    mevcut_hedef_ici_kupa = sum(min(20, int(prof_aktif["ders_sayaclari"].get(d, 0))) for d in DERS_LISTESI)
    toplam_kalan_kupa = max(0, toplam_hedef_kupa - mevcut_hedef_ici_kupa)
    genel_ilerleme_yuzde = int((mevcut_hedef_ici_kupa / float(toplam_hedef_kupa)) * 100)

    with st.container(border=True):
        # SinoTest Başlık Alanı + Canlı Kupa & 6/6 Ders Durumu
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">'
            f'<div>'
            f'<span style="font-size:24px; font-weight:900; background:linear-gradient(90deg, #1d4ed8, #7c3aed); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">⚡ SinoTest</span>'
            f'<div style="font-size:12.5px; color:#64748b; font-weight:600;">Sınırsız Yapay Zeka Çalışma, Kupa & Hediye Paketi İstasyonu</div>'
            f'</div>'
            f'<div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">'
            f'<span id="sino-top-kupa-pill" style="background:linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color:#92400e; font-size:13px; font-weight:900; padding:6px 13px; border-radius:99px; border:1.5px solid #f59e0b; box-shadow:0 2px 8px rgba(245,158,11,0.18);">'
            f'🏆 Kazanılan: <span id="sino-live-kupa">{prof_aktif["toplam_kupa"]}</span> Kupa'
            f'</span>'
            f'<span id="sino-top-odul-pill" style="background:linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); color:#166534; font-size:13px; font-weight:900; padding:6px 13px; border-radius:99px; border:1.5px solid #22c55e;">'
            f'🎯 Tamamlanan Ders: <span id="sino-live-odul">{tamamlanan_ders_adedi}</span> / {len(DERS_LISTESI)}'
            f'</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # 🏆 DERS KUPA DURUMU + 🎁 3 YAN YANA SÜRPRİZ HEDİYE PAKETİ (KOMPAKT & KEYİFLİ VİTRİN)
        ders_kartlari_parcalar = []
        ders_durum_js_listesi = []
        kisa_ad_haritasi = {
            "Türkçe": "Türkçe",
            "Matematik": "Matematik",
            "Fen Bilimleri": "Fen Bil.",
            "İnkılap Tarihi": "İnkılap",
            "İngilizce": "İngilizce",
            "Din Kültürü": "Din K.",
        }
        for d_ad in DERS_LISTESI:
            d_meta = DERS_ODUL_META.get(d_ad, {"ikon": "📘", "renk": "#2563eb"})
            d_toplam = int(prof_aktif["ders_sayaclari"].get(d_ad, 0))
            d_tamam_mi = d_toplam >= 20
            d_gosterim = min(20, d_toplam)
            d_kalan = max(0, 20 - d_gosterim)
            d_yuzde = 100 if d_tamam_mi else int((d_gosterim / 20.0) * 100)
            odul_rozet = "✅ 20/20" if d_tamam_mi else f"{d_gosterim}/20 🏆"
            odul_bg = "#dcfce7; color:#166534;" if d_tamam_mi else "#fef3c7; color:#92400e;"
            ders_durum_js_listesi.append({
                "ders": d_ad,
                "ikon": d_meta["ikon"],
                "renk": d_meta["renk"],
                "mevcut": d_gosterim,
                "kalan": d_kalan,
                "yuzde": d_yuzde,
                "tamam": d_tamam_mi,
            })
            ders_kartlari_parcalar.append(
                f'<div class="subj-chip">'
                f'<div class="subj-top">'
                f'<span class="subj-name">{d_meta["ikon"]} {kisa_ad_haritasi.get(d_ad, d_ad)}</span>'
                f'<span id="sino-badge-{d_ad}" class="subj-bdg" style="background:{odul_bg}">{odul_rozet}</span>'
                f'</div>'
                f'<div class="subj-bar"><div id="sino-bar-{d_ad}" class="subj-fill" style="width:{d_yuzde}%;background:{d_meta["renk"]};"></div></div>'
                f'</div>'
            )
        ders_kartlari_html = "".join(ders_kartlari_parcalar)

        kutu_alt_yazi = (
            "🎉 Kilidi açıldı! Tıkla & seç"
            if tum_dersler_20_mi
            else "Kalan kupayı tamamla, hediyeni seç!"
        )
        kilit_ikon = "🔓" if tum_dersler_20_mi else "🔒"

        hediye_html_widget = f"""
        <style>
            * {{ box-sizing: border-box; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
            html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
            .joy-wrap {{
                background: linear-gradient(135deg, #fffdf7 0%, #f5f7ff 55%, #faf5ff 100%);
                border: 1.5px solid #fde68a;
                border-radius: 16px;
                padding: 10px 10px;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
            }}
            .subj-grid {{
                display: grid;
                grid-template-columns: repeat(6, minmax(0, 1fr));
                gap: 6px;
                margin-bottom: 9px;
            }}
            @media (max-width: 768px) {{
                .subj-grid {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
            }}
            @media (max-width: 580px) {{
                .subj-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 5px !important; }}
            }}
            .subj-chip {{
                background: rgba(255,255,255,0.95);
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 5px 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            }}
            .subj-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 3px;
                margin-bottom: 4px;
            }}
            .subj-name {{
                font-size: 11px;
                font-weight: 800;
                color: #0f172a;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .subj-bdg {{
                font-size: 10px;
                font-weight: 900;
                padding: 1px 6px;
                border-radius: 99px;
                white-space: nowrap;
                flex-shrink: 0;
            }}
            .subj-bar {{
                height: 5px;
                background: #e2e8f0;
                border-radius: 99px;
                overflow: hidden;
            }}
            .subj-fill {{
                height: 100%;
                border-radius: 99px;
                transition: width 0.35s ease;
            }}
            .gift-row {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
            }}
            .gift-card {{
                position: relative;
                border-radius: 14px;
                padding: 8px 8px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                color: #1e293b;
                box-shadow: 0 3px 10px rgba(15, 23, 42, 0.06);
                transition: transform 0.18s ease, box-shadow 0.18s ease;
                user-select: none;
                overflow: hidden;
            }}
            .gift-card:hover {{
                transform: translateY(-2px) scale(1.015);
                box-shadow: 0 6px 14px rgba(15, 23, 42, 0.10);
            }}
            .gift-card.pk1 {{
                background: linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%);
                border: 1.5px solid #fda4af;
            }}
            .gift-card.pk2 {{
                background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%);
                border: 1.5px solid #fdba74;
            }}
            .gift-card.pk3 {{
                background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
                border: 1.5px solid #d8b4fe;
            }}
            .gift-icon-box {{
                width: 38px;
                height: 38px;
                border-radius: 11px;
                background: rgba(255,255,255,0.68);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                flex-shrink: 0;
                position: relative;
                animation: bobGift 2.4s ease-in-out infinite;
                box-shadow: 0 2px 6px rgba(15,23,42,0.06);
            }}
            @keyframes bobGift {{
                0%, 100% {{ transform: translateY(0); }}
                50% {{ transform: translateY(-3px); }}
            }}
            .gift-lock-dot {{
                position: absolute;
                bottom: -3px;
                right: -3px;
                background: #ffffff;
                border-radius: 99px;
                width: 16px;
                height: 16px;
                font-size: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.12);
            }}
            .gift-info {{
                min-width: 0;
                flex: 1;
                text-align: left;
            }}
            .gift-title {{
                font-size: 12.5px;
                font-weight: 900;
                line-height: 1.2;
                margin-bottom: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .gift-card.pk1 .gift-title {{ color: #9f1239; }}
            .gift-card.pk2 .gift-title {{ color: #9a3412; }}
            .gift-card.pk3 .gift-title {{ color: #5b21b6; }}
            .gift-sub {{
                font-size: 10px;
                font-weight: 700;
                line-height: 1.25;
            }}
            .gift-card.pk1 .gift-sub {{ color: #be123c; }}
            .gift-card.pk2 .gift-sub {{ color: #c2410c; }}
            .gift-card.pk3 .gift-sub {{ color: #6d28d9; }}
            @media (max-width: 580px) {{
                .joy-wrap {{ padding: 8px 6px; }}
                .gift-row {{ gap: 5px; }}
                .gift-card {{
                    flex-direction: column;
                    text-align: center;
                    padding: 7px 4px;
                    gap: 3px;
                }}
                .gift-info {{ text-align: center; width: 100%; }}
                .gift-icon-box {{ width: 34px; height: 34px; font-size: 19px; }}
                .gift-title {{ font-size: 11px; line-height: 1.15; white-space: normal; }}
                .gift-sub {{ font-size: 9px; line-height: 1.2; }}
            }}
        </style>
        <div class="joy-wrap">
            <div class="subj-grid">{ders_kartlari_html}</div>
            <div class="gift-row">
                <div class="gift-card pk1" onclick="openSinoGiftPopup('paket_1')">
                    <div class="gift-icon-box">🎁<span class="gift-lock-dot">{kilit_ikon}</span></div>
                    <div class="gift-info">
                        <div class="gift-title">1. Hediye Paketi</div>
                        <div class="gift-sub">{kutu_alt_yazi}</div>
                    </div>
                </div>
                <div class="gift-card pk2" onclick="openSinoGiftPopup('paket_2')">
                    <div class="gift-icon-box">🎁<span class="gift-lock-dot">{kilit_ikon}</span></div>
                    <div class="gift-info">
                        <div class="gift-title">2. Hediye Paketi</div>
                        <div class="gift-sub">{kutu_alt_yazi}</div>
                    </div>
                </div>
                <div class="gift-card pk3" onclick="openSinoGiftPopup('paket_3')">
                    <div class="gift-icon-box">🎁<span class="gift-lock-dot">{kilit_ikon}</span></div>
                    <div class="gift-info">
                        <div class="gift-title">3. Hediye Paketi</div>
                        <div class="gift-sub">{kutu_alt_yazi}</div>
                    </div>
                </div>
            </div>
        </div>
        <script>
            const GIFT_DATA = {json.dumps(HEDIYE_PAKETLERI, ensure_ascii=False)};
            const ALL_20_DONE = {json.dumps(tum_dersler_20_mi)};
            const SUBJECT_STATUS = {json.dumps(ders_durum_js_listesi, ensure_ascii=False)};
            const REMAINING_TOTAL_CUPS = {toplam_kalan_kupa};

            function resizeSelf() {{
                try {{
                    const h = (document.body.scrollHeight || document.documentElement.scrollHeight) + 4;
                    if (window.frameElement) {{
                        window.frameElement.style.height = h + 'px';
                    }}
                    if (window.parent && window.parent.document) {{
                        const frames = window.parent.document.querySelectorAll('iframe');
                        frames.forEach(f => {{
                            try {{
                                if (f.contentWindow === window || f.contentDocument === document) {{
                                    f.style.height = h + 'px';
                                }}
                            }} catch(e) {{}}
                        }});
                    }}
                }} catch(err) {{}}
            }}
            window.addEventListener('load', resizeSelf);
            window.addEventListener('resize', resizeSelf);
            setTimeout(resizeSelf, 50);
            setTimeout(resizeSelf, 250);
            setTimeout(resizeSelf, 600);

            window.openSinoGiftPopup = function(pkgKey) {{
                const pk = GIFT_DATA[pkgKey];
                if (!pk) return;
                const pDoc = window.parent ? window.parent.document : document;
                let overlay = pDoc.getElementById('sino-gift-popup-modal');
                if (overlay) overlay.remove();

                overlay = pDoc.createElement('div');
                overlay.id = 'sino-gift-popup-modal';
                overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,0.72);backdrop-filter:blur(5px);z-index:999999;display:flex;align-items:center;justify-content:center;padding:16px;';

                if (!ALL_20_DONE) {{
                    const rowsHtml = SUBJECT_STATUS.map(s => `
                        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:7px 10px;text-align:left;">
                            <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:800;color:#0f172a;margin-bottom:4px;">
                                <span>${{s.ikon}} ${{s.ders}}</span>
                                <span style="color:${{s.tamam ? '#16a34a' : '#b45309'}};">${{s.tamam ? '✅ 20/20' : s.kalan + ' Kupa kaldı'}}</span>
                            </div>
                            <div style="height:6px;background:#e2e8f0;border-radius:99px;overflow:hidden;">
                                <div style="height:100%;width:${{s.yuzde}}%;background:${{s.tamam ? '#16a34a' : '#f59e0b'}};border-radius:99px;"></div>
                            </div>
                        </div>
                    `).join('');

                    overlay.innerHTML = `
                        <div style="background:#ffffff;max-width:440px;width:100%;max-height:92vh;overflow-y:auto;border-radius:24px;padding:22px 20px;text-align:center;position:relative;box-shadow:0 24px 60px rgba(0,0,0,0.38);border:3px solid #f59e0b;font-family:'Inter',sans-serif;" onclick="event.stopPropagation()">
                            <button onclick="document.getElementById('sino-gift-popup-modal').remove()" style="position:absolute;top:12px;right:12px;width:34px;height:34px;border-radius:99px;border:none;background:#f1f5f9;color:#0f172a;font-size:17px;font-weight:900;cursor:pointer;">✕</button>
                            <div style="display:inline-block;background:#fef3c7;color:#92400e;border:1px solid #fcd34d;font-size:12px;font-weight:900;padding:4px 14px;border-radius:99px;margin-bottom:10px;">
                                🔒 ${{pk.kutu_baslik.toUpperCase()}} KİLİTLİ
                            </div>
                            <div style="font-size:48px;line-height:1.1;margin:4px 0 8px 0;">🎁🔒</div>
                            <div style="font-size:19px;font-weight:900;color:#0f172a;margin-bottom:6px;">
                                Kalan Kupayı Tamamla, Hediyeni Seç!
                            </div>
                            <div style="font-size:12.5px;font-weight:600;color:#475569;margin-bottom:14px;line-height:1.45;">
                                Bu sürpriz hediye paketinin görsel içeriği, <b>tüm derslerden 20 Kupa</b> kazandığında açılır! Toplam <b>${{REMAINING_TOTAL_CUPS}} Kupa</b> daha kazanarak kilidi açabilirsin.
                            </div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">
                                ${{rowsHtml}}
                            </div>
                            <button onclick="document.getElementById('sino-gift-popup-modal').remove()" style="width:100%;padding:11px;border:none;border-radius:12px;background:linear-gradient(90deg, #2563eb, #4f46e5);color:#ffffff;font-size:13px;font-weight:900;cursor:pointer;">
                                💪 Hemen Soru Çözüp Kupa Kazanmaya Devam Et!
                            </button>
                        </div>
                    `;
                }} else {{
                    overlay.innerHTML = `
                        <div style="background:#ffffff;max-width:450px;width:100%;max-height:92vh;overflow-y:auto;border-radius:26px;padding:22px 20px;text-align:center;position:relative;box-shadow:0 24px 60px rgba(0,0,0,0.45);border:4px solid ${{pk.tema_renk}};font-family:'Inter',sans-serif;" onclick="event.stopPropagation()">
                            <button onclick="document.getElementById('sino-gift-popup-modal').remove()" style="position:absolute;top:12px;right:12px;width:36px;height:36px;border-radius:99px;border:none;background:#f1f5f9;color:#0f172a;font-size:18px;font-weight:900;cursor:pointer;">✕</button>
                            <div style="display:inline-block;background:${{pk.tema_renk}};color:#ffffff;font-size:12px;font-weight:900;padding:5px 14px;border-radius:99px;margin-bottom:12px;">
                                🎉 ${{pk.kutu_baslik.toUpperCase()}} AÇILDI!
                            </div>
                            <div style="background:${{pk.tema_bg}};border:2px dashed ${{pk.tema_renk}};border-radius:20px;padding:16px 12px;margin-bottom:12px;">
                                ${{pk.svg}}
                                <div style="font-size:28px;margin-top:8px;">${{pk.ikonlar}}</div>
                                <div style="font-size:24px;font-weight:900;color:#0f172a;margin:6px 0;">${{pk.odul_adi}}</div>
                                <div style="font-size:13.5px;font-weight:800;color:${{pk.tema_renk}};">${{pk.alt_baslik}}</div>
                            </div>
                            <div style="font-size:13px;font-weight:600;color:#334155;line-height:1.5;margin-bottom:12px;">
                                ${{pk.detay}}
                            </div>
                            <div id="sino-gift-chosen-msg" style="display:none;background:#dcfce7;border:2px solid #16a34a;color:#166534;padding:10px;border-radius:12px;font-size:13px;font-weight:900;margin-bottom:10px;">
                                🎉 Harika Seçim! Ödülün: <b>${{pk.odul_adi}}</b> olarak kaydedildi!
                            </div>
                            <button onclick="document.getElementById('sino-gift-chosen-msg').style.display='block'; this.innerHTML='✅ Bu Hediye Paketi Seçildi!'; this.style.background='#16a34a';" style="width:100%;padding:12px;border:none;border-radius:14px;background:linear-gradient(90deg, ${{pk.tema_renk}}, #1e293b);color:#ffffff;font-size:14px;font-weight:900;cursor:pointer;">
                                🏆 Bu Hediye Paketini Ödülüm Olarak Seç!
                            </button>
                        </div>
                    `;
                }}
                overlay.onclick = function() {{ overlay.remove(); }};
                pDoc.body.appendChild(overlay);
            }};
        </script>
        """
        components.html(hediye_html_widget, height=255, scrolling=False)

        # Sadece tüm derslerden 20 Kupa tamamlandığında kalıcı veritabanı ödül seçimi butonlarını göster
        if tum_dersler_20_mi:
            g_col1, g_col2, g_col3 = st.columns(3, gap="small")
            for idx_col, (p_key, p_val) in zip((g_col1, g_col2, g_col3), HEDIYE_PAKETLERI.items()):
                with idx_col:
                    secili_mi = (secili_paket_key == p_key)
                    btn_etiket = f"✅ Seçildi: {p_val['odul_adi']}" if secili_mi else f"🏆 {p_val['kutu_baslik']}ni Seç ({p_val['odul_adi']})"
                    if st.button(btn_etiket, key=f"claim_final_gift_{p_key}", use_container_width=True):
                        st.session_state.sinotest_profil["secilen_hediye_paketi"] = p_key
                        save_user_data(aktif_kullanici_kupa, "sinotest_oduller", "profil", st.session_state.sinotest_profil)
                        st.balloons()
                        st.rerun()

        # 1) ÜST 3'LÜ SEGMENTED BAR: [⚡ Hızlı Test | 📚 Kaynağım | 📷 Fotoğraf]
        t_col1, t_col2, t_col3 = st.columns(3, gap="small")
        with t_col1:
            if st.button("⚡ Hızlı Test", key="cipko_tab_0", use_container_width=True):
                st.session_state.cipko_ana_mod = "hizli_test"
                st.rerun()
        with t_col2:
            if st.button("📚 Kaynağım", key="cipko_tab_1", use_container_width=True):
                st.session_state.cipko_ana_mod = "kaynagimdan"
                st.rerun()
        with t_col3:
            if st.button("📷 Fotoğraf", key="cipko_tab_2", use_container_width=True):
                st.session_state.cipko_ana_mod = "fotograftan"
                st.rerun()

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        # =========================================================================
        # MOD 1: ⚡ HIZLI TEST (Ders -> Konu -> Çalışma Türü (6 Mod) -> Zorluk -> 5/10/20)
        # =========================================================================
        if st.session_state.cipko_ana_mod == "hizli_test":
            # Alt Segmented Bar: [Konudan seç | Konu yaz]
            s_col1, s_col2 = st.columns(2, gap="small")
            with s_col1:
                if st.button("📋 Konudan seç", key="cipko_sub_0", use_container_width=True):
                    st.session_state.cipko_konu_mod = "sec"
                    st.rerun()
            with s_col2:
                if st.button("✍️ Konu yaz", key="cipko_sub_1", use_container_width=True):
                    st.session_state.cipko_konu_mod = "yaz"
                    st.rerun()

            st.markdown("<div style='font-size:17px; font-weight:800; color:#0f172a; margin:14px 0 8px 0;'>Hangi ders?</div>", unsafe_allow_html=True)

            # 6 LGS Dersi (2'li Yan Yana Kapsül Butonlar — Seçilen Mavi Olur)
            for r_idx in range(0, 6, 2):
                d_col1, d_col2 = st.columns(2, gap="small")
                for c_offset, d_col in enumerate([d_col1, d_col2]):
                    d_idx = r_idx + c_offset
                    ders_adi = DERS_LISTESI[d_idx]
                    secili_mi = (st.session_state.cipko_ders == ders_adi)
                    etiket = f"✓ {ders_adi}" if secili_mi else ders_adi
                    with d_col:
                        if st.button(etiket, key=f"cipko_ders_{d_idx}", use_container_width=True):
                            st.session_state.cipko_ders = ders_adi
                            if ders_adi not in st.session_state.ai_konu_havuzu:
                                with st.spinner(f"🤖 Yapay zeka {ders_adi} konularını getiriyor..."):
                                    st.session_state.ai_konu_havuzu[ders_adi] = get_ai_lgs_topics(ders_adi)
                            konu_list = st.session_state.ai_konu_havuzu[ders_adi]
                            st.session_state.cipko_konu = konu_list[0] if konu_list else "🌟 Tüm Konular (Genel Karma)"
                            st.session_state.hedef_scroll = "cipko-konu-alani"
                            st.rerun()

            # ÇALIŞMA TÜRÜ (Görseldeki 6'lı Grid + Çoklu Seç)
            tur_baslik_col, coklu_col = st.columns([2.2, 1.2], gap="small")
            with tur_baslik_col:
                st.markdown("<div style='font-size:17px; font-weight:800; color:#0f172a; margin:14px 0 6px 0;'>Çalışma türü</div>", unsafe_allow_html=True)
            with coklu_col:
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                coklu_etiket = "☑️ Çoklu seç (Açık)" if st.session_state.cipko_coklu_sec else "⬜ Çoklu seç"
                if st.button(coklu_etiket, key="cipko_multi_toggle", use_container_width=True):
                    st.session_state.cipko_coklu_sec = not st.session_state.cipko_coklu_sec
                    if not st.session_state.cipko_coklu_sec and len(st.session_state.cipko_turler) > 1:
                        st.session_state.cipko_turler = [st.session_state.cipko_turler[0]]
                    st.rerun()

            for tr_row in range(0, 6, 2):
                tc1, tc2 = st.columns(2, gap="small")
                for tc_off, t_col in enumerate([tc1, tc2]):
                    t_idx = tr_row + tc_off
                    t_gorunen, t_kod = CALISMA_TURLERI[t_idx]
                    secili_tur_mu = (t_kod in st.session_state.cipko_turler)
                    btn_metin = f"✓ {t_gorunen}" if secili_tur_mu else t_gorunen
                    with t_col:
                        if st.button(btn_metin, key=f"cipko_tur_{t_idx}", use_container_width=True):
                            if st.session_state.cipko_coklu_sec:
                                if t_kod in st.session_state.cipko_turler:
                                    if len(st.session_state.cipko_turler) > 1:
                                        st.session_state.cipko_turler.remove(t_kod)
                                else:
                                    st.session_state.cipko_turler.append(t_kod)
                            else:
                                st.session_state.cipko_turler = [t_kod]
                            st.rerun()

            # Ders Seçildiyse Konu, Zorluk ve Soru Sayısı Alanını Aç
            st.markdown("<div id='cipko-konu-alani'></div>", unsafe_allow_html=True)
            secili_ders = st.session_state.cipko_ders

            if not secili_ders:
                st.info("👆 Konuları görmek ve çalışmaya başlamak için yukarıdan bir **ders seç**!")
            else:
                st.markdown("---")
                if st.session_state.cipko_konu_mod == "sec":
                    baslik_col, yenile_col = st.columns([2.2, 1.2], gap="small")
                    with baslik_col:
                        st.markdown(f"<div style='font-size:16.5px; font-weight:800; color:#0f172a;'>🎯 {secili_ders} Konuları</div>", unsafe_allow_html=True)
                    with yenile_col:
                        if st.button("🤖 AI Alt Konu Öner", key="cipko_ai_refresh", use_container_width=True):
                            with st.spinner(f"🤖 Yapay zeka {secili_ders} için yeni alt kazanımlar çıkarıyor..."):
                                st.session_state.ai_konu_havuzu[secili_ders] = get_ai_lgs_topics(secili_ders, force_ai=True)
                                st.session_state.cipko_konu = st.session_state.ai_konu_havuzu[secili_ders][0]
                                st.rerun()

                    if secili_ders not in st.session_state.ai_konu_havuzu:
                        st.session_state.ai_konu_havuzu[secili_ders] = MEB_8_SINIF_KONULARI.get(secili_ders, [])

                    tum_konular = ["🌟 Tüm Konular (Genel Karma)"] + st.session_state.ai_konu_havuzu[secili_ders]
                    if st.session_state.cipko_konu not in tum_konular:
                        st.session_state.cipko_konu = tum_konular[0]

                    for k_idx, k_ad in enumerate(tum_konular):
                        isaret = "✓ " if st.session_state.cipko_konu == k_ad else "• "
                        if st.button(f"{isaret}{k_ad}", key=f"cipko_konu_btn_{k_idx}", use_container_width=True):
                            st.session_state.cipko_konu = k_ad
                            st.session_state.hedef_scroll = "cipko-ayar-alani"
                            st.rerun()
                else:
                    st.markdown(f"<div style='font-size:16.5px; font-weight:800; color:#0f172a; margin-bottom:6px;'>✍️ {secili_ders} Konusu Yaz</div>", unsafe_allow_html=True)
                    yazilan_konu = st.text_input(
                        "Çalışmak istediğin konuyu veya kazanımı yaz:",
                        value="" if (not st.session_state.cipko_konu or st.session_state.cipko_konu.startswith("🌟")) else st.session_state.cipko_konu,
                        placeholder=f"Örn: {MEB_8_SINIF_KONULARI.get(secili_ders, ['Özel Konu'])[0]}",
                        key="cipko_yazilan_konu_input"
                    )
                    st.session_state.cipko_konu = yazilan_konu.strip() if yazilan_konu.strip() else "Genel Karma"

                # ZORLUK SEVİYESİ VE SORU/İÇERİK SAYISI (5 - 10 - 20)
                st.markdown("<div id='cipko-ayar-alani'></div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:16.5px; font-weight:800; color:#0f172a; margin:14px 0 8px 0;'>🔥 Zorluk seviyesi</div>", unsafe_allow_html=True)
                z_col1, z_col2, z_col3 = st.columns(3, gap="small")
                ZORLUK_ETIKET = [("🟢 Kolay", "Kolay"), ("🟡 Orta", "Orta"), ("🔴 Zor", "Zor")]
                for z_i, (z_goster, z_deger) in enumerate(ZORLUK_ETIKET):
                    z_sec = (st.session_state.cipko_zorluk == z_deger)
                    z_txt = f"✓ {z_goster}" if z_sec else z_goster
                    with [z_col1, z_col2, z_col3][z_i]:
                        if st.button(z_txt, key=f"cipko_zor_{z_i}", use_container_width=True):
                            st.session_state.cipko_zorluk = z_deger
                            st.rerun()

                st.markdown("<div style='font-size:16.5px; font-weight:800; color:#0f172a; margin:14px 0 8px 0;'>🔢 Soru / Kart sayısı</div>", unsafe_allow_html=True)
                a_col1, a_col2, a_col3 = st.columns(3, gap="small")
                for a_i, adet_val in enumerate([5, 10, 20]):
                    a_sec = (st.session_state.cipko_soru_sayisi == adet_val)
                    a_txt = f"✓ {adet_val} Adet" if a_sec else f"{adet_val} Adet"
                    with [a_col1, a_col2, a_col3][a_i]:
                        if st.button(a_txt, key=f"cipko_adet_{a_i}", use_container_width=True):
                            st.session_state.cipko_soru_sayisi = adet_val
                            st.rerun()

                secili_konu_son = st.session_state.cipko_konu or "Genel Karma"
                secili_zorluk_son = st.session_state.cipko_zorluk
                secili_adet_son = st.session_state.cipko_soru_sayisi
                secili_turler_son = st.session_state.cipko_turler or ["Test Oluştur"]
                turler_ozet_str = ", ".join(secili_turler_son)

                st.markdown(f"""
                <div style="background:#eff6ff; border:2px solid #93c5fd; border-radius:14px; padding:12px 14px; margin:12px 0; font-size:13.5px; color:#1e3a8a; font-weight:700;">
                    📌 <b>Seçimin:</b> {secili_ders} &nbsp;|&nbsp; 🎯 {secili_konu_son} &nbsp;|&nbsp; 🧩 <b>{turler_ozet_str}</b> &nbsp;|&nbsp; 🔥 {secili_zorluk_son} &nbsp;|&nbsp; 🔢 {secili_adet_son} Adet
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🚀 SinoTest'i Başlat ({turler_ozet_str})", key="cipko_start_test_btn", use_container_width=True):
                    uretilen_paketler = []
                    for tur_adi in secili_turler_son:
                        with st.spinner(f"🤖 SinoTest '{secili_ders} - {secili_konu_son}' için [{tur_adi}] ({secili_adet_son} adet) hazırlıyor..."):
                            veriler = generate_sinotest_activity(
                                ders=secili_ders,
                                konu=secili_konu_son,
                                zorluk=secili_zorluk_son,
                                adet=secili_adet_son,
                                calisma_turu=tur_adi
                            )
                            uretilen_paketler.append({
                                "ders": secili_ders,
                                "tur": tur_adi,
                                "baslik": f"{secili_ders} • {secili_konu_son} ({secili_zorluk_son})",
                                "veriler": veriler,
                                "odul_alindi": False,
                            })
                    st.session_state.cipko_aktif_paketler = uretilen_paketler
                    st.session_state.hedef_scroll = "cipko-test-arena-sonuc"
                    st.rerun()

        # =========================================================================
        # MOD 2: 📚 KAYNAĞIMDAN (Kütüphanedeki PDF'lerden Seçip Test Üretme)
        # =========================================================================
        elif st.session_state.cipko_ana_mod == "kaynagimdan":
            pdf_lib_dir = Path("pdf_kutuphanesi")
            pdf_lib_dir.mkdir(exist_ok=True)
            kayitli_pdfler = sorted(pdf_lib_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
            if not kayitli_pdfler:
                st.info("📚 Henüz kütüphanende yüklü bir PDF yok. '📚 PDF Havuzu' istasyonundan veya '📷 Fotoğraftan' sekmesinden kaynak yükebilirsin!")
            else:
                secilen_pdf_ad = st.selectbox("📖 Kütüphanendeki Kaynağı Seç:", [p.stem for p in kayitli_pdfler])
                secilen_pdf_yol = next((p for p in kayitli_pdfler if p.stem == secilen_pdf_ad), kayitli_pdfler[0])
                doc_k = fitz.open(str(secilen_pdf_yol))
                toplam_s_k = max(1, len(doc_k))
                sayfa_k = st.number_input(f"Hangi Sayfa? (1 - {toplam_s_k})", min_value=1, max_value=toplam_s_k, value=1)
                pix_k = doc_k.load_page(sayfa_k - 1).get_pixmap(dpi=140)
                img_k = Image.frombytes("RGB", [pix_k.width, pix_k.height], pix_k.samples)
                doc_k.close()
                st.image(img_k, caption=f"{secilen_pdf_ad} - Sayfa {sayfa_k}", use_container_width=True)
                if st.button("🎯 Bu Sayfadan SinoTest Üret", use_container_width=True):
                    with st.spinner("Kaynağındaki sayfadan yeni nesil LGS soruları hazırlanıyor..."):
                        veriler_k = generate_lgs_quiz_list(image=img_k)
                        tahmini_ders = next((d for d in DERS_LISTESI if d.lower() in secilen_pdf_ad.lower()), "Matematik")
                        st.session_state.cipko_aktif_paketler = [{
                            "ders": tahmini_ders,
                            "tur": "Test Oluştur",
                            "baslik": f"{secilen_pdf_ad} (Sayfa {sayfa_k})",
                            "veriler": veriler_k,
                            "odul_alindi": False,
                        }]
                        st.session_state.hedef_scroll = "cipko-test-arena-sonuc"
                        st.rerun()

        # =========================================================================
        # MOD 3: 📷 FOTOĞRAFTAN (Fotoğraf/PDF Yükle -> Çözüm + İkiz Soru Üret)
        # =========================================================================
        elif st.session_state.cipko_ana_mod == "fotograftan":
            st.markdown("#### 📷 Soru Fotoğrafı veya PDF Yükle")
            ders_secimi = st.selectbox("Ders Seç", ["Türkçe", "Matematik", "Fen Bilimleri", "T.C. İnkılap Tarihi", "Din Kültürü", "İngilizce"])
            soru_metni = st.text_area("Soru metnini yapıştır (isteğe bağlı):")
            uploaded_files = st.file_uploader(
                "Soru Fotoğrafları veya PDF Yükle (Birden fazla sayfa seçebilirsin!)",
                type=["jpg", "png", "jpeg", "pdf"],
                accept_multiple_files=True
            )
            
            soru_gorselleri = []
            if uploaded_files:
                for uf in uploaded_files:
                    if uf.name.lower().endswith(".pdf"):
                        doc = fitz.open(stream=uf.getvalue(), filetype="pdf")
                        for p_idx in range(min(5, len(doc))):
                            pix = doc.load_page(p_idx).get_pixmap(dpi=140)
                            soru_gorselleri.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
                        doc.close()
                    else:
                        soru_gorselleri.append(Image.open(uf))
                
                st.success(f"📎 Toplam **{len(soru_gorselleri)} sayfa/görsel** yüklendi!")
                g_cols = st.columns(min(3, len(soru_gorselleri)))
                for idx, im in enumerate(soru_gorselleri):
                    with g_cols[idx % len(g_cols)]:
                        st.image(im, caption=f"Sayfa {idx + 1}")
            
            if st.button("✨ İkiz Sorusunu Üret ve Çöz", use_container_width=True):
                with st.spinner("Yapay zeka yüklenen tüm sayfaları inceliyor ve ikiz soruyu tasarlıyor..."):
                    st.session_state.ikiz_sonuc = generate_twin_question(
                        f"[{ders_secimi}] {soru_metni}",
                        image=soru_gorselleri if soru_gorselleri else None
                    )
                    st.session_state.ikiz_ders = ders_secimi
                    st.session_state.hedef_scroll = "ikiz-soru-sonuc"

        # =========================================================================
        # SİNOTEST ARENASI SONUÇ EKRANI (6 ÇALIŞMA TÜRÜ + KUPA & 20'LİK DERS ÖDÜLÜ)
        # =========================================================================
        st.markdown("<div id='cipko-test-arena-sonuc'></div>", unsafe_allow_html=True)
        if st.session_state.get("cipko_aktif_paketler") and st.session_state.cipko_ana_mod in ("hizli_test", "kaynagimdan"):
            for p_idx, paket in enumerate(st.session_state.cipko_aktif_paketler):
                st.markdown("---")
                tur_adi = paket.get("tur", "Test Oluştur")
                paket_ders = paket.get("ders") or st.session_state.get("cipko_ders") or "Türkçe"
                paket_baslik = paket.get("baslik", "SinoTest Çalışması")
                paket_veriler = paket.get("veriler", [])
                paket_odul_meta = DERS_ODUL_META.get(paket_ders, {"ikon": "📘", "renk": "#2563eb"})
                mevcut_ders_sayaci = int(prof_aktif["ders_sayaclari"].get(paket_ders, 0))
                mevcut_toplam_kupa = int(prof_aktif["toplam_kupa"])

                st.markdown(f"#### 🏆 [{tur_adi}] — {paket_baslik}")

                v_json = json.dumps(paket_veriler, ensure_ascii=False)

                # Ortak JS Kupa & 20 Kupa Ders Barajı Kutlama Fonksiyonu
                ortak_odul_js = f"""
                const SINO_DERS = {json.dumps(paket_ders, ensure_ascii=False)};
                const SINO_ODUL_IKON = {json.dumps(paket_odul_meta['ikon'], ensure_ascii=False)};
                const SINO_INIT_DERS_CNT = {mevcut_ders_sayaci};
                const SINO_INIT_KUPA = {mevcut_toplam_kupa};

                function awardSinoTrophy(completedCount, correctCount, bannerElId) {{
                    const earnedCups = Math.max(2, completedCount + (correctCount * 2));
                    const oldCnt = SINO_INIT_DERS_CNT;
                    const newCnt = oldCnt + completedCount;
                    const unlocked20 = (oldCnt < 20 && newCnt >= 20);
                    const bonusCups = unlocked20 ? 10 : 0;
                    const totalEarnedCups = earnedCups + bonusCups;
                    const newTotalCups = SINO_INIT_KUPA + totalEarnedCups;
                    const shownCnt = Math.min(20, newCnt);
                    const pct = newCnt >= 20 ? 100 : Math.round((shownCnt / 20) * 100);
                    const rem = Math.max(0, 20 - newCnt);

                    // Üstteki Ana Vitrini Canlı Güncelle (window.parent.document)
                    try {{
                        const pDoc = window.parent.document;
                        const kEl = pDoc.getElementById('sino-live-kupa');
                        if (kEl) kEl.textContent = newTotalCups;
                        const barEl = pDoc.getElementById('sino-bar-' + SINO_DERS);
                        if (barEl) barEl.style.width = pct + '%';
                        const cntEl = pDoc.getElementById('sino-cnt-' + SINO_DERS);
                        if (cntEl) cntEl.textContent = newCnt >= 20 ? '🎉 Hedef tamamlandı!' : ('⏳ ' + rem + ' kupa kaldı');
                        const bdgEl = pDoc.getElementById('sino-badge-' + SINO_DERS);
                        if (bdgEl) {{
                            if (newCnt >= 20) {{
                                bdgEl.textContent = '✅ 20/20 Tamam!';
                                bdgEl.style.background = '#dcfce7';
                                bdgEl.style.color = '#166534';
                            }} else {{
                                bdgEl.textContent = '🏆 ' + shownCnt + ' / 20';
                            }}
                        }}
                    }} catch (e) {{}}

                    const banner = document.getElementById(bannerElId);
                    if (!banner) return;
                    banner.style.display = 'block';
                    if (newCnt >= 20) {{
                        banner.innerHTML = `
                            <div style="background:linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #dcfce7 100%); border:3px solid #f59e0b; border-radius:18px; padding:18px; margin:14px 0; text-align:center; box-shadow:0 10px 26px rgba(245,158,11,0.3);">
                                <div style="font-size:32px; margin-bottom:4px;">🏆🎉🎁🎉🏆</div>
                                <div style="font-size:17px; font-weight:900; color:#92400e;">TEBRİKLER! ${{SINO_ODUL_IKON}} ${{SINO_DERS.toUpperCase()}} DERSİNDE 20 KUPA HEDEFİ TAMAMLANDI!</div>
                                <div style="font-size:14.5px; font-weight:900; color:#166534; margin:6px 0;">
                                    🎁 Tüm derslerde kalan kupaları tamamladığında üstteki 3 Sürpriz Hediye Paketinin kilidi açılacak ve hediyeni seçebileceksin!
                                </div>
                                <div style="font-size:13.5px; font-weight:800; color:#1e40af;">
                                    🏆 Bu çalışmadan <b>+${{totalEarnedCups}} Kupa</b> kazandın! Alttaki <b>"Vitrine Kaydet"</b> butonuna basarak kalıcı kaydetmeyi unutma!
                                </div>
                            </div>
                        `;
                    }} else {{
                        banner.innerHTML = `
                            <div style="background:linear-gradient(135deg, #eff6ff 0%, #fef3c7 100%); border:2px solid #60a5fa; border-radius:16px; padding:14px 16px; margin:12px 0;">
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                                    <span style="font-size:15px; font-weight:900; color:#1e3a8a;">🏆 Harika! +${{completedCount}} Ders Kupası & +${{totalEarnedCups}} Genel Kupa Kazandın!</span>
                                    <span style="background:#fef3c7; color:#92400e; border:1px solid #f59e0b; padding:4px 10px; border-radius:99px; font-size:12px; font-weight:800;">
                                        🎁 ${{SINO_DERS}} 20 Kupa Hedefine ${{rem}} Kupa kaldı! (${{shownCnt}} / 20 🏆)
                                    </span>
                                </div>
                                <div style="background:#cbd5e1; height:10px; border-radius:99px; overflow:hidden;">
                                    <div style="background:linear-gradient(90deg, #f59e0b, #16a34a); width:${{pct}}%; height:100%; border-radius:99px;"></div>
                                </div>
                            </div>
                        `;
                    }}
                }}
                """

                if tur_adi == "Test Oluştur":
                    st.caption("👇 Önce tüm sorularda cevabını işaretle (seçtiğin şık mavi yanar). Bitirince en alttaki **'🏁 Testi Bitir ve Gönder'** butonuna basarak doğru/yanlış sonuçlarını, çözümleri ve kazandığın **🏆 Kupaları** gör!")
                    optik_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; }}
                        .ct-wrap {{ font-family: 'Inter', -apple-system, sans-serif; padding: 4px 2px; }}
                        .ct-scorebar {{
                            background: linear-gradient(90deg, #1d4ed8 0%, #4f46e5 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 14px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            flex-wrap: wrap;
                            gap: 8px;
                            position: sticky;
                            top: 0;
                            z-index: 10;
                            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22);
                        }}
                        .ct-card {{
                            background: #ffffff;
                            border: 2px solid #e0e7ff;
                            border-radius: 18px;
                            padding: 16px;
                            margin-bottom: 16px;
                            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
                        }}
                        .ct-header {{
                            display: flex;
                            align-items: stretch;
                            gap: 10px;
                            margin-bottom: 12px;
                        }}
                        .ct-num {{
                            background: linear-gradient(90deg, #2563eb, #7c3aed);
                            color: white;
                            font-weight: 800;
                            font-size: 13px;
                            padding: 8px 10px;
                            border-radius: 12px;
                            white-space: nowrap;
                            flex: 0 0 104px;
                            width: 104px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            text-align: center;
                        }}
                        .ct-topic {{
                            background: #eff6ff;
                            border: 1.5px solid #bfdbfe;
                            color: #1d4ed8;
                            font-size: 12.5px;
                            font-weight: 700;
                            padding: 8px 12px;
                            border-radius: 12px;
                            flex: 1 1 auto;
                            min-width: 0;
                            line-height: 1.35;
                            display: flex;
                            align-items: center;
                            text-align: left;
                            word-break: break-word;
                        }}
                        .ct-qtext {{
                            font-size: 15px;
                            font-weight: 700;
                            color: #1e293b;
                            line-height: 1.55;
                            margin-bottom: 14px;
                            white-space: pre-line;
                        }}
                        .ct-opts {{ display: flex; flex-direction: column; gap: 8px; }}
                        .ct-opt {{
                            background: #f8fafc;
                            border: 2px solid #cbd5e1;
                            border-radius: 12px;
                            padding: 11px 14px;
                            font-size: 14px;
                            font-weight: 700;
                            color: #334155;
                            cursor: pointer;
                            text-align: left;
                            transition: all 0.15s ease;
                        }}
                        .ct-opt:hover {{ border-color: #3b82f6; background: #eff6ff; }}
                        .ct-opt.selected {{
                            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
                            border-color: #1e3a8a !important;
                            color: #ffffff !important;
                            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
                        }}
                        .ct-opt.correct {{ background: #dcfce7 !important; border-color: #16a34a !important; color: #14532d !important; }}
                        .ct-opt.wrong {{ background: #fee2e2 !important; border-color: #dc2626 !important; color: #7f1d1d !important; }}
                        .ct-status {{
                            display: none;
                            margin-top: 10px;
                            padding: 9px 12px;
                            border-radius: 10px;
                            font-size: 13.5px;
                            font-weight: 800;
                            text-align: center;
                        }}
                        .ct-status.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .ct-status.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .ct-actions {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }}
                        .ct-act-btn {{
                            border: none;
                            padding: 10px 14px;
                            border-radius: 10px;
                            font-size: 13px;
                            font-weight: 800;
                            cursor: pointer;
                            flex: 1 1 180px;
                            width: 100%;
                            text-align: left;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        }}
                        .ct-act-btn::after {{ content: '▾'; font-size: 12px; opacity: 0.7; }}
                        .ct-btn-hint {{ background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }}
                        .ct-btn-sol {{ background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; display: none; }}
                        .ct-box {{ display: none; margin-top: 10px; padding: 12px; border-radius: 12px; font-size: 13.5px; line-height: 1.5; }}
                        .ct-hint-box {{ background: #fffbeb; color: #78350f; border-left: 5px solid #f59e0b; }}
                        .ct-sol-box {{ background: #f0fdf4; color: #166534; border-left: 5px solid #16a34a; }}
                        .ct-submit-bar {{ margin: 18px 0 10px 0; text-align: center; }}
                        .ct-submit-btn {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: #ffffff;
                            border: none;
                            padding: 15px 20px;
                            border-radius: 16px;
                            font-size: 16px;
                            font-weight: 900;
                            cursor: pointer;
                            box-shadow: 0 6px 18px rgba(22, 163, 74, 0.32);
                        }}
                        .ct-submit-btn:disabled {{ background: #64748b; cursor: default; box-shadow: none; }}
                    </style>
                    <div class="ct-wrap">
                        <div class="ct-scorebar" id="ct-top-bar">
                            <span>📝 SinoTest Optik Durumu (Test)</span>
                            <span id="ct-score">İşaretlenen: 0 / {len(paket_veriler)}</span>
                        </div>
                        <div id="ct-reward-banner" style="display:none;"></div>
                        <div id="ct-root"></div>
                        <div class="ct-submit-bar">
                            <button class="ct-submit-btn" id="ct-finish-btn" onclick="submitCtTest()">🏁 Testi Bitir ve Gönder (Sonuçları, Çözümleri & Kupaları Gör)</button>
                        </div>
                    </div>
                    <script>
                        {ortak_odul_js}
                        const qs = {v_json};
                        const userChoices = {{}};
                        let isSubmitted = false;
                        const rt = document.getElementById('ct-root');
                        const harfler = ['A', 'B', 'C', 'D'];
                        qs.forEach((q, qIdx) => {{
                            const card = document.createElement('div');
                            card.className = 'ct-card';
                            const stdNo = 'Soru ' + (qIdx + 1);
                            const topicTxt = q.kazanim || '{paket_baslik}';
                            const qText = q.soru || q.cumle || q.ifade || '';
                            const opts = (q.secenekler || []).map((opt, oIdx) =>
                                `<button class="ct-opt" id="ctopt-${{qIdx}}-${{oIdx}}" data-raw="${{encodeURIComponent(opt)}}" onclick="selCtOpt(${{qIdx}}, ${{oIdx}})">${{opt}}</button>`
                            ).join('');
                            card.innerHTML = `
                                <div class="ct-header">
                                    <span class="ct-num">📌 ${{stdNo}}</span>
                                    <span class="ct-topic">🎯 ${{topicTxt}}</span>
                                </div>
                                <div class="ct-qtext">${{qText}}</div>
                                <div class="ct-opts">${{opts}}</div>
                                <div class="ct-status" id="ctst-${{qIdx}}"></div>
                                <div class="ct-actions">
                                    <button class="ct-act-btn ct-btn-hint" onclick="togCtBox('cthint-${{qIdx}}')"><span>💡 İpucu Göster</span></button>
                                    <button class="ct-act-btn ct-btn-sol" id="ctbtn-sol-${{qIdx}}" onclick="togCtBox('ctsol-${{qIdx}}')"><span>📖 Adım Adım Çözümü Gör</span></button>
                                </div>
                                <div class="ct-box ct-hint-box" id="cthint-${{qIdx}}"><b>💡 İpucu:</b> ${{q.ipucu || 'Sorudaki anahtar kavramlara dikkat et.'}}</div>
                                <div class="ct-box ct-sol-box" id="ctsol-${{qIdx}}"><b>✅ Adım Adım Çözüm:</b> ${{q.cozum || ''}}</div>
                            `;
                            rt.appendChild(card);
                        }});

                        window.selCtOpt = function(qIdx, oIdx) {{
                            if (isSubmitted) return;
                            userChoices[qIdx] = oIdx;
                            const optList = qs[qIdx].secenekler || [];
                            for (let i = 0; i < optList.length; i++) {{
                                const b = document.getElementById(`ctopt-${{qIdx}}-${{i}}`);
                                if (!b) continue;
                                const rawTxt = decodeURIComponent(b.getAttribute('data-raw'));
                                if (i === oIdx) {{
                                    b.classList.add('selected');
                                    b.innerHTML = '✓ ' + rawTxt;
                                }} else {{
                                    b.classList.remove('selected');
                                    b.innerHTML = rawTxt;
                                }}
                            }}
                            const answeredCount = Object.keys(userChoices).length;
                            document.getElementById('ct-score').innerHTML = `İşaretlenen: ${{answeredCount}} / ${{qs.length}}`;
                        }};

                        window.submitCtTest = function() {{
                            if (isSubmitted) return;
                            isSubmitted = true;
                            let scD = 0, scY = 0, scB = 0;
                            qs.forEach((q, qIdx) => {{
                                const cIdx = q.dogru_index || 0;
                                const uIdx = userChoices[qIdx];
                                const optList = q.secenekler || [];
                                const cBtn = document.getElementById(`ctopt-${{qIdx}}-${{cIdx}}`);
                                const stEl = document.getElementById(`ctst-${{qIdx}}`);
                                const solBtn = document.getElementById(`ctbtn-sol-${{qIdx}}`);
                                const dogruEtiket = harfler[cIdx] || '';

                                for (let i = 0; i < optList.length; i++) {{
                                    const b = document.getElementById(`ctopt-${{qIdx}}-${{i}}`);
                                    if (b) {{
                                        b.classList.remove('selected');
                                        b.innerHTML = decodeURIComponent(b.getAttribute('data-raw'));
                                    }}
                                }}

                                if (uIdx === undefined) {{
                                    scB++;
                                    if (cBtn) {{
                                        cBtn.classList.add('correct');
                                        cBtn.innerHTML += ' &nbsp; ✔️ <b>Doğru Cevap</b>';
                                    }}
                                    stEl.className = 'ct-status err';
                                    stEl.innerHTML = `⚪ <b>BOŞ BIRAKILDI!</b> Doğru Cevap: <b>${{dogruEtiket}}</b> — Alttan çözümü incele!`;
                                }} else if (uIdx === cIdx) {{
                                    scD++;
                                    const uBtn = document.getElementById(`ctopt-${{qIdx}}-${{uIdx}}`);
                                    if (uBtn) {{
                                        uBtn.classList.add('correct');
                                        uBtn.innerHTML += ' &nbsp; 🎉 <b>DOĞRU!</b>';
                                    }}
                                    stEl.className = 'ct-status ok';
                                    stEl.innerHTML = `✅ <b>DOĞRU!</b> (${{dogruEtiket}} şıkkı) — Alttaki butondan adım adım çözümü görebilirsin.`;
                                }} else {{
                                    scY++;
                                    const uBtn = document.getElementById(`ctopt-${{qIdx}}-${{uIdx}}`);
                                    const secEtiket = harfler[uIdx] || '';
                                    if (uBtn) {{
                                        uBtn.classList.add('wrong');
                                        uBtn.innerHTML += ' &nbsp; ❌ <b>Senin Seçimin</b>';
                                    }}
                                    if (cBtn) {{
                                        cBtn.classList.add('correct');
                                        cBtn.innerHTML += ' &nbsp; ✔️ <b>Doğru Cevap</b>';
                                    }}
                                    stEl.className = 'ct-status err';
                                    stEl.innerHTML = `❌ <b>YANLIŞ!</b> İşaretlediğin: <b>${{secEtiket}}</b> &nbsp;|&nbsp; Doğru Cevap: <b>${{dogruEtiket}}</b>`;
                                }}
                                stEl.style.display = 'block';
                                solBtn.style.display = 'flex';
                            }});

                            document.getElementById('ct-score').innerHTML = `✅ Doğru: ${{scD}} &nbsp;|&nbsp; ❌ Yanlış: ${{scY}} &nbsp;|&nbsp; ⚪ Boş: ${{scB}}`;
                            const fBtn = document.getElementById('ct-finish-btn');
                            fBtn.disabled = true;
                            fBtn.innerHTML = `✅ Test Tamamlandı — Doğru: ${{scD}} | Yanlış: ${{scY}} | Boş: ${{scB}}`;
                            awardSinoTrophy(qs.length, scD, 'ct-reward-banner');
                            document.getElementById('ct-top-bar').scrollIntoView({{ behavior: 'smooth' }});
                        }};

                        window.togCtBox = function(id) {{
                            const el = document.getElementById(id);
                            el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                        }};
                    </script>
                    """
                    components.html(optik_html, height=min(880, len(paket_veriler) * 350 + 180), scrolling=True)

                elif tur_adi == "Boşluk Doldur":
                    st.caption("👇 Cümledeki boşluğa tıklayıp üstteki **Kelime Havuzu**'ndan kavram seçebilir veya kutucuğa doğrudan yazabilirsin. Bitirince en alttaki **'🏁 Boşlukları Bitir ve Gönder'** butonuna bas!")
                    bosluk_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Inter', -apple-system, sans-serif; }}
                        .bd-wrap {{ padding: 4px 2px; }}
                        .bd-bar {{
                            background: linear-gradient(90deg, #1d4ed8 0%, #4f46e5 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 12px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            flex-wrap: wrap;
                            gap: 8px;
                        }}
                        .bd-bank {{
                            background: #eff6ff;
                            border: 2px dashed #60a5fa;
                            border-radius: 16px;
                            padding: 12px 14px;
                            margin-bottom: 16px;
                        }}
                        .bd-bank-title {{ font-size: 12.5px; font-weight: 800; color: #1e40af; margin-bottom: 8px; }}
                        .bd-words {{ display: flex; flex-wrap: wrap; gap: 8px; }}
                        .bd-word {{
                            background: #ffffff;
                            border: 2px solid #93c5fd;
                            color: #1d4ed8;
                            font-weight: 800;
                            font-size: 13px;
                            padding: 7px 13px;
                            border-radius: 99px;
                            cursor: pointer;
                            transition: all 0.15s ease;
                        }}
                        .bd-word:hover {{ background: #2563eb; color: #ffffff; border-color: #1e3a8a; }}
                        .bd-card {{
                            background: #ffffff;
                            border: 2px solid #e2e8f0;
                            border-radius: 16px;
                            padding: 15px;
                            margin-bottom: 12px;
                            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
                        }}
                        .bd-head {{ display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }}
                        .bd-num {{
                            background: linear-gradient(90deg, #2563eb, #7c3aed);
                            color: white;
                            font-weight: 800;
                            font-size: 12.5px;
                            padding: 6px 12px;
                            border-radius: 10px;
                            white-space: nowrap;
                        }}
                        .bd-topic {{
                            background: #f1f5f9;
                            color: #334155;
                            font-size: 12px;
                            font-weight: 700;
                            padding: 6px 10px;
                            border-radius: 10px;
                            flex: 1;
                        }}
                        .bd-sentence {{
                            font-size: 15px;
                            font-weight: 700;
                            color: #0f172a;
                            line-height: 1.8;
                        }}
                        .bd-input {{
                            display: inline-block;
                            min-width: 150px;
                            padding: 6px 12px;
                            margin: 0 4px;
                            border: 2px solid #2563eb;
                            border-radius: 10px;
                            background: #eff6ff;
                            color: #1e3a8a;
                            font-weight: 800;
                            font-size: 14px;
                            text-align: center;
                            outline: none;
                        }}
                        .bd-input:focus, .bd-input.active-slot {{
                            background: #dbeafe;
                            border-color: #1d4ed8;
                            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.22);
                        }}
                        .bd-input.correct {{ background: #dcfce7 !important; border-color: #16a34a !important; color: #14532d !important; }}
                        .bd-input.wrong {{ background: #fee2e2 !important; border-color: #dc2626 !important; color: #7f1d1d !important; }}
                        .bd-fb {{ display: none; margin-top: 10px; padding: 10px 12px; border-radius: 10px; font-size: 13px; font-weight: 700; }}
                        .bd-fb.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .bd-fb.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .bd-submit {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            padding: 15px;
                            border-radius: 16px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            margin-top: 10px;
                            box-shadow: 0 6px 16px rgba(22, 163, 74, 0.28);
                        }}
                        .bd-submit:disabled {{ background: #64748b; cursor: default; box-shadow: none; }}
                    </style>
                    <div class="bd-wrap">
                        <div class="bd-bar" id="bd-top">
                            <span>✏️ Boşluk Doldurma Etkinliği</span>
                            <span id="bd-score">Doldurulan: 0 / {len(paket_veriler)}</span>
                        </div>
                        <div id="bd-reward-banner" style="display:none;"></div>
                        <div class="bd-bank">
                            <div class="bd-bank-title">🎯 Kelime Havuzu (Önce aşağıdaki bir boşluğa tıkla, sonra buradaki kelimeye dokun veya klavyeyle yaz):</div>
                            <div class="bd-words" id="bd-words"></div>
                        </div>
                        <div id="bd-root"></div>
                        <button class="bd-submit" id="bd-finish" onclick="gradeBd()">🏁 Boşlukları Bitir ve Gönder (Sonuçları & Kupaları Gör)</button>
                    </div>
                    <script>
                        {ortak_odul_js}
                        const rawItems = {v_json};
                        const items = rawItems.map((it, idx) => {{
                            let ans = it.cevap || it.dogru_cevap || '';
                            if (!ans && Array.isArray(it.secenekler)) {{
                                const di = it.dogru_index || 0;
                                ans = String(it.secenekler[di] || '').replace(/^[A-Da-d][\\)\\.\\-\\s]+/, '').trim();
                            }}
                            let sent = it.cumle || it.soru || it.ifade || '';
                            if (!sent.includes('___')) sent = sent + ' _______';
                            return {{
                                kazanim: it.kazanim || ('Soru ' + (idx + 1)),
                                cumle: sent,
                                cevap: ans,
                                ipucu: it.ipucu || '',
                                cozum: it.cozum || ''
                            }};
                        }});

                        let activeSlot = 0;
                        let isSubmitted = false;

                        const wordsPool = items.map(x => x.cevap).filter(Boolean);
                        for (let i = wordsPool.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [wordsPool[i], wordsPool[j]] = [wordsPool[j], wordsPool[i]];
                        }}
                        const wContainer = document.getElementById('bd-words');
                        wordsPool.forEach(w => {{
                            const b = document.createElement('button');
                            b.className = 'bd-word';
                            b.textContent = w;
                            b.onclick = function() {{
                                if (isSubmitted) return;
                                const inp = document.getElementById('bdinp-' + activeSlot);
                                if (inp) {{
                                    inp.value = w;
                                    updateBdCount();
                                    if (activeSlot + 1 < items.length) setActiveSlot(activeSlot + 1);
                                }}
                            }};
                            wContainer.appendChild(b);
                        }});

                        const root = document.getElementById('bd-root');
                        items.forEach((it, idx) => {{
                            const card = document.createElement('div');
                            card.className = 'bd-card';
                            const parts = it.cumle.split(/_{2,}/);
                            const inputHtml = `<input type="text" class="bd-input ${{idx === 0 ? 'active-slot' : ''}}" id="bdinp-${{idx}}" placeholder="Boşluk ${{idx + 1}}..." onfocus="setActiveSlot(${{idx}})" oninput="updateBdCount()" />`;
                            const fullSentence = parts.length > 1 ? (parts[0] + inputHtml + parts.slice(1).join(' ')) : (it.cumle + ' ' + inputHtml);
                            card.innerHTML = `
                                <div class="bd-head">
                                    <span class="bd-num">📌 Soru ${{idx + 1}}</span>
                                    <span class="bd-topic">🎯 ${{it.kazanim}}</span>
                                </div>
                                <div class="bd-sentence">${{fullSentence}}</div>
                                <div class="bd-fb" id="bdfb-${{idx}}"></div>
                            `;
                            root.appendChild(card);
                        }});

                        window.setActiveSlot = function(idx) {{
                            activeSlot = idx;
                            items.forEach((_, i) => {{
                                const el = document.getElementById('bdinp-' + i);
                                if (el) el.classList.toggle('active-slot', i === idx);
                            }});
                        }};

                        window.updateBdCount = function() {{
                            let filled = 0;
                            items.forEach((_, i) => {{
                                const el = document.getElementById('bdinp-' + i);
                                if (el && el.value.trim() !== '') filled++;
                            }});
                            document.getElementById('bd-score').innerHTML = `Doldurulan: ${{filled}} / ${{items.length}}`;
                        }};

                        function normTr(s) {{
                            return String(s || '').trim().toLocaleLowerCase('tr-TR').replace(/[.,!?;:'"()-]/g, '').replace(/\\s+/g, ' ');
                        }}

                        window.gradeBd = function() {{
                            if (isSubmitted) return;
                            isSubmitted = true;
                            let d = 0, y = 0, b = 0;
                            items.forEach((it, i) => {{
                                const inp = document.getElementById('bdinp-' + i);
                                const fb = document.getElementById('bdfb-' + i);
                                const uVal = inp ? inp.value.trim() : '';
                                if (inp) {{
                                    inp.disabled = true;
                                    inp.classList.remove('active-slot');
                                }}
                                if (!uVal) {{
                                    b++;
                                    if (inp) inp.classList.add('wrong');
                                    fb.className = 'bd-fb err';
                                    fb.innerHTML = `⚪ <b>BOŞ BIRAKILDI!</b> Doğru Kavram: <b>${{it.cevap}}</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }} else if (normTr(uVal) === normTr(it.cevap)) {{
                                    d++;
                                    if (inp) inp.classList.add('correct');
                                    fb.className = 'bd-fb ok';
                                    fb.innerHTML = `✅ <b>DOĞRU! (${{it.cevap}})</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }} else {{
                                    y++;
                                    if (inp) inp.classList.add('wrong');
                                    fb.className = 'bd-fb err';
                                    fb.innerHTML = `❌ <b>YANLIŞ!</b> Yazdığın: <b>${{uVal}}</b> &nbsp;|&nbsp; Doğru Kavram: <b>${{it.cevap}}</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }}
                                fb.style.display = 'block';
                            }});
                            document.getElementById('bd-score').innerHTML = `✅ Doğru: ${{d}} | ❌ Yanlış: ${{y}} | ⚪ Boş: ${{b}}`;
                            const btn = document.getElementById('bd-finish');
                            btn.disabled = true;
                            btn.innerHTML = `✅ Tamamlandı — Doğru: ${{d}} | Yanlış: ${{y}} | Boş: ${{b}}`;
                            awardSinoTrophy(items.length, d, 'bd-reward-banner');
                            document.getElementById('bd-top').scrollIntoView({{ behavior: 'smooth' }});
                        }};
                    </script>
                    """
                    components.html(bosluk_html, height=min(880, len(paket_veriler) * 190 + 260), scrolling=True)

                elif tur_adi == "Doğru/Yanlış":
                    st.caption("👇 Her cümlenin altındaki **'✅ DOĞRU'** veya **'❌ YANLIŞ'** butonuna bas (seçtiğin mavi yanar). Bitirince en alttaki **'🏁 Doğru/Yanlış'ı Bitir ve Gönder'** butonuna bas!")
                    dy_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Inter', -apple-system, sans-serif; }}
                        .dy-wrap {{ padding: 4px 2px; }}
                        .dy-bar {{
                            background: linear-gradient(90deg, #1d4ed8 0%, #4f46e5 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 14px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }}
                        .dy-card {{
                            background: #ffffff;
                            border: 2px solid #e2e8f0;
                            border-radius: 16px;
                            padding: 16px;
                            margin-bottom: 12px;
                            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
                        }}
                        .dy-head {{ display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }}
                        .dy-num {{
                            background: linear-gradient(90deg, #2563eb, #7c3aed);
                            color: white;
                            font-weight: 800;
                            font-size: 12.5px;
                            padding: 6px 12px;
                            border-radius: 10px;
                        }}
                        .dy-topic {{
                            background: #eff6ff;
                            color: #1d4ed8;
                            font-size: 12px;
                            font-weight: 700;
                            padding: 6px 10px;
                            border-radius: 10px;
                            flex: 1;
                        }}
                        .dy-text {{
                            font-size: 15px;
                            font-weight: 700;
                            color: #0f172a;
                            line-height: 1.55;
                            margin-bottom: 12px;
                        }}
                        .dy-btns {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
                        .dy-btn {{
                            background: #f8fafc;
                            border: 2px solid #cbd5e1;
                            border-radius: 12px;
                            padding: 11px 14px;
                            font-size: 14px;
                            font-weight: 800;
                            color: #334155;
                            cursor: pointer;
                            transition: all 0.15s ease;
                        }}
                        .dy-btn:hover {{ border-color: #3b82f6; background: #eff6ff; }}
                        .dy-btn.selected {{
                            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
                            border-color: #1e3a8a !important;
                            color: #ffffff !important;
                            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
                        }}
                        .dy-btn.correct {{ background: #dcfce7 !important; border-color: #16a34a !important; color: #14532d !important; }}
                        .dy-btn.wrong {{ background: #fee2e2 !important; border-color: #dc2626 !important; color: #7f1d1d !important; }}
                        .dy-fb {{ display: none; margin-top: 10px; padding: 10px 12px; border-radius: 10px; font-size: 13px; font-weight: 700; }}
                        .dy-fb.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .dy-fb.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .dy-submit {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            padding: 15px;
                            border-radius: 16px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            margin-top: 10px;
                        }}
                        .dy-submit:disabled {{ background: #64748b; cursor: default; }}
                    </style>
                    <div class="dy-wrap">
                        <div class="dy-bar" id="dy-top">
                            <span>✅ Doğru / Yanlış Etkinliği</span>
                            <span id="dy-score">İşaretlenen: 0 / {len(paket_veriler)}</span>
                        </div>
                        <div id="dy-reward-banner" style="display:none;"></div>
                        <div id="dy-root"></div>
                        <button class="dy-submit" id="dy-finish" onclick="gradeDy()">🏁 Doğru/Yanlış'ı Bitir ve Gönder (Sonuçları & Kupaları Gör)</button>
                    </div>
                    <script>
                        {ortak_odul_js}
                        const rawDy = {v_json};
                        const dyItems = rawDy.map((it, idx) => {{
                            const txt = it.ifade || it.soru || it.cumle || '';
                            let isTrue = true;
                            if (typeof it.dogru_mu === 'boolean') isTrue = it.dogru_mu;
                            else if (typeof it.dogru_index === 'number') isTrue = (it.dogru_index === 0);
                            return {{
                                kazanim: it.kazanim || ('Madde ' + (idx + 1)),
                                ifade: txt,
                                dogru_mu: isTrue,
                                cozum: it.cozum || ''
                            }};
                        }});
                        const choices = {{}};
                        let submitted = false;
                        const root = document.getElementById('dy-root');
                        dyItems.forEach((it, idx) => {{
                            const card = document.createElement('div');
                            card.className = 'dy-card';
                            card.innerHTML = `
                                <div class="dy-head">
                                    <span class="dy-num">📌 Madde ${{idx + 1}}</span>
                                    <span class="dy-topic">🎯 ${{it.kazanim}}</span>
                                </div>
                                <div class="dy-text">${{it.ifade}}</div>
                                <div class="dy-btns">
                                    <button class="dy-btn" id="dybtn-${{idx}}-true" onclick="selDy(${{idx}}, true)">✅ DOĞRU</button>
                                    <button class="dy-btn" id="dybtn-${{idx}}-false" onclick="selDy(${{idx}}, false)">❌ YANLIŞ</button>
                                </div>
                                <div class="dy-fb" id="dyfb-${{idx}}"></div>
                            `;
                            root.appendChild(card);
                        }});

                        window.selDy = function(idx, val) {{
                            if (submitted) return;
                            choices[idx] = val;
                            const bT = document.getElementById(`dybtn-${{idx}}-true`);
                            const bF = document.getElementById(`dybtn-${{idx}}-false`);
                            bT.classList.toggle('selected', val === true);
                            bF.classList.toggle('selected', val === false);
                            bT.innerHTML = (val === true ? '✓ ' : '') + '✅ DOĞRU';
                            bF.innerHTML = (val === false ? '✓ ' : '') + '❌ YANLIŞ';
                            document.getElementById('dy-score').innerHTML = `İşaretlenen: ${{Object.keys(choices).length}} / ${{dyItems.length}}`;
                        }};

                        window.gradeDy = function() {{
                            if (submitted) return;
                            submitted = true;
                            let d = 0, y = 0, b = 0;
                            dyItems.forEach((it, idx) => {{
                                const uVal = choices[idx];
                                const cVal = it.dogru_mu;
                                const bT = document.getElementById(`dybtn-${{idx}}-true`);
                                const bF = document.getElementById(`dybtn-${{idx}}-false`);
                                const fb = document.getElementById(`dyfb-${{idx}}`);
                                bT.classList.remove('selected');
                                bF.classList.remove('selected');
                                const cBtn = cVal ? bT : bF;
                                const cLabel = cVal ? 'DOĞRU' : 'YANLIŞ';

                                if (uVal === undefined) {{
                                    b++;
                                    cBtn.classList.add('correct');
                                    fb.className = 'dy-fb err';
                                    fb.innerHTML = `⚪ <b>BOŞ BIRAKILDI!</b> Doğru Cevap: <b>${{cLabel}}</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }} else if (uVal === cVal) {{
                                    d++;
                                    cBtn.classList.add('correct');
                                    fb.className = 'dy-fb ok';
                                    fb.innerHTML = `✅ <b>TEBRİKLER, DOĞRU! (${{cLabel}})</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }} else {{
                                    y++;
                                    const uBtn = uVal ? bT : bF;
                                    uBtn.classList.add('wrong');
                                    cBtn.classList.add('correct');
                                    fb.className = 'dy-fb err';
                                    fb.innerHTML = `❌ <b>YANLIŞ!</b> Doğru Cevap: <b>${{cLabel}}</b><br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }}
                                fb.style.display = 'block';
                            }});
                            document.getElementById('dy-score').innerHTML = `✅ Doğru: ${{d}} | ❌ Yanlış: ${{y}} | ⚪ Boş: ${{b}}`;
                            const fBtn = document.getElementById('dy-finish');
                            fBtn.disabled = true;
                            fBtn.innerHTML = `✅ Tamamlandı — Doğru: ${{d}} | Yanlış: ${{y}} | Boş: ${{b}}`;
                            awardSinoTrophy(dyItems.length, d, 'dy-reward-banner');
                            document.getElementById('dy-top').scrollIntoView({{ behavior: 'smooth' }});
                        }};
                    </script>
                    """
                    components.html(dy_html, height=min(880, len(paket_veriler) * 210 + 180), scrolling=True)

                elif tur_adi == "Flash Kart":
                    st.caption("👇 Kartların üzerine tıklayarak arka yüzündeki **cevabı ve kritik LGS ipucunu** çevirip görebilirsin! Tüm kartları inceledikten sonra alttaki butonla **🏆 Kupalarını** al!")
                    flash_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Inter', -apple-system, sans-serif; }}
                        .fc-bar {{
                            background: linear-gradient(90deg, #1d4ed8 0%, #7c3aed 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 12px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }}
                        .fc-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; padding: 6px 2px; }}
                        .fc-item {{
                            background: #ffffff;
                            border: 2px solid #93c5fd;
                            border-radius: 18px;
                            padding: 18px 16px;
                            min-height: 185px;
                            cursor: pointer;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                            box-shadow: 0 6px 14px rgba(37, 99, 235, 0.08);
                            transition: all 0.2s ease;
                        }}
                        .fc-item:hover {{ transform: translateY(-2px); border-color: #2563eb; }}
                        .fc-item.flipped {{
                            background: linear-gradient(135deg, #eff6ff 0%, #dcfce7 100%);
                            border-color: #16a34a;
                        }}
                        .fc-badge {{
                            display: inline-block;
                            background: #dbeafe;
                            color: #1e40af;
                            font-size: 11.5px;
                            font-weight: 800;
                            padding: 4px 10px;
                            border-radius: 99px;
                            margin-bottom: 10px;
                        }}
                        .fc-item.flipped .fc-badge {{ background: #bbf7d0; color: #166534; }}
                        .fc-body {{ font-size: 14.5px; font-weight: 700; color: #1e293b; line-height: 1.55; }}
                        .fc-foot {{ font-size: 11.5px; color: #2563eb; font-weight: 800; margin-top: 12px; text-align: right; }}
                        .fc-submit {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            padding: 15px;
                            border-radius: 16px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            margin-top: 14px;
                        }}
                        .fc-submit:disabled {{ background: #64748b; cursor: default; }}
                    </style>
                    <div class="fc-bar" id="fc-top">
                        <span>🎴 Flash Kart Çalışması</span>
                        <span id="fc-score">İncelenen Kart: 0 / {len(paket_veriler)}</span>
                    </div>
                    <div id="fc-reward-banner" style="display:none;"></div>
                    <div class="fc-grid" id="fc-root"></div>
                    <button class="fc-submit" id="fc-finish" onclick="finishFc()">🏁 Flash Kartları Tamamladım — Kupamı & Ödülümü Al!</button>
                    <script>
                        {ortak_odul_js}
                        const rawCards = {v_json};
                        const seenSet = new Set();
                        let fcDone = false;
                        const root = document.getElementById('fc-root');
                        rawCards.forEach((c, idx) => {{
                            const frontTxt = c.on_yuz || c.soru || c.kavram || c.front || '';
                            const backTxt = c.arka_yuz || c.cevap || c.aciklama || c.back || '';
                            const topicTxt = c.kazanim || ('Kart ' + (idx + 1));
                            const hintTxt = c.ipucu || '';
                            const el = document.createElement('div');
                            el.className = 'fc-item';
                            el.onclick = function() {{
                                seenSet.add(idx);
                                document.getElementById('fc-score').innerHTML = `İncelenen Kart: ${{seenSet.size}} / ${{rawCards.length}}`;
                                const isF = el.classList.toggle('flipped');
                                const bdg = el.querySelector('.fc-badge');
                                const bdy = el.querySelector('.fc-body');
                                const ft = el.querySelector('.fc-foot');
                                if (isF) {{
                                    bdg.innerHTML = '✅ CEVAP & ÖZET • ' + topicTxt;
                                    bdy.innerHTML = backTxt + (hintTxt ? `<div style="margin-top:8px;font-size:12.5px;color:#15803d;">💡 <b>Püf Noktası:</b> ${{hintTxt}}</div>` : '');
                                    ft.innerHTML = '🔄 Ön yüze (soruya) dönmek için dokun';
                                }} else {{
                                    bdg.innerHTML = '🎴 KART ' + (idx + 1) + ' • ' + topicTxt;
                                    bdy.innerHTML = frontTxt;
                                    ft.innerHTML = '👆 Cevabı görmek için karta dokun';
                                }}
                            }};
                            el.innerHTML = `
                                <div>
                                    <span class="fc-badge">🎴 KART ${{idx + 1}} • ${{topicTxt}}</span>
                                    <div class="fc-body">${{frontTxt}}</div>
                                </div>
                                <div class="fc-foot">👆 Cevabı görmek için karta dokun</div>
                            `;
                            root.appendChild(el);
                        }});
                        window.finishFc = function() {{
                            if (fcDone) return;
                            fcDone = true;
                            const btn = document.getElementById('fc-finish');
                            btn.disabled = true;
                            btn.innerHTML = `✅ Flash Kart Çalışması Tamamlandı (${{rawCards.length}} Kart)`;
                            awardSinoTrophy(rawCards.length, rawCards.length, 'fc-reward-banner');
                            document.getElementById('fc-top').scrollIntoView({{ behavior: 'smooth' }});
                        }};
                    </script>
                    """
                    components.html(flash_html, height=min(860, ((len(paket_veriler) + 1) // 2) * 220 + 170), scrolling=True)

                elif tur_adi == "Eşleştir":
                    st.caption("👇 Her kavramın karşısındaki açılır kutudan eşleşen ifadeyi seç (seçtiğin mavi yanar) ve en alttaki **'🏁 Eşleştirmeyi Bitir ve Gönder'** butonuna bas!")
                    eslestir_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Inter', -apple-system, sans-serif; }}
                        .em-wrap {{ padding: 6px 2px; }}
                        .em-bar {{
                            background: linear-gradient(90deg, #1d4ed8, #7c3aed);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 14px;
                            display: flex;
                            justify-content: space-between;
                        }}
                        .em-row {{
                            background: #ffffff;
                            border: 2px solid #e2e8f0;
                            border-radius: 14px;
                            padding: 13px 14px;
                            margin-bottom: 10px;
                            display: flex;
                            flex-direction: column;
                            gap: 8px;
                        }}
                        .em-left {{ font-size: 14.5px; font-weight: 800; color: #0f172a; line-height: 1.45; }}
                        .em-sel {{
                            width: 100%;
                            padding: 10px 12px;
                            border-radius: 10px;
                            border: 2px solid #cbd5e1;
                            font-size: 13.5px;
                            font-weight: 700;
                            color: #1e293b;
                            background: #f8fafc;
                        }}
                        .em-sel.selected {{ border-color: #2563eb; background: #eff6ff; color: #1d4ed8; }}
                        .em-fb {{ display: none; font-size: 13px; font-weight: 700; padding: 9px 12px; border-radius: 10px; }}
                        .em-fb.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .em-fb.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .em-btn {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            padding: 15px;
                            border-radius: 16px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            margin-top: 10px;
                        }}
                    </style>
                    <div class="em-wrap">
                        <div class="em-bar" id="em-top">
                            <span>🧩 Eşleştirme Etkinliği</span>
                            <span id="em-score">Toplam: {len(paket_veriler)} Eşleşme</span>
                        </div>
                        <div id="em-reward-banner" style="display:none;"></div>
                        <div id="em-root"></div>
                        <button class="em-btn" id="em-submit" onclick="gradeEm()">🏁 Eşleştirmeyi Bitir ve Gönder (Sonuçları & Kupaları Gör)</button>
                    </div>
                    <script>
                        {ortak_odul_js}
                        const rawPairs = {v_json};
                        const pairs = rawPairs.map(p => ({{
                            sol: p.sol || p.kavram || p.terim || p.soru || '',
                            sag: p.sag || p.karsilik || p.tanim || p.cevap || '',
                            aciklama: p.aciklama || ''
                        }}));
                        const rights = pairs.map((p, i) => ({{ idx: i, txt: p.sag }}));
                        for (let i = rights.length - 1; i > 0; i--) {{
                            const j = Math.floor(Math.random() * (i + 1));
                            [rights[i], rights[j]] = [rights[j], rights[i]];
                        }}
                        const root = document.getElementById('em-root');
                        pairs.forEach((p, idx) => {{
                            const row = document.createElement('div');
                            row.className = 'em-row';
                            const opts = `<option value="-1">-- Eşleşen karşılığı seç --</option>` +
                                rights.map(r => `<option value="${{r.idx}}">${{r.txt}}</option>`).join('');
                            row.innerHTML = `
                                <div class="em-left">📌 ${{idx + 1}}. ${{p.sol}}</div>
                                <select class="em-sel" id="emsel-${{idx}}" onchange="this.classList.toggle('selected', this.value !== '-1')">${{opts}}</select>
                                <div class="em-fb" id="emfb-${{idx}}"></div>
                            `;
                            root.appendChild(row);
                        }});
                        window.gradeEm = function() {{
                            let d = 0, y = 0;
                            pairs.forEach((p, idx) => {{
                                const sel = document.getElementById(`emsel-${{idx}}`);
                                const fb = document.getElementById(`emfb-${{idx}}`);
                                const val = parseInt(sel.value, 10);
                                sel.disabled = true;
                                if (val === idx) {{
                                    d++;
                                    fb.className = 'em-fb ok';
                                    fb.innerHTML = `✅ <b>DOĞRU EŞLEŞME!</b> (${{p.sag}}) ${{p.aciklama ? '<br>' + p.aciklama : ''}}`;
                                }} else {{
                                    y++;
                                    fb.className = 'em-fb err';
                                    fb.innerHTML = `❌ <b>Doğru Eşleşme:</b> ${{p.sag}} ${{p.aciklama ? '<br><span style="font-weight:600;">' + p.aciklama + '</span>' : ''}}`;
                                }}
                                fb.style.display = 'block';
                            }});
                            document.getElementById('em-score').innerHTML = `✅ Doğru: ${{d}} | ❌ Yanlış/Boş: ${{y}}`;
                            const btn = document.getElementById('em-submit');
                            btn.disabled = true;
                            btn.style.background = '#64748b';
                            btn.innerHTML = `✅ Eşleştirme Tamamlandı — Doğru: ${{d}} / ${{pairs.length}}`;
                            awardSinoTrophy(pairs.length, d, 'em-reward-banner');
                            document.getElementById('em-top').scrollIntoView({{ behavior: 'smooth' }});
                        }};
                    </script>
                    """
                    components.html(eslestir_html, height=min(880, len(paket_veriler) * 150 + 180), scrolling=True)

                elif tur_adi == "Karıştırma":
                    st.caption("👇 Karışık verilen kelime/adım kutucuklarına **doğru sırayla dokunarak** üstteki cevap alanına diz (geri almak için üstteki kutucuğa tekrar dokun). Bitirince **'🏁 Sıralamayı Bitir ve Gönder'** butonuna bas!")
                    karistir_html = f"""
                    <style>
                        * {{ box-sizing: border-box; }}
                        body {{ margin: 0; padding: 0; background: transparent; font-family: 'Inter', -apple-system, sans-serif; }}
                        .kr-wrap {{ padding: 4px 2px; }}
                        .kr-bar {{
                            background: linear-gradient(90deg, #1d4ed8 0%, #7c3aed 100%);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 14px;
                            font-weight: 800;
                            font-size: 13.5px;
                            margin-bottom: 14px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }}
                        .kr-card {{
                            background: #ffffff;
                            border: 2px solid #e0e7ff;
                            border-radius: 18px;
                            padding: 16px;
                            margin-bottom: 14px;
                            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
                        }}
                        .kr-head {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 10px; }}
                        .kr-num {{
                            background: linear-gradient(90deg, #2563eb, #7c3aed);
                            color: white;
                            font-weight: 800;
                            font-size: 12.5px;
                            padding: 6px 12px;
                            border-radius: 10px;
                        }}
                        .kr-reset {{
                            background: #f1f5f9;
                            border: 1px solid #cbd5e1;
                            color: #475569;
                            font-size: 12px;
                            font-weight: 800;
                            padding: 5px 10px;
                            border-radius: 8px;
                            cursor: pointer;
                        }}
                        .kr-prompt {{ font-size: 14.5px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }}
                        .kr-tray {{
                            min-height: 52px;
                            background: #eff6ff;
                            border: 2px dashed #60a5fa;
                            border-radius: 12px;
                            padding: 10px;
                            margin-bottom: 10px;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 8px;
                            align-items: center;
                        }}
                        .kr-tray-empty {{ font-size: 12.5px; color: #64748b; font-weight: 600; }}
                        .kr-pool {{ display: flex; flex-wrap: wrap; gap: 8px; }}
                        .kr-chip {{
                            background: #ffffff;
                            border: 2px solid #cbd5e1;
                            color: #0f172a;
                            font-weight: 800;
                            font-size: 13.5px;
                            padding: 8px 13px;
                            border-radius: 10px;
                            cursor: pointer;
                            transition: all 0.15s ease;
                        }}
                        .kr-chip:hover {{ border-color: #2563eb; background: #eff6ff; }}
                        .kr-chip.in-tray {{
                            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
                            border-color: #1e3a8a;
                            color: #ffffff;
                        }}
                        .kr-fb {{ display: none; margin-top: 10px; padding: 10px 12px; border-radius: 10px; font-size: 13px; font-weight: 700; }}
                        .kr-fb.ok {{ background: #dcfce7; color: #166534; border: 1.5px solid #86efac; }}
                        .kr-fb.err {{ background: #fee2e2; color: #991b1b; border: 1.5px solid #fca5a5; }}
                        .kr-submit {{
                            width: 100%;
                            background: linear-gradient(135deg, #16a34a 0%, #059669 100%);
                            color: white;
                            border: none;
                            padding: 15px;
                            border-radius: 16px;
                            font-size: 15.5px;
                            font-weight: 900;
                            cursor: pointer;
                            margin-top: 10px;
                        }}
                        .kr-submit:disabled {{ background: #64748b; cursor: default; }}
                    </style>
                    <div class="kr-wrap">
                        <div class="kr-bar" id="kr-top">
                            <span>🔀 Kelime / Kavram Karıştırma (Sıraya Dizme)</span>
                            <span id="kr-score">Tamamlanan: 0 / {len(paket_veriler)}</span>
                        </div>
                        <div id="kr-reward-banner" style="display:none;"></div>
                        <div id="kr-root"></div>
                        <button class="kr-submit" id="kr-finish" onclick="gradeKr()">🏁 Sıralamayı Bitir ve Gönder (Sonuçları & Kupaları Gör)</button>
                    </div>
                    <script>
                        {ortak_odul_js}
                        const rawKr = {v_json};
                        const krItems = rawKr.map((it, idx) => {{
                            let parts = it.parcalar || it.kelimeler || it.adimlar || [];
                            if (!Array.isArray(parts) || parts.length === 0) {{
                                const fallbackStr = it.dogru_dizilis || it.cevap || 'Kavramları doğru sırayla birleştir';
                                parts = String(fallbackStr).split(/\\s+/).filter(Boolean);
                            }}
                            const pool = parts.map((txt, pIdx) => ({{ id: pIdx, txt: String(txt) }}));
                            for (let i = pool.length - 1; i > 0; i--) {{
                                const j = Math.floor(Math.random() * (i + 1));
                                [pool[i], pool[j]] = [pool[j], pool[i]];
                            }}
                            return {{
                                kazanim: it.kazanim || ('Etkinlik ' + (idx + 1)),
                                yonerge: it.yonerge || 'Aşağıdaki karışık parçaları doğru sırayla tıklayarak dizin:',
                                target: parts.map(String),
                                pool: pool,
                                selected: [],
                                cozum: it.cozum || ''
                            }};
                        }});

                        let krSubmitted = false;
                        const root = document.getElementById('kr-root');

                        function renderKrCard(qIdx) {{
                            const it = krItems[qIdx];
                            const trayEl = document.getElementById('krtray-' + qIdx);
                            const poolEl = document.getElementById('krpool-' + qIdx);
                            if (!trayEl || !poolEl) return;

                            if (it.selected.length === 0) {{
                                trayEl.innerHTML = `<span class="kr-tray-empty">👆 Aşağıdaki kutucuklara sırayla dokunarak buraya diz...</span>`;
                            }} else {{
                                trayEl.innerHTML = it.selected.map((pObj, sPos) =>
                                    `<button class="kr-chip in-tray" onclick="unpickKr(${{qIdx}}, ${{sPos}})">${{pObj.txt}} ✕</button>`
                                ).join('');
                            }}

                            const usedIds = new Set(it.selected.map(x => x.id));
                            poolEl.innerHTML = it.pool
                                .filter(pObj => !usedIds.has(pObj.id))
                                .map(pObj => `<button class="kr-chip" onclick="pickKr(${{qIdx}}, ${{pObj.id}})">${{pObj.txt}}</button>`)
                                .join('');

                            const doneCount = krItems.filter(x => x.selected.length > 0).length;
                            document.getElementById('kr-score').innerHTML = `Dizilen: ${{doneCount}} / ${{krItems.length}}`;
                        }}

                        krItems.forEach((it, qIdx) => {{
                            const card = document.createElement('div');
                            card.className = 'kr-card';
                            card.innerHTML = `
                                <div class="kr-head">
                                    <span class="kr-num">📌 Etkinlik ${{qIdx + 1}} • ${{it.kazanim}}</span>
                                    <button class="kr-reset" onclick="resetKr(${{qIdx}})">🔄 Sıfırla</button>
                                </div>
                                <div class="kr-prompt">${{it.yonerge}}</div>
                                <div class="kr-tray" id="krtray-${{qIdx}}"></div>
                                <div class="kr-pool" id="krpool-${{qIdx}}"></div>
                                <div class="kr-fb" id="krfb-${{qIdx}}"></div>
                            `;
                            root.appendChild(card);
                            renderKrCard(qIdx);
                        }});

                        window.pickKr = function(qIdx, pId) {{
                            if (krSubmitted) return;
                            const it = krItems[qIdx];
                            const found = it.pool.find(x => x.id === pId);
                            if (found && !it.selected.some(x => x.id === pId)) {{
                                it.selected.push(found);
                                renderKrCard(qIdx);
                            }}
                        }};

                        window.unpickKr = function(qIdx, sPos) {{
                            if (krSubmitted) return;
                            krItems[qIdx].selected.splice(sPos, 1);
                            renderKrCard(qIdx);
                        }};

                        window.resetKr = function(qIdx) {{
                            if (krSubmitted) return;
                            krItems[qIdx].selected = [];
                            renderKrCard(qIdx);
                        }};

                        window.gradeKr = function() {{
                            if (krSubmitted) return;
                            krSubmitted = true;
                            let d = 0, y = 0;
                            krItems.forEach((it, qIdx) => {{
                                const userStr = it.selected.map(x => x.txt.trim()).join(' ');
                                const targetStr = it.target.map(x => x.trim()).join(' ');
                                const fb = document.getElementById('krfb-' + qIdx);
                                if (userStr.toLocaleLowerCase('tr-TR') === targetStr.toLocaleLowerCase('tr-TR')) {{
                                    d++;
                                    fb.className = 'kr-fb ok';
                                    fb.innerHTML = `✅ <b>HARİKA, DOĞRU DİZİLİŞ!</b> (${{targetStr}})<br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }} else {{
                                    y++;
                                    fb.className = 'kr-fb err';
                                    fb.innerHTML = `❌ <b>Doğru Diziliş:</b> ${{targetStr}}<br><span style="font-weight:600;">💡 ${{it.cozum}}</span>`;
                                }}
                                fb.style.display = 'block';
                            }});
                            document.getElementById('kr-score').innerHTML = `✅ Doğru: ${{d}} | ❌ Yanlış/Eksik: ${{y}}`;
                            const btn = document.getElementById('kr-finish');
                            btn.disabled = true;
                            btn.innerHTML = `✅ Tamamlandı — Doğru: ${{d}} / ${{krItems.length}}`;
                            awardSinoTrophy(krItems.length, d, 'kr-reward-banner');
                            document.getElementById('kr-top').scrollIntoView({{ behavior: 'smooth' }});
                        }};
                    </script>
                    """
                    components.html(karistir_html, height=min(880, len(paket_veriler) * 235 + 180), scrolling=True)

                # Kalıcı Kupa & 20'lik Ders Kupa Barajı Kasaya Kaydetme Butonu
                eklenecek_adet = max(1, len(paket_veriler))
                eklenecek_kupa = eklenecek_adet * 2
                if paket.get("odul_alindi"):
                    st.success(f"🏆 Bu çalışmanın **+{eklenecek_adet} {paket_ders} Kupası** (ve **+{eklenecek_kupa} Genel Kupa**) ödül vitrinine kalıcı olarak eklendi!")
                else:
                    if st.button(
                        f"🏆 +{eklenecek_adet} {paket_ders} Kupasını (Hedef: 20 🏆) Vitrine Kaydet",
                        key=f"claim_cup_{p_idx}_{tur_adi}",
                        use_container_width=True
                    ):
                        kazanilan_odul = sinotest_ilerleme_kaydet(
                            ders_adi=paket_ders,
                            eklenen_soru_sayisi=eklenecek_adet,
                            kazanilan_kupa=eklenecek_kupa
                        )
                        paket["odul_alindi"] = True
                        st.balloons()
                        if kazanilan_odul:
                            st.session_state.son_kazanilan_odul = kazanilan_odul
                        st.rerun()

            if st.session_state.get("son_kazanilan_odul"):
                st.success(f"🎉🎁 **TEBRİKLER! DERS KUPA BARAJI TAMAMLANDI:** {st.session_state.son_kazanilan_odul} — Tüm dersler 20/20 Kupa olduğunda üstteki 3 Hediye Paketinden birini seçebilirsin!")
                st.session_state.son_kazanilan_odul = None




        # Fotoğraftan İkiz Soru Sonucu
        st.markdown("<div id='ikiz-soru-sonuc'></div>", unsafe_allow_html=True)
        if st.session_state.cipko_ana_mod == "fotograftan" and "ikiz_sonuc" in st.session_state and st.session_state.ikiz_sonuc:
            st.markdown("---")
            ikiz_verisi = st.session_state.ikiz_sonuc
            if isinstance(ikiz_verisi, str):
                # Eski metin formatı kalmışsa sözlüğe dönüştür
                ikiz_verisi = {
                    "kazanim": "MEB LGS Kazanım Analizi",
                    "altin_taktik": "Sorudaki anahtar kelimelere dikkat et!",
                    "orijinal_adimlar": [ikiz_verisi],
                    "orijinal_cevap": "✅ Çözüm",
                    "ikiz_soru": "Yeni interaktif görünüm için tekrar '✨ İkiz Sorusunu Üret ve Çöz' butonuna tıkla!",
                    "secenekler": ["A) Seçenek A", "B) Seçenek B", "C) Seçenek C", "D) Seçenek D"],
                    "dogru_index": 0,
                    "ikiz_ipucu": "İpucu için yeni soru üret!",
                    "ikiz_adimlar": ["Adım adım çözüm burada görünecek."]
                }
            
            kazanim_txt = str(ikiz_verisi.get("kazanim", "")).replace("<", "&lt;").replace(">", "&gt;")
            taktik_txt = str(ikiz_verisi.get("altin_taktik", "")).replace("<", "&lt;").replace(">", "&gt;")
            orijinal_cevap_txt = str(ikiz_verisi.get("orijinal_cevap", "")).replace("<", "&lt;").replace(">", "&gt;")
            ikiz_soru_txt = str(ikiz_verisi.get("ikiz_soru", "")).replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            ikiz_ipucu_txt = str(ikiz_verisi.get("ikiz_ipucu", "")).replace("<", "&lt;").replace(">", "&gt;")
            dogru_idx = int(ikiz_verisi.get("dogru_index", 0)) if str(ikiz_verisi.get("dogru_index", 0)).isdigit() else 0
            
            orijinal_adimlar_html = ""
            for s_i, adim in enumerate(ikiz_verisi.get("orijinal_adimlar", [])):
                c_adim = str(adim).replace("<", "&lt;").replace(">", "&gt;")
                orijinal_adimlar_html += f"""
                <div class="step-row">
                    <span class="step-num">{s_i + 1}</span>
                    <span class="step-txt">{c_adim}</span>
                </div>
                """
            
            ikiz_adimlar_html = ""
            for s_i, adim in enumerate(ikiz_verisi.get("ikiz_adimlar", [])):
                c_adim = str(adim).replace("<", "&lt;").replace(">", "&gt;")
                ikiz_adimlar_html += f"""
                <div class="step-row">
                    <span class="step-num" style="background:#10b981;">{s_i + 1}</span>
                    <span class="step-txt">{c_adim}</span>
                </div>
                """
            
            secenekler_json = json.dumps(ikiz_verisi.get("secenekler", ["A)", "B)", "C)", "D)"]), ensure_ascii=False)
            
            ikiz_html = f"""
            <style>
                .tw-wrap {{ font-family: 'Inter', -apple-system, sans-serif; padding: 4px; color: #1e293b; }}
                .tw-banner {{
                    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                    color: white;
                    border-radius: 20px;
                    padding: 20px;
                    margin-bottom: 16px;
                    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
                }}
                .tw-pill {{
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 12px;
                    border-radius: 99px;
                    font-size: 11.5px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }}
                .tw-kazanim {{ font-size: 16px; font-weight: 800; line-height: 1.45; margin-bottom: 12px; }}
                .tw-taktik {{
                    background: rgba(254, 249, 195, 0.95);
                    color: #854d0e;
                    border-radius: 12px;
                    padding: 10px 14px;
                    font-size: 13.5px;
                    font-weight: 700;
                }}
                .tw-card {{
                    background: #ffffff;
                    border: 2px solid #e2e8f0;
                    border-radius: 20px;
                    padding: 20px;
                    margin-bottom: 16px;
                    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
                }}
                .tw-card-title {{
                    font-size: 17px;
                    font-weight: 900;
                    color: #1e293b;
                    margin-bottom: 12px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .step-row {{
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                }}
                .step-num {{
                    background: #4f46e5;
                    color: white;
                    min-width: 24px;
                    height: 24px;
                    border-radius: 99px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 800;
                    margin-top: 1px;
                }}
                .step-txt {{ font-size: 14px; color: #334155; font-weight: 600; line-height: 1.5; }}
                .ans-badge {{
                    display: inline-block;
                    background: #dcfce7;
                    color: #166534;
                    border: 1.5px solid #86efac;
                    padding: 6px 14px;
                    border-radius: 99px;
                    font-size: 13.5px;
                    font-weight: 800;
                    margin-top: 6px;
                }}
                .tw-question-box {{
                    background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
                    border: 2px solid #c7d2fe;
                    border-radius: 16px;
                    padding: 16px;
                    font-size: 15px;
                    font-weight: 700;
                    color: #1e293b;
                    line-height: 1.55;
                    margin-bottom: 14px;
                }}
                .tw-opts {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 10px;
                    margin-bottom: 14px;
                }}
                @media (max-width: 520px) {{
                    .tw-opts {{ grid-template-columns: 1fr; }}
                }}
                .tw-opt-btn {{
                    background: #f8fafc;
                    border: 2px solid #cbd5e1;
                    border-radius: 14px;
                    padding: 12px 16px;
                    font-size: 14.5px;
                    font-weight: 800;
                    color: #1e293b;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s ease;
                }}
                .tw-opt-btn:hover {{
                    border-color: #6366f1;
                    background: #eef2ff;
                    transform: translateY(-2px);
                }}
                .tw-opt-btn.correct {{
                    background: #dcfce7 !important;
                    border-color: #16a34a !important;
                    color: #15803d !important;
                }}
                .tw-opt-btn.wrong {{
                    background: #fee2e2 !important;
                    border-color: #ef4444 !important;
                    color: #b91c1c !important;
                }}
                .tw-actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
                .tw-action-btn {{
                    background: #fef3c7;
                    border: 1.5px solid #fde68a;
                    border-radius: 10px;
                    padding: 9px 14px;
                    font-size: 13px;
                    font-weight: 800;
                    color: #92400e;
                    cursor: pointer;
                }}
                .tw-action-sol {{
                    background: #e0e7ff;
                    border: 1.5px solid #c7d2fe;
                    border-radius: 10px;
                    padding: 9px 14px;
                    font-size: 13px;
                    font-weight: 800;
                    color: #3730a3;
                    cursor: pointer;
                    display: none;
                }}
                .tw-collapse {{
                    display: none;
                    margin-top: 12px;
                    padding: 14px;
                    border-radius: 14px;
                }}
            </style>
            <div class="tw-wrap">
                <div class="tw-banner">
                    <div class="tw-pill">🎯 MEB ALT KAZANIMI & TAKTİK</div>
                    <div class="tw-kazanim">📌 {kazanim_txt}</div>
                    <div class="tw-taktik">⚡ <b>Süper Taktik:</b> {taktik_txt}</div>
                </div>

                <div class="tw-card">
                    <div class="tw-card-title">
                        <span>🧩 Senin Sorunun Adım Adım Çözümü</span>
                    </div>
                    <button class="tw-action-sol" style="display:inline-block; margin-bottom:10px;" onclick="toggleTw('tw-orig-sol')">📖 Senin Sorunun Çözümünü ve Cevabını Gör</button>
                    <div id="tw-orig-sol" class="tw-collapse" style="background:#f8fafc; border:1.5px solid #e2e8f0;">
                        {orijinal_adimlar_html}
                        <div class="ans-badge">🎯 Doğru Cevap: {orijinal_cevap_txt}</div>
                    </div>
                </div>

                <div class="tw-card" style="border-color: #a5b4fc;">
                    <div class="tw-card-title">
                        <span>👯 Şimdi Sıra Sende: İkiz Soru Meydan Okuması!</span>
                        <span style="background:#e0e7ff; color:#3730a3; font-size:12px; padding:4px 10px; border-radius:99px;">Önce Şıkkı İşaretle 👇</span>
                    </div>
                    <div class="tw-question-box">{ikiz_soru_txt}</div>
                    <div class="tw-opts" id="tw-opts-root"></div>
                    <div class="tw-actions">
                        <button class="tw-action-btn" onclick="toggleTw('tw-hint')">💡 İpucu Al</button>
                        <button class="tw-action-sol" id="tw-btn-sol" onclick="toggleTw('tw-sol')">📖 Detaylı Çözümü Gör (Adım Adım)</button>
                    </div>
                    <div id="tw-hint" class="tw-collapse" style="background:#fef9c3; border:1.5px solid #fde047; color:#854d0e; font-weight:700; font-size:13.5px;">
                        💡 <b>İpucu:</b> {ikiz_ipucu_txt}
                    </div>
                    <div id="tw-sol" class="tw-collapse" style="background:#f0fdf4; border:1.5px solid #86efac;">
                        <div style="font-weight:900; color:#166534; margin-bottom:8px; font-size:14.5px;">✅ İkiz Sorunun Adım Adım Çözümü:</div>
                        {ikiz_adimlar_html}
                    </div>
                </div>
            </div>
            <script>
                const opts = {secenekler_json};
                const correctIndex = {dogru_idx};
                let twMarked = false;
                const optsRoot = document.getElementById('tw-opts-root');
                opts.forEach((optText, idx) => {{
                    const b = document.createElement('button');
                    b.className = 'tw-opt-btn';
                    b.id = 'tw-opt-' + idx;
                    b.innerText = optText;
                    b.onclick = function() {{
                        if (twMarked) return;
                        twMarked = true;
                        const cBtn = document.getElementById('tw-opt-' + correctIndex);
                        if (idx === correctIndex) {{
                            b.classList.add('correct');
                            b.innerText += '  🎉 DOĞRU!';
                        }} else {{
                            b.classList.add('wrong');
                            b.innerText += '  ❌ YANLIŞ!';
                            if (cBtn) {{
                                cBtn.classList.add('correct');
                                cBtn.innerText += '  ✔️ Doğru Cevap';
                            }}
                        }}
                        document.getElementById('tw-btn-sol').style.display = 'inline-block';
                    }};
                    optsRoot.appendChild(b);
                }});
                window.toggleTw = function(id) {{
                    const el = document.getElementById(id);
                    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                }};
            </script>
            """
            components.html(ikiz_html, height=740, scrolling=True)
            
            if st.button("💾 Bu Soruyu Hata Defterime Ekle"):
                doc_id = f"soru_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ozet_not = f"{kazanim_txt} | İkiz Soru: {ikiz_verisi.get('ikiz_soru', '')[:180]}"
                data = {
                    "ders": st.session_state.get("ikiz_ders", "Matematik"),
                    "tip": "Soru Çözüm",
                    "not": ozet_not,
                    "tarih": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "hafta": datetime.datetime.now().strftime("%Y-W%V")
                }
                save_user_data(current_user, "hata_defteri", doc_id, data)
                st.success("Soru hata defterine eklendi!")

elif menu == "📷 Deneme Analizi":
    import fitz
    with st.container(border=True):
        st.markdown("### 📷 Deneme Analizi & LGS Puan Hesaplayıcı")
        st.write("1️⃣ Deneme sayfalarının fotoğraflarını yükle, 2️⃣ 6 ders için Doğru / Yanlış / Boş sayılarını gir; sistem hem **LGS Puanını** hesaplasın hem de **Genel Performans** karneni çıkarsın!")
        
        deneme_adi = st.text_input("📝 Deneme Adı / Yayın (İsteğe bağlı):", placeholder="Örn: Özdebir Türkiye Geneli Deneme - 1")
        
        deneme_files = st.file_uploader(
            "📸 Deneme Sayfalarını veya PDF'ini Yükle (Çoklu seçim açık 📚)",
            type=["jpg", "png", "jpeg", "pdf"],
            accept_multiple_files=True
        )
        
        deneme_gorselleri = []
        if deneme_files:
            for df_item in deneme_files:
                if df_item.name.lower().endswith(".pdf"):
                    doc = fitz.open(stream=df_item.getvalue(), filetype="pdf")
                    for p_idx in range(min(10, len(doc))):
                        pix = doc.load_page(p_idx).get_pixmap(dpi=130)
                        deneme_gorselleri.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
                    doc.close()
                else:
                    deneme_gorselleri.append(Image.open(df_item))
            
            st.success(f"📑 Toplam **{len(deneme_gorselleri)} sayfa** yüklendi!")
            with st.expander(f"👁️ Yüklenen Sayfaları Önizle ({len(deneme_gorselleri)} Sayfa)", expanded=False):
                d_cols = st.columns(min(4, len(deneme_gorselleri)))
                for idx, d_img in enumerate(deneme_gorselleri):
                    with d_cols[idx % len(d_cols)]:
                        st.image(d_img, caption=f"Sayfa {idx + 1}")

        st.markdown("---")
        st.markdown("#### 🎯 6 Ders Doğru / Yanlış / Boş Girişi")
        
        ders_ayar = [
            ("📘 Türkçe", "turkce", 20, 4.348),
            ("📐 Matematik", "mat", 20, 4.254),
            ("🧬 Fen Bilimleri", "fen", 20, 4.123),
            ("🏛️ T.C. İnkılap", "ink", 10, 1.666),
            ("🕌 Din Kültürü", "din", 10, 1.899),
            ("🌍 İngilizce", "ing", 10, 1.508),
        ]

        # Varsayılan değerleri bir kez ata (widget'lara value vermeden session_state üzerinden yönetilir)
        for _lbl, _k, _mx, _ks in ders_ayar:
            if f"dn_d_{_k}" not in st.session_state:
                st.session_state[f"dn_d_{_k}"] = _mx - 2
            if f"dn_y_{_k}" not in st.session_state:
                st.session_state[f"dn_y_{_k}"] = 1

        # 🤖 Yüklenen görsellerden D/Y/B otomatik doldurma
        if deneme_gorselleri:
            if st.button("🤖 Görsellerden Doğru / Yanlış / Boş Sayılarını Otomatik Doldur", use_container_width=True, key="dn_auto_fill"):
                with st.spinner("Yapay zeka deneme görsellerini okuyor ve D/Y/B sayılarını çıkarıyor..."):
                    okunan = extract_exam_scores(deneme_gorselleri[:6])
                if okunan:
                    for _lbl, _k, _mx, _ks in ders_ayar:
                        if _k in okunan:
                            st.session_state[f"dn_d_{_k}"] = int(okunan[_k]["D"])
                            st.session_state[f"dn_y_{_k}"] = int(okunan[_k]["Y"])
                    st.session_state.dn_auto_mesaj = f"✅ {len(okunan)} dersin sonuçları görsellerden dolduruldu! Hatalı olan varsa aşağıdan düzeltebilirsin."
                else:
                    st.session_state.dn_auto_mesaj = "⚠️ Görsellerden D/Y/B okunamadı. Sayıları aşağıdan elle girebilirsin."
                st.rerun()
            if st.session_state.get("dn_auto_mesaj"):
                st.info(st.session_state.dn_auto_mesaj)
        else:
            st.caption("💡 Deneme sonuç sayfanı yüklersen yapay zeka Doğru / Yanlış / Boş sayılarını senin yerine otomatik doldurur; yanlış okunan olursa düzeltebilirsin.")

        st.markdown("""
        <style>
            /* D / Y / B kutuları mobilde de yan yana kalsın */
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-dn_d_"]) {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                gap: 6px !important;
            }
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-dn_d_"]) > div[data-testid="stColumn"] {
                min-width: 0 !important;
                width: auto !important;
                flex: 1 1 0% !important;
            }
            div[data-testid="stHorizontalBlock"]:has([class*="st-key-dn_d_"]) div[data-testid="stWidgetLabel"] p {
                font-size: 12px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        net_tablosu = {}
        toplam_d, toplam_y, toplam_b, toplam_net = 0, 0, 0, 0.0
        puan_katkisi = 194.75  # MEB taban puan sabiti
        
        for idx, (d_label, d_key, max_soru, katsayi) in enumerate(ders_ayar):
            with st.container(border=True):
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;'>"
                        f"<span style='font-weight:800; font-size:14.5px; color:#1e293b;'>{d_label}</span>"
                        f"<span style='background:#f1f5f9; color:#475569; font-size:11px; font-weight:700; padding:3px 9px; border-radius:99px;'>Toplam {max_soru} Soru</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    # Sınır dışı değerleri widget çizilmeden önce düzelt
                    st.session_state[f"dn_d_{d_key}"] = max(0, min(max_soru, int(st.session_state[f"dn_d_{d_key}"])))
                    kalan_y = max_soru - st.session_state[f"dn_d_{d_key}"]
                    st.session_state[f"dn_y_{d_key}"] = max(0, min(kalan_y, int(st.session_state[f"dn_y_{d_key}"])))
                    st.session_state[f"dn_b_{d_key}"] = max_soru - st.session_state[f"dn_d_{d_key}"] - st.session_state[f"dn_y_{d_key}"]

                    k1, k2, k3 = st.columns(3, gap="small")
                    with k1:
                        d_say = st.number_input("✅ Doğru", min_value=0, max_value=max_soru, key=f"dn_d_{d_key}")
                    with k2:
                        y_say = st.number_input("❌ Yanlış", min_value=0, max_value=kalan_y, key=f"dn_y_{d_key}")
                    with k3:
                        b_say = max_soru - d_say - y_say
                        st.number_input("⭕ Boş", min_value=0, max_value=max_soru, disabled=True, key=f"dn_b_{d_key}")
                    
                    net = max(0.0, round(d_say - (y_say / 3.0), 2))
                    ders_kisa_ad = d_label.split(" ", 1)[1]
                    st.markdown(
                        f"<div style='background:#f5f3ff; border:1px solid #ddd6fe; border-radius:10px; padding:6px 12px; margin-top:4px; display:flex; justify-content:space-between; align-items:center; gap:8px;'>"
                        f"<span style='font-size:12.5px; font-weight:700; color:#4c1d95; white-space:nowrap;'>✨ {ders_kisa_ad} Neti</span>"
                        f"<span style='background:#6366f1; color:white; font-size:12.5px; font-weight:800; padding:2px 10px; border-radius:99px; white-space:nowrap;'>{net:.2f} / {max_soru}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    
                    net_tablosu[d_label] = {"D": d_say, "Y": y_say, "B": b_say, "Net": net, "Max": max_soru}
                    toplam_d += d_say
                    toplam_y += y_say
                    toplam_b += b_say
                    toplam_net += net
                    puan_katkisi += net * katsayi
        
        lgs_puani = min(500.0, max(100.0, round(puan_katkisi, 2)))
        
        # Anlık Canlı LGS Puan & Net Rozet Kartı (Soft Pastel-Canlı Tema)
        puan_renk = "#10b981" if lgs_puani >= 420 else ("#6366f1" if lgs_puani >= 350 else "#f59e0b")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 55%, #ecfdf5 100%); border: 1.5px solid #c7d2fe; border-radius: 20px; padding: 18px; color: #1e293b; display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 12px; margin: 12px 0; box-shadow: 0 6px 18px rgba(99, 102, 241, 0.10);">
            <div style="text-align: center;">
                <div style="font-size: 11.5px; color: #64748b; font-weight: 700; text-transform: uppercase;">Toplam Doğru / Yanlış / Boş</div>
                <div style="font-size: 18px; font-weight: 800; color: #1e293b; margin-top: 4px;">✅ {toplam_d} D &nbsp;|&nbsp; ❌ {toplam_y} Y &nbsp;|&nbsp; ⭕ {toplam_b} B</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 11.5px; color: #64748b; font-weight: 700; text-transform: uppercase;">Toplam Net (90 Soru)</div>
                <div style="font-size: 22px; font-weight: 900; color: #4f46e5; margin-top: 4px;">{toplam_net:.2f} Net</div>
            </div>
            <div style="text-align: center; background: {puan_renk}; padding: 10px 22px; border-radius: 16px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.10);">
                <div style="font-size: 11px; color: rgba(255,255,255,0.92); font-weight: 800; text-transform: uppercase;">🏆 MEB LGS Puanı</div>
                <div style="font-size: 26px; font-weight: 900; color: white;">{lgs_puani:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 LGS Puanımı Hesapla & Genel Performans Analizi Çıkar", use_container_width=True):
            ozet_str = f"LGS Puanı: {lgs_puani:.2f} | Toplam Net: {toplam_net:.2f}/90\n"
            for d_lbl, ver in net_tablosu.items():
                ozet_str += f"- {d_lbl}: {ver['D']} Doğru, {ver['Y']} Yanlış, {ver['B']} Boş -> {ver['Net']} Net\n"
            
            with st.spinner("Yapay zeka koçun fotoğrafları ve netlerini inceleyip Genel Performans karneni hazırlıyor..."):
                # Çok fazla sayfa varsa hız için ilk 6 sayfayı modele gönder
                gonderilecek_img = deneme_gorselleri[:6] if deneme_gorselleri else None
                st.session_state.deneme_analiz_json = analyze_exam_sheet(image=gonderilecek_img, netler_ozeti=ozet_str)
                st.session_state.deneme_son_puan = lgs_puani
                st.session_state.deneme_son_net = round(toplam_net, 2)
                st.session_state.deneme_son_ad = deneme_adi if deneme_adi else f"Deneme ({datetime.datetime.now().strftime('%d.%m.%Y')})"
                st.session_state.hedef_scroll = "deneme-analiz-sonuc"

        st.markdown("<div id='deneme-analiz-sonuc'></div>", unsafe_allow_html=True)
        if st.session_state.get("deneme_analiz_json"):
            analiz_d = st.session_state.deneme_analiz_json
            genel_perf = str(analiz_d.get("genel_performans", "")).replace("<", "&lt;").replace(">", "&gt;")
            hedef_txt = str(analiz_d.get("haftanin_hedefi", "")).replace("<", "&lt;").replace(">", "&gt;")
            
            # ERGEN DOSTU GÖRSEL "GENEL PERFORMANS" KARTI
            perf_html = f"""
            <style>
                .perf-wrap {{ font-family: 'Inter', sans-serif; padding: 6px 2px; }}
                .perf-hero {{
                    background: linear-gradient(135deg, #5b6cf9 0%, #8b5cf6 100%);
                    color: white;
                    border-radius: 20px;
                    padding: 22px;
                    margin-bottom: 16px;
                    box-shadow: 0 8px 20px rgba(91, 108, 249, 0.18);
                }}
                .perf-badge {{
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 12px;
                    border-radius: 99px;
                    font-size: 11.5px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }}
                .perf-title {{ font-size: 20px; font-weight: 900; margin-bottom: 8px; }}
                .perf-desc {{ font-size: 14.5px; line-height: 1.55; opacity: 0.95; font-weight: 500; }}
                .ders-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 12px;
                    margin-bottom: 16px;
                }}
                .ders-card {{
                    background: #f8fafc;
                    border: 1.5px solid #e2e8f0;
                    border-left: 5px solid #6366f1;
                    border-radius: 14px;
                    padding: 14px;
                    transition: transform 0.2s ease;
                    cursor: pointer;
                }}
                .ders-card:hover {{ transform: translateY(-2px); background: #eff6ff; }}
                .ders-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
                .ders-name {{ font-size: 14.5px; font-weight: 800; color: #1e293b; }}
                .ders-tag {{
                    background: #e0e7ff; color: #3730a3; font-size: 11px;
                    font-weight: 800; padding: 3px 8px; border-radius: 99px;
                }}
                .ders-body {{ font-size: 13px; color: #475569; line-height: 1.45; font-weight: 500; }}
                .hedef-box {{
                    background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                    border: 2px dashed #10b981;
                    border-radius: 16px;
                    padding: 16px;
                    color: #065f46;
                }}
            </style>
            <div class="perf-wrap">
                <div class="perf-hero">
                    <div class="perf-badge">✨ YAPAY ZEKA KOÇ DEĞERLENDİRMESİ</div>
                    <div class="perf-title">🌟 Genel Performans</div>
                    <div class="perf-desc">{genel_perf}</div>
                </div>
                <div class="ders-grid">
            """
            for da in analiz_d.get("ders_analizleri", []):
                em = str(da.get("emoji", "📘"))
                dn = str(da.get("ders", "")).replace("<", "&lt;").replace(">", "&gt;")
                dr = str(da.get("durum", "")).replace("<", "&lt;").replace(">", "&gt;")
                kt = str(da.get("kazanim_ve_taktik", "")).replace("<", "&lt;").replace(">", "&gt;")
                perf_html += f"""
                <div class="ders-card" onclick="this.style.borderLeftColor='#10b981'; this.style.background='#f0fdf4';">
                    <div class="ders-top">
                        <span class="ders-name">{em} {dn}</span>
                        <span class="ders-tag">{dr}</span>
                    </div>
                    <div class="ders-body">{kt}</div>
                </div>
                """
            perf_html += f"""
                </div>
                <div class="hedef-box">
                    <div style="font-weight: 900; font-size: 13.5px; text-transform: uppercase;">🎯 Bir Sonraki Deneme Hedefin</div>
                    <div style="font-weight: 700; font-size: 14.5px; margin-top: 4px;">{hedef_txt}</div>
                </div>
            </div>
            """
            components.html(perf_html, height=540, scrolling=True)
            
            if st.button("💾 Bu Deneme Sonucunu ve Puanımı Gelişim Karneme Kaydet", use_container_width=True):
                doc_id = f"deneme_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                data = {
                    "deneme_adi": st.session_state.get("deneme_son_ad", "Genel Deneme"),
                    "ders": "Genel Deneme",
                    "tip": "Deneme Karnesi",
                    "toplam_net": st.session_state.get("deneme_son_net", round(toplam_net, 2)),
                    "lgs_puani": st.session_state.get("deneme_son_puan", lgs_puani),
                    "not": f"Puan: {lgs_puani} | Net: {toplam_net:.2f} | {genel_perf[:250]}",
                    "tarih": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "hafta": datetime.datetime.now().strftime("%Y-W%V")
                }
                save_user_data(current_user, "denemeler", doc_id, data)
                st.balloons()
                st.success(f"🎉 Harika! {lgs_puani} puanlık deneme sonucun gelişim karnene başarıyla kaydedildi!")

elif menu == "❌ Hata & Gelişim":
    with st.container(border=True):
        st.markdown("### 📈 Deneme ve Haftalık Gelişim Trendi")
        user_denemeler = get_user_data(current_user, "denemeler")
        user_hatalar = get_user_data(current_user, "hata_defteri")
        tum_veriler = {**user_denemeler, **user_hatalar}
        
        if tum_veriler:
            df_gelisim = pd.DataFrame.from_dict(tum_veriler, orient="index")
            if "tip" not in df_gelisim.columns:
                df_gelisim["tip"] = "Kayıt"
            if "hafta" in df_gelisim.columns:
                st.markdown("#### 📅 Haftalık Deneme & Hata Değişim Grafiği")
                hafta_pivot = df_gelisim.pivot_table(index="hafta", columns="tip", aggfunc="size", fill_value=0)
                st.bar_chart(hafta_pivot)
            else:
                st.bar_chart(df_gelisim["tip"].value_counts())
                
            st.markdown("#### 🔍 Detaylı Gelişim Karnesi")
            st.dataframe(df_gelisim, use_container_width=True)
        else:
            st.info("Henüz deneme veya soru verisi yok.")

# Tıklanan Butonun İlgili Bölümüne Otomatik Yumuşak Kaydırma (Auto-Scroll)
if st.session_state.get("hedef_scroll"):
    hedef_id = st.session_state.hedef_scroll
    st.session_state.hedef_scroll = None
    components.html(f"""
    <script>
        setTimeout(function() {{
            try {{
                const el = window.parent.document.getElementById('{hedef_id}');
                if (el) {{
                    el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }} catch (e) {{}}
        }}, 180);
    </script>
    """, height=0)

