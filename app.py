import streamlit as st
import streamlit.components.v1 as components
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
    get_youtube_transcript,
    generate_flashcards_list,
    generate_hap_ozet_structured,
    generate_lgs_quiz_list,
    solve_page_questions_structured
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

# --- MODERN, TEMİZ VE KULLANICI DOSTU ÖZEL CSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
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
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .user-pill {
        background: #eff6ff;
        color: #1d4ed8;
        padding: 6px 14px;
        border-radius: 99px;
        font-size: 13.5px;
        font-weight: 700;
        border: 1px solid #bfdbfe;
    }
    /* Hero Kartı */
    .hero-card {
        background: linear-gradient(135deg, #1e40af 0%, #6d28d9 100%);
        color: white !important;
        padding: 28px;
        border-radius: 24px;
        box-shadow: 0 12px 30px rgba(37, 99, 235, 0.25);
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .hero-card h2, .hero-card span, .hero-card div {
        color: #ffffff !important;
    }
    .hero-card p {
        color: #e0e7ff !important;
        font-size: 15.5px;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.18);
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
    p, label, li, div[data-testid="stMarkdownContainer"] {
        color: #334155;
    }
    /* Tüm Butonlar ve 📋 Menü (Popover) Butonu Aynı Mavi-Mor Gradyan Stilde */
    .stButton > button,
    div[data-testid="stPopover"] button,
    [data-testid="stPopover"] > div > button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button p, .stButton > button span, .stButton > button div,
    div[data-testid="stPopover"] button p, div[data-testid="stPopover"] button span,
    div[data-testid="stPopover"] button div, div[data-testid="stPopover"] button svg {
        background: transparent !important;
        color: white !important;
        fill: white !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .stButton > button:hover, div[data-testid="stPopover"] > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
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
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<div style='text-align: center; padding: 10px 0;'>", unsafe_allow_html=True)
            st.markdown("<div class='brand-title' style='font-size: 30px;'>🎯 LGS Karargahı</div>", unsafe_allow_html=True)
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

def geri_git():
    if len(st.session_state.nav_gecmisi) > 0:
        hedef = st.session_state.nav_gecmisi.pop()
        st.session_state.aktif_istasyon = hedef
        st.session_state.onceki_secim = hedef
    else:
        st.session_state.aktif_istasyon = "🏠 Ana Sayfa"
        st.session_state.onceki_secim = "🏠 Ana Sayfa"

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

# Mobil Hızlı Kontrol Çubuğu (⬅️ Geri | 🏠 Ana Sayfa | 📋 Hızlı Menü | 🚪 Çıkış)
m_col1, m_col2, m_col3, m_col4 = st.columns([1.1, 1.3, 1.4, 1], gap="small")
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

# 6 İstasyon İçin Soft Renkli, Hizalı 3x2 Tıklanabilir Buton Izgarası
ISTASYON_KISA_AD = [
    ("🏠 Ana Sayfa", "🏠 Ana Sayfa"),
    ("📚 PDF Havuzu", "📚 PDF Havuzu"),
    ("⚡ Hızlı Öğren", "⚡ Hızlı Öğren (Video/Kaynak)"),
    ("🤖 Soru Çöz & İkiz", "🤖 Soru Çöz & İkiz"),
    ("📷 Deneme Analizi", "📷 Deneme Analizi"),
    ("❌ Hata & Gelişim", "❌ Hata & Gelişim"),
]

st.markdown("""
<style>
    /* 6 İstasyon Butonu İçin Ayrı Soft Pastel Renkler ve Tam Hizalama */
    div[class*="st-key-ist_btn_"] button {
        min-height: 50px !important;
        border-radius: 14px !important;
        font-size: 14.5px !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.05) !important;
        transition: all 0.2s ease !important;
    }
    div[class*="st-key-ist_btn_"] button:hover {
        transform: translateY(-2px) !important;
        filter: brightness(0.97) !important;
    }
    /* 0: Ana Sayfa - Soft Gökyüzü Mavisi */
    .st-key-ist_btn_0 button {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
        border: 2px solid #7dd3fc !important;
    }
    .st-key-ist_btn_0 button p, .st-key-ist_btn_0 button span, .st-key-ist_btn_0 button div {
        color: #0369a1 !important;
    }
    /* 1: PDF Havuzu - Soft Lavanta Moru */
    .st-key-ist_btn_1 button {
        background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%) !important;
        border: 2px solid #d8b4fe !important;
    }
    .st-key-ist_btn_1 button p, .st-key-ist_btn_1 button span, .st-key-ist_btn_1 button div {
        color: #6b21a8 !important;
    }
    /* 2: Hızlı Öğren - Soft Şeftali / Kehribar */
    .st-key-ist_btn_2 button {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
        border: 2px solid #fcd34d !important;
    }
    .st-key-ist_btn_2 button p, .st-key-ist_btn_2 button span, .st-key-ist_btn_2 button div {
        color: #92400e !important;
    }
    /* 3: Soru Çöz & İkiz - Soft Nane Yeşili */
    .st-key-ist_btn_3 button {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
        border: 2px solid #6ee7b7 !important;
    }
    .st-key-ist_btn_3 button p, .st-key-ist_btn_3 button span, .st-key-ist_btn_3 button div {
        color: #065f46 !important;
    }
    /* 4: Deneme Analizi - Soft Gül Kurusu / Pembe */
    .st-key-ist_btn_4 button {
        background: linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%) !important;
        border: 2px solid #fda4af !important;
    }
    .st-key-ist_btn_4 button p, .st-key-ist_btn_4 button span, .st-key-ist_btn_4 button div {
        color: #9f1239 !important;
    }
    /* 5: Hata & Gelişim - Soft İndigo */
    .st-key-ist_btn_5 button {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%) !important;
        border: 2px solid #a5b4fc !important;
    }
    .st-key-ist_btn_5 button p, .st-key-ist_btn_5 button span, .st-key-ist_btn_5 button div {
        color: #3730a3 !important;
    }
</style>
""", unsafe_allow_html=True)

with st.container(border=True):
    r1_c1, r1_c2, r1_c3 = st.columns(3, gap="small")
    r2_c1, r2_c2, r2_c3 = st.columns(3, gap="small")
    grid_cols = [r1_c1, r1_c2, r1_c3, r2_c1, r2_c2, r2_c3]
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
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: white !important;
        text-decoration: none !important;
        padding: 12px 16px;
        border-radius: 99px;
        font-weight: 800;
        font-size: 13.5px;
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.4);
        display: flex;
        align-items: center;
        gap: 6px;
        border: 2px solid rgba(255,255,255,0.85);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .fab-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 26px rgba(37, 99, 235, 0.55);
    }
</style>
<div class="floating-nav">
    <a href="#sayfa-basi" class="fab-btn" title="En Üste Çık">⬆️ Yukarı Çık</a>
</div>
""", unsafe_allow_html=True)

# ----------------- MODÜLLER -----------------

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
            st.button("📚 Kütüphaneyi Aç →", on_click=istasyona_git, args=("📚 PDF Havuzu",), key="go_pdf")
            
        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>🤖</div>
                <div class='station-title'>Soru Çöz & İkiz Üret</div>
                <div class='station-desc' style='margin-bottom: 12px;'>Takıldığın sorunun fotoğrafını yükle, adım adım çözümünü ve MEB ikizini al.</div>
            """, unsafe_allow_html=True)
            st.button("🤖 Soru Çözücüye Git →", on_click=istasyona_git, args=("🤖 Soru Çöz & İkiz",), key="go_soru")

    with c2:
        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>⚡</div>
                <div class='station-title'>Hızlı Öğren & 3D Flashcard</div>
                <div class='station-desc' style='margin-bottom: 12px;'>Konu yaz veya YouTube videosu ekle; 3D çevirmeli kartlar, podcast ve mini testlerle öğren.</div>
            """, unsafe_allow_html=True)
            st.button("⚡ Hızlı Öğren'e Git →", on_click=istasyona_git, args=("⚡ Hızlı Öğren (Video/Kaynak)",), key="go_hizli")

        with st.container(border=True):
            st.markdown("""
                <div class='station-icon'>📷</div>
                <div class='station-title'>Deneme Optik & Karnem</div>
                <div class='station-desc' style='margin-bottom: 12px;'>6 ders deneme sonuç belgeni yükle, zayıf kazanımlarını ve haftalık gelişimini gör.</div>
            """, unsafe_allow_html=True)
            st.button("📷 Deneme Analizine Git →", on_click=istasyona_git, args=("📷 Deneme Analizi",), key="go_deneme")
        
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
    from pathlib import Path
    
    pdf_lib_dir = Path("pdf_kutuphanesi")
    pdf_lib_dir.mkdir(exist_ok=True)
    
    st.markdown("<div class='karargah-card'>", unsafe_allow_html=True)
    st.markdown("### 📚 Dijital PDF & Soru Kütüphanesi")
    st.write("Anne tarafından yüklenen ders notları, testler ve denemeler kalıcı olarak bu kütüphaneye kaydedilir. İstediğin kitaba/teste tıklayıp hemen açabilir ve üzerinde çalışabilirsin!")
    
    with st.expander("➕ Kütüphaneye Yeni PDF / Test Yükle", expanded=False):
        ders_etiketi = st.selectbox("Hangi Ders?", ["Matematik", "Fen Bilimleri", "Türkçe", "T.C. İnkılap Tarihi", "Din Kültürü", "İngilizce", "Genel Deneme"], key="lib_ders")
        yuklenen_pdf = st.file_uploader("PDF Dosyası Seç", type=["pdf"], key="lib_uploader")
        if yuklenen_pdf:
            hedef_dosya = pdf_lib_dir / f"[{ders_etiketi}] {yuklenen_pdf.name}"
            if not hedef_dosya.exists():
                hedef_dosya.write_bytes(yuklenen_pdf.getvalue())
                st.success(f"✅ '{yuklenen_pdf.name}' kütüphaneye kalıcı olarak eklendi!")
            else:
                st.info(f"📁 '{yuklenen_pdf.name}' zaten kütüphanede mevcut.")
            st.session_state.secili_pdf = str(hedef_dosya)
    
    st.markdown("---")
    st.markdown("#### 📖 Kütüphanedeki Kaynaklar *(Açmak için kaynağa tıkla)*")
    
    kayitli_pdfler = sorted(pdf_lib_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not kayitli_pdfler:
        st.info("Kütüphanede henüz kayıtlı bir PDF yok. Yukarıdaki '➕ Kütüphaneye Yeni PDF / Test Yükle' bölümünden ilk kaynağını ekleyebilirsin!")
    else:
        # Kitaplık Grid Görünümü (2 sütunlu kartlar)
        cols = st.columns(2)
        for idx, pdf_path in enumerate(kayitli_pdfler):
            col = cols[idx % 2]
            with col:
                boyut_mb = pdf_path.stat().st_size / (1024 * 1024)
                secili_mi = (st.session_state.get("secili_pdf") == str(pdf_path))
                kart_stili = "border: 2px solid #2563eb; background: #eff6ff;" if secili_mi else "border: 1px solid #e2e8f0; background: #f8fafc;"
                st.markdown(f"""
                <div style='{kart_stili} padding: 14px; border-radius: 14px; margin-bottom: 8px;'>
                    <div style='font-size: 15px; font-weight: 800; color: #1e293b;'>📕 {pdf_path.stem}</div>
                    <div style='font-size: 12px; color: #64748b; margin-top: 4px;'>Boyut: {boyut_mb:.1f} MB</div>
                </div>
                """, unsafe_allow_html=True)
                c_ac, c_sil = st.columns([3, 1])
                with c_ac:
                    if st.button("📖 Kitabı Aç", key=f"open_{idx}"):
                        st.session_state.secili_pdf = str(pdf_path)
                        st.session_state.pdf_sayfa_no = 1
                        st.session_state.pdf_ai_sonuc = None
                        st.rerun()
                with c_sil:
                    if st.button("🗑️", key=f"del_{idx}"):
                        if st.session_state.get("secili_pdf") == str(pdf_path):
                            st.session_state.secili_pdf = None
                        pdf_path.unlink(missing_ok=True)
                        st.rerun()
        
        # SEÇİLEN PDF'İ OKUMA VE ÇALIŞMA EKRANI
        secili_yol = st.session_state.get("secili_pdf")
        if secili_yol and Path(secili_yol).exists():
            aktif_pdf = Path(secili_yol)
            doc = fitz.open(str(aktif_pdf))
            toplam_sayfa = len(doc)
            
            st.markdown("---")
            st.markdown(f"### 📖 Açık Kaynak: **{aktif_pdf.stem}** *(Toplam {toplam_sayfa} Sayfa)*")
            
            if "pdf_sayfa_no" not in st.session_state:
                st.session_state.pdf_sayfa_no = 1
            st.session_state.pdf_sayfa_no = max(1, min(toplam_sayfa, st.session_state.pdf_sayfa_no))
            
            # Sayfa Geçiş Kontrolleri
            nav1, nav2, nav3, nav4 = st.columns([1, 2, 1, 1.5])
            with nav1:
                if st.button("⬅️ Önceki") and st.session_state.pdf_sayfa_no > 1:
                    st.session_state.pdf_sayfa_no -= 1
                    st.session_state.pdf_ai_sonuc = None
                    st.rerun()
            with nav2:
                secilen_s = st.number_input("Sayfaya Git:", min_value=1, max_value=toplam_sayfa, value=st.session_state.pdf_sayfa_no, label_visibility="collapsed")
                if secilen_s != st.session_state.pdf_sayfa_no:
                    st.session_state.pdf_sayfa_no = secilen_s
                    st.session_state.pdf_ai_sonuc = None
                    st.rerun()
            with nav3:
                if st.button("Sonraki ➡️") and st.session_state.pdf_sayfa_no < toplam_sayfa:
                    st.session_state.pdf_sayfa_no += 1
                    st.session_state.pdf_ai_sonuc = None
                    st.rerun()
            with nav4:
                with open(aktif_pdf, "rb") as f_dl:
                    st.download_button("📥 PDF İndir", data=f_dl, file_name=aktif_pdf.name, mime="application/pdf")
            
            # Aktif Sayfayı Yüksek Çözünürlüklü Görsel Olarak Göster (Taranmış PDF'lerde bile %100 çalışır)
            sayfa_index = st.session_state.pdf_sayfa_no - 1
            page = doc.load_page(sayfa_index)
            pix = page.get_pixmap(dpi=150)
            sayfa_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            st.image(sayfa_img, caption=f"{aktif_pdf.stem} — Sayfa {st.session_state.pdf_sayfa_no} / {toplam_sayfa}")
            
            # Bu Sayfa Üzerinde İnteraktif Yapay Zeka İşlemleri
            st.markdown("#### 🎮 Bu Sayfayla Ne Yapmak İstersin?")
            b_coz, b_ikiz, b_ozet = st.columns(3)
            with b_coz:
                if st.button("🧠 Soruları İnteraktif Çöz"):
                    with st.spinner(f"Sayfa {st.session_state.pdf_sayfa_no} inceleniyor, adım adım çözüm kartları hazırlanıyor..."):
                        st.session_state.pdf_cozum_kartlari = solve_page_questions_structured(sayfa_img)
                        st.session_state.pdf_ikiz_quiz = None
                        st.session_state.pdf_ozet_kart = None
            with b_ikiz:
                if st.button("🎯 İkiz Soru Meydan Okuması"):
                    with st.spinner("Bu sayfadaki soruların MEB ikizleri hazırlanıyor..."):
                        st.session_state.pdf_ikiz_quiz = generate_lgs_quiz_list(image=sayfa_img)
                        st.session_state.pdf_cozum_kartlari = None
                        st.session_state.pdf_ozet_kart = None
            with b_ozet:
                if st.button("🚀 Sayfayı Hap Özetle"):
                    with st.spinner("Sayfadaki kazanımlar infografik özete dönüştürülüyor..."):
                        st.session_state.pdf_ozet_kart = generate_hap_ozet_structured(image=sayfa_img)
                        st.session_state.pdf_cozum_kartlari = None
                        st.session_state.pdf_ikiz_quiz = None
            
            # 1) İNTERAKTİF ADIM ADIM SORU ÇÖZÜM KARTLARI
            if st.session_state.get("pdf_cozum_kartlari"):
                st.markdown("---")
                st.markdown("#### 🧩 İnteraktif Soru Çözüm İstasyonu *(İpucunu aç, adımları tek tek gör ve cevabı kontrol et!)*")
                cozum_json = json.dumps(st.session_state.pdf_cozum_kartlari, ensure_ascii=False)
                cozum_html = f"""
                <style>
                    .sol-wrap {{ font-family: 'Inter', sans-serif; padding: 4px; display: flex; flex-direction: column; gap: 16px; }}
                    .sol-card {{
                        background: white;
                        border: 2px solid #e0e7ff;
                        border-radius: 18px;
                        padding: 18px;
                        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.06);
                    }}
                    .sol-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
                    .sol-num {{
                        background: linear-gradient(90deg, #2563eb, #7c3aed);
                        color: white;
                        font-weight: 800;
                        font-size: 13px;
                        padding: 5px 12px;
                        border-radius: 99px;
                    }}
                    .sol-kazanim {{
                        background: #eff6ff;
                        color: #1d4ed8;
                        font-size: 12px;
                        font-weight: 700;
                        padding: 4px 10px;
                        border-radius: 8px;
                    }}
                    .sol-btn-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }}
                    .sol-action-btn {{
                        border: none;
                        padding: 9px 14px;
                        border-radius: 10px;
                        font-size: 13px;
                        font-weight: 700;
                        cursor: pointer;
                        transition: transform 0.15s ease;
                    }}
                    .sol-action-btn:hover {{ transform: translateY(-2px); }}
                    .btn-hint {{ background: #fef3c7; color: #92400e; }}
                    .btn-steps {{ background: #e0e7ff; color: #3730a3; }}
                    .btn-ans {{ background: #dcfce7; color: #166534; }}
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
                    .panel-ans {{
                        background: linear-gradient(135deg, #10b981, #059669);
                        color: white;
                        font-size: 16px;
                        font-weight: 800;
                        text-align: center;
                    }}
                    .step-item {{
                        padding: 8px 10px;
                        margin-bottom: 6px;
                        background: white;
                        border-radius: 8px;
                        border: 1px solid #e2e8f0;
                        font-weight: 600;
                    }}
                </style>
                <div class="sol-wrap" id="sol-root"></div>
                <script>
                    const items = {cozum_json};
                    const root = document.getElementById('sol-root');
                    items.forEach((item, idx) => {{
                        const card = document.createElement('div');
                        card.className = 'sol-card';
                        const stepsHtml = (item.adimlar || []).map(s => `<div class="step-item">👉 ${{s}}</div>`).join('');
                        card.innerHTML = `
                            <div class="sol-header">
                                <span class="sol-num">📌 ${{item.soru_no || ('Soru ' + (idx+1))}}</span>
                                <span class="sol-kazanim">🎯 ${{item.kazanim || 'LGS Kazanımı'}}</span>
                            </div>
                            <div class="sol-btn-row">
                                <button class="sol-action-btn btn-hint" onclick="toggleP('sh-${{idx}}')">💡 1. İpucunu Göster</button>
                                <button class="sol-action-btn btn-steps" onclick="toggleP('ss-${{idx}}')">👣 2. Adım Adım Çözümü Aç</button>
                                <button class="sol-action-btn btn-ans" onclick="toggleP('sa-${{idx}}')">🏆 3. Doğru Şıkkı Gör</button>
                            </div>
                            <div class="sol-panel panel-hint" id="sh-${{idx}}"><b>💡 Püf Nokta:</b> ${{item.ipucu || ''}}</div>
                            <div class="sol-panel panel-steps" id="ss-${{idx}}">${{stepsHtml}}</div>
                            <div class="sol-panel panel-ans" id="sa-${{idx}}">🎉 Doğru Cevap: ${{item.dogru_sik || ''}}</div>
                        `;
                        root.appendChild(card);
                    }});
                    window.toggleP = function(id) {{
                        const el = document.getElementById(id);
                        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                    }};
                </script>
                """
                components.html(cozum_html, height=min(650, len(st.session_state.pdf_cozum_kartlari) * 230 + 60), scrolling=True)

            # 2) BU SAYFADAN İNTERAKTİF İKİZ SORU MEYDAN OKUMASI
            if st.session_state.get("pdf_ikiz_quiz"):
                st.markdown("---")
                st.markdown("#### 🎯 Bu Sayfanın İkiz Soru Arenası *(Şıklara tıkla, kendini test et!)*")
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
                        padding: 11px 14px; font-size: 14px; font-weight: 600; color: #334155;
                        cursor: pointer; text-align: left;
                    }}
                    .q-opt.correct {{ background: #dcfce7 !important; border-color: #16a34a !important; color: #14532d !important; }}
                    .q-opt.wrong {{ background: #fee2e2 !important; border-color: #dc2626 !important; color: #7f1d1d !important; }}
                    .q-actions {{ display: flex; gap: 10px; margin-top: 12px; }}
                    .q-btn-small {{
                        background: #f1f5f9; border: none; padding: 7px 12px; border-radius: 8px;
                        font-size: 12px; font-weight: 700; color: #475569; cursor: pointer;
                    }}
                    .q-box {{ display: none; margin-top: 10px; padding: 12px; border-radius: 12px; font-size: 13.5px; }}
                    .q-hint-box {{ background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }}
                    .q-sol-box {{ background: #f0fdf4; color: #166534; border: 1px solid #86efac; }}
                </style>
                <div class="q-container">
                    <div class="q-scorebar">
                        <span>⚡ İkiz Soru Meydan Okuması</span>
                        <span id="p-score">Skor: 0 / {len(q_data)} 🏆</span>
                    </div>
                    <div id="p-quiz-root"></div>
                </div>
                <script>
                    const qs = {q_json};
                    let sc = 0;
                    const ans = new Set();
                    const rt = document.getElementById('p-quiz-root');
                    qs.forEach((q, qIdx) => {{
                        const card = document.createElement('div');
                        card.className = 'q-card';
                        const opts = (q.secenekler || []).map((opt, oIdx) =>
                            `<button class="q-opt" id="popt-${{qIdx}}-${{oIdx}}" onclick="selPOpt(${{qIdx}}, ${{oIdx}}, ${{q.dogru_index}})">${{opt}}</button>`
                        ).join('');
                        card.innerHTML = `
                            <div class="q-badge">🔥 İkiz Soru ${{qIdx + 1}}</div>
                            <div class="q-text">${{q.soru}}</div>
                            <div class="q-options">${{opts}}</div>
                            <div class="q-actions">
                                <button class="q-btn-small" onclick="togPBox('phint-${{qIdx}}')">💡 İpucu Al</button>
                                <button class="q-btn-small" onclick="togPBox('psol-${{qIdx}}')">📖 Çözümü Gör</button>
                            </div>
                            <div class="q-box q-hint-box" id="phint-${{qIdx}}"><b>💡 İpucu:</b> ${{q.ipucu || ''}}</div>
                            <div class="q-box q-sol-box" id="psol-${{qIdx}}"><b>✅ Çözüm:</b> ${{q.cozum || ''}}</div>
                        `;
                        rt.appendChild(card);
                    }});
                    window.selPOpt = function(qIdx, oIdx, cIdx) {{
                        const btn = document.getElementById(`popt-${{qIdx}}-${{oIdx}}`);
                        const sol = document.getElementById(`psol-${{qIdx}}`);
                        if (oIdx === cIdx) {{
                            btn.classList.add('correct');
                            btn.innerHTML += ' &nbsp; 🎉 <b>DOĞRU!</b>';
                            sol.style.display = 'block';
                            if (!ans.has(qIdx)) {{
                                sc++; ans.add(qIdx);
                                document.getElementById('p-score').innerText = `Skor: ${{sc}} / ${{qs.length}} 🏆`;
                            }}
                        }} else {{
                            btn.classList.add('wrong');
                            btn.innerHTML += ' &nbsp; ❌ <b>Tekrar Dene!</b>';
                            ans.add(qIdx);
                        }}
                    }};
                    window.togPBox = function(id) {{
                        const el = document.getElementById(id);
                        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                    }};
                </script>
                """
                components.html(ikiz_html, height=len(q_data) * 340 + 80, scrolling=True)

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
    st.markdown("</div>", unsafe_allow_html=True)

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
        
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("🎧 Hap Özet & Ses"):
                with st.spinner("İnfografik Hap Özet ve Podcast hazırlanıyor..."):
                    ozet_data = generate_hap_ozet_structured(kaynak_metni)
                    st.session_state.hizli_ozet_data = ozet_data
                    st.session_state.hizli_flashcards = None
                    st.session_state.hizli_quiz = None
                    ses_metni = ozet_data.get("ses_metni") or " ".join([m.get("detay", "") for m in ozet_data.get("maddeler", [])])
                    tts = gTTS(text=ses_metni, lang='tr')
                    tts.save("hapis_ozet.mp3")
                    st.session_state.hizli_ses = "hapis_ozet.mp3"
        with col_b2:
            if st.button("📇 Flashcard Üret"):
                with st.spinner("İnteraktif Flashcard kartları tasarlanıyor..."):
                    st.session_state.hizli_flashcards = generate_flashcards_list(kaynak_metni)
                    st.session_state.hizli_ozet_data = None
                    st.session_state.hizli_quiz = None
                    st.session_state.hizli_ses = None
        with col_b3:
            if st.button("📝 LGS Sorusu Üret"):
                with st.spinner("İnteraktif LGS Mini Yarışması hazırlanıyor..."):
                    st.session_state.hizli_quiz = generate_lgs_quiz_list(kaynak_metni)
                    st.session_state.hizli_ozet_data = None
                    st.session_state.hizli_flashcards = None
                    st.session_state.hizli_ses = None

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
                    <span id="score-text">Skor: 0 / {len(quiz_data)} ✨</span>
                </div>
                <div id="quiz-root"></div>
            </div>
            <script>
                const questions = {quiz_json_str};
                let score = 0;
                const answered = new Set();
                const root = document.getElementById('quiz-root');

                questions.forEach((q, qIdx) => {{
                    const card = document.createElement('div');
                    card.className = 'q-card';
                    
                    let optsHtml = '';
                    (q.secenekler || []).forEach((opt, oIdx) => {{
                        optsHtml += `<button class="q-opt" id="opt-${{qIdx}}-${{oIdx}}" onclick="selectOpt(${{qIdx}}, ${{oIdx}}, ${{q.dogru_index}})">${{opt}}</button>`;
                    }});

                    card.innerHTML = `
                        <div class="q-badge">🔥 Soru ${{qIdx + 1}}</div>
                        <div class="q-text">${{q.soru}}</div>
                        <div class="q-options">${{optsHtml}}</div>
                        <div class="q-actions">
                            <button class="q-btn-small" onclick="toggleBox('hint-${{qIdx}}')">💡 İpucu Al</button>
                            <button class="q-btn-small" onclick="toggleBox('sol-${{qIdx}}')">📖 Çözümü Gör</button>
                        </div>
                        <div class="q-box q-hint-box" id="hint-${{qIdx}}"><b>💡 İpucu:</b> ${{q.ipucu || 'Sorudaki anahtar kelimelere dikkat et!'}}</div>
                        <div class="q-box q-sol-box" id="sol-${{qIdx}}"><b>✅ Adım Adım Çözüm:</b> ${{q.cozum || ''}}</div>
                    `;
                    root.appendChild(card);
                }});

                window.selectOpt = function(qIdx, oIdx, correctIdx) {{
                    const btn = document.getElementById(`opt-${{qIdx}}-${{oIdx}}`);
                    const solBox = document.getElementById(`sol-${{qIdx}}`);
                    if (oIdx === correctIdx) {{
                        btn.classList.add('correct');
                        btn.innerHTML += ' &nbsp; 🎉 <b>DOĞRU!</b>';
                        solBox.style.display = 'block';
                        if (!answered.has(qIdx)) {{
                            score++;
                            answered.add(qIdx);
                            document.getElementById('score-text').innerText = `Skor: ${{score}} / ${{questions.length}} 🏆`;
                        }}
                    }} else {{
                        btn.classList.add('wrong');
                        btn.innerHTML += ' &nbsp; ❌ <b>Tekrar Dene!</b>';
                        answered.add(qIdx);
                    }}
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
    with st.container(border=True):
        st.markdown("### 🤖 Çipko Soru Çözücü & İkiz Soru Üretici")
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
                    doc = fitz.open(stream=uf.read(), filetype="pdf")
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
        
        if st.button("✨ İkiz Sorusunu Üret ve Çöz"):
            with st.spinner("Yapay zeka yüklenen tüm sayfaları inceliyor ve ikiz soruyu tasarlıyor..."):
                st.session_state.ikiz_sonuc = generate_twin_question(
                    f"[{ders_secimi}] {soru_metni}",
                    image=soru_gorselleri if soru_gorselleri else None
                )
                st.session_state.ikiz_ders = ders_secimi
                
        if "ikiz_sonuc" in st.session_state and st.session_state.ikiz_sonuc:
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
                    background: #f1f5f9;
                    border: 1.5px solid #cbd5e1;
                    border-radius: 10px;
                    padding: 8px 14px;
                    font-size: 13px;
                    font-weight: 800;
                    color: #334155;
                    cursor: pointer;
                }}
                .tw-action-btn:hover {{ background: #e2e8f0; }}
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
                    {orijinal_adimlar_html}
                    <div class="ans-badge">🎯 Doğru Cevap: {orijinal_cevap_txt}</div>
                </div>

                <div class="tw-card" style="border-color: #a5b4fc;">
                    <div class="tw-card-title">
                        <span>👯 Şimdi Sıra Sende: İkiz Soru Meydan Okuması!</span>
                        <span style="background:#e0e7ff; color:#3730a3; font-size:12px; padding:4px 10px; border-radius:99px;">Şıkka Tıkla 👇</span>
                    </div>
                    <div class="tw-question-box">{ikiz_soru_txt}</div>
                    <div class="tw-opts" id="tw-opts-root"></div>
                    <div class="tw-actions">
                        <button class="tw-action-btn" onclick="toggleTw('tw-hint')">💡 İpucu Al</button>
                        <button class="tw-action-btn" onclick="toggleTw('tw-sol')">📖 Detaylı Çözümü Gör (Adım Adım)</button>
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
                const optsRoot = document.getElementById('tw-opts-root');
                opts.forEach((optText, idx) => {{
                    const b = document.createElement('button');
                    b.className = 'tw-opt-btn';
                    b.id = 'tw-opt-' + idx;
                    b.innerText = optText;
                    b.onclick = function() {{
                        if (idx === correctIndex) {{
                            b.classList.add('correct');
                            if (!b.innerText.includes('DOĞRU')) b.innerText += '  🎉 DOĞRU!';
                            document.getElementById('tw-sol').style.display = 'block';
                        }} else {{
                            b.classList.add('wrong');
                            if (!b.innerText.includes('Tekrar')) b.innerText += '  ❌ Tekrar Dene!';
                        }}
                    }};
                    optsRoot.appendChild(b);
                }});
                window.toggleTw = function(id) {{
                    const el = document.getElementById(id);
                    el.style.display = (el.style.display === 'block') ? 'none' : 'block';
                }};
            </script>
            """
            components.html(ikiz_html, height=720, scrolling=True)
            
            if st.button("💾 Bu Soruyu Hata Defterime Ekle"):
                doc_id = f"soru_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ozet_not = f"{kazanim_txt} | İkiz Soru: {ikiz_verisi.get('ikiz_soru', '')[:180]}"
                data = {
                    "ders": st.session_state.get("ikiz_ders", ders_secimi),
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
                    doc = fitz.open(stream=df_item.read(), filetype="pdf")
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
        
        net_tablosu = {}
        toplam_d, toplam_y, toplam_b, toplam_net = 0, 0, 0, 0.0
        puan_katkisi = 194.75  # MEB taban puan sabiti
        
        c_left, c_right = st.columns(2, gap="medium")
        for idx, (d_label, d_key, max_soru, katsayi) in enumerate(ders_ayar):
            hedef_col = c_left if idx < 3 else c_right
            with hedef_col:
                with st.container(border=True):
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>"
                        f"<span style='font-weight:800; font-size:15.5px; color:#1e293b;'>{d_label}</span>"
                        f"<span style='background:#f1f5f9; color:#475569; font-size:11.5px; font-weight:700; padding:3px 10px; border-radius:99px;'>Toplam {max_soru} Soru</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    k1, k2, k3 = st.columns(3, gap="small")
                    with k1:
                        d_say = st.number_input("✅ Doğru", min_value=0, max_value=max_soru, value=max_soru - 2, key=f"dn_d_{d_key}")
                    with k2:
                        kalan_y = max_soru - d_say
                        y_say = st.number_input("❌ Yanlış", min_value=0, max_value=kalan_y, value=min(1, kalan_y), key=f"dn_y_{d_key}")
                    with k3:
                        b_say = max_soru - d_say - y_say
                        st.number_input("⭕ Boş", min_value=0, max_value=max_soru, value=b_say, disabled=True, key=f"dn_b_{d_key}")
                    
                    net = max(0.0, round(d_say - (y_say / 3.0), 2))
                    ders_kisa_ad = d_label.split(" ", 1)[1]
                    st.markdown(
                        f"<div style='background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:7px 12px; margin-top:6px; display:flex; justify-content:space-between; align-items:center;'>"
                        f"<span style='font-size:13px; font-weight:700; color:#1e40af;'>✨ {ders_kisa_ad} Neti</span>"
                        f"<span style='background:#2563eb; color:white; font-size:13px; font-weight:800; padding:2px 10px; border-radius:99px;'>{net:.2f} / {max_soru}</span>"
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
        
        # Anlık Canlı LGS Puan & Net Rozet Kartı
        puan_renk = "#10b981" if lgs_puani >= 420 else ("#6366f1" if lgs_puani >= 350 else "#f59e0b")
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 20px; padding: 20px; color: white; display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 12px; margin: 12px 0; box-shadow: 0 10px 25px rgba(15,23,42,0.18);">
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Toplam Doğru / Yanlış / Boş</div>
                <div style="font-size: 20px; font-weight: 800; color: #f8fafc; margin-top: 4px;">✅ {toplam_d} D &nbsp;|&nbsp; ❌ {toplam_y} Y &nbsp;|&nbsp; ⭕ {toplam_b} B</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Toplam Net (90 Soru)</div>
                <div style="font-size: 24px; font-weight: 900; color: #38bdf8; margin-top: 4px;">{toplam_net:.2f} Net</div>
            </div>
            <div style="text-align: center; background: {puan_renk}; padding: 10px 22px; border-radius: 16px;">
                <div style="font-size: 11px; color: rgba(255,255,255,0.9); font-weight: 800; text-transform: uppercase;">🏆 MEB LGS Puanı</div>
                <div style="font-size: 28px; font-weight: 900; color: white;">{lgs_puani:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 LGS Puanımı Hesapla & Genel Performans Analizi Çıkar"):
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

        if st.session_state.get("deneme_analiz_json"):
            analiz_d = st.session_state.deneme_analiz_json
            genel_perf = str(analiz_d.get("genel_performans", "")).replace("<", "&lt;").replace(">", "&gt;")
            hedef_txt = str(analiz_d.get("haftanin_hedefi", "")).replace("<", "&lt;").replace(">", "&gt;")
            
            # ERGEN DOSTU GÖRSEL "GENEL PERFORMANS" KARTI
            perf_html = f"""
            <style>
                .perf-wrap {{ font-family: 'Inter', sans-serif; padding: 6px 2px; }}
                .perf-hero {{
                    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
                    color: white;
                    border-radius: 20px;
                    padding: 22px;
                    margin-bottom: 16px;
                    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2);
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
            
            if st.button("💾 Bu Deneme Sonucunu ve Puanımı Gelişim Karneme Kaydet"):
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
    st.markdown("<div class='karargah-card'>", unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)
