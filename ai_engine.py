import os
import json
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
import re

desktop_path = Path.home() / "Desktop"
env_path = desktop_path / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv(override=True)

def _get_gemini_key():
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        try:
            key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        except Exception:
            key = ""
    return key

def ask_gemini(prompt, image=None):
    try:
        current_key = _get_gemini_key()
        genai.configure(api_key=current_key, transport="rest")
        model = genai.GenerativeModel(
            'gemini-3.5-flash-lite',
            generation_config={"max_output_tokens": 8192, "temperature": 0.7}
        )
        if image:
            if isinstance(image, list):
                response = model.generate_content([prompt] + image)
            else:
                response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Yapay zeka hata oluştu: {e}"

def get_youtube_transcript(url):
    """YouTube linkinden video ID'sini çözer ve altyazı metnini çeker."""
    try:
        video_id = None
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "watch?v=" in url:
            match = re.search(r"watch\?v=([a-zA-Z0-9_-]+)", url)
            if match:
                video_id = match.group(1)
        elif "/shorts/" in url or "/live/" in url or "/embed/" in url:
            match = re.search(r"(?:shorts|live|embed)/([a-zA-Z0-9_-]+)", url)
            if match:
                video_id = match.group(1)
        
        if video_id:
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])
                full_text = " ".join([t['text'] for t in transcript_list])
            else:
                ytt_api = YouTubeTranscriptApi()
                fetched = ytt_api.fetch(video_id, languages=['tr', 'en'])
                full_text = " ".join([snippet.text for snippet in fetched])
            return full_text
        return None
    except Exception as e:
        return None

import json

def clean_math_text(val):
    """LaTeX ($m^2$, 10^3, \sqrt, \frac vb.) ifadelerini temiz ve okunaklı Unicode sembollere dönüştürür."""
    if isinstance(val, list):
        return [clean_math_text(v) for v in val]
    if isinstance(val, dict):
        return {k: clean_math_text(v) for k, v in val.items()}
    if not isinstance(val, str):
        return val
    text = val
    # $...$ işaretlerini kaldır
    text = re.sub(r"\$([^$]+)\$", r"\1", text)
    # Kesirleri \frac{a}{b} -> a/b yap
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1/\2)", text)
    # Karekök \sqrt{x} -> √x
    text = re.sub(r"\\sqrt\{([^}]+)\}", r"√(\1)", text)
    text = text.replace("\\sqrt", "√").replace("\\cdot", "·").replace("\\times", "×").replace("\\div", "÷")
    text = text.replace("\\pi", "π").replace("\\leq", "≤").replace("\\geq", "≥").replace("\\neq", "≠")
    text = text.replace("\\rightarrow", "→").replace("\\degree", "°").replace("^\\circ", "°")
    # Üslü ifadeleri (^2, ^3, ^{...}) Unicode üst simgeye çevir
    sup_map = str.maketrans("0123456789+-=nxy", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼ⁿˣʸ")
    text = re.sub(r"\^\{([0-9+\-=nxy]+)\}", lambda m: m.group(1).translate(sup_map), text)
    text = re.sub(r"\^([0-9+\-=nxy]+)", lambda m: m.group(1).translate(sup_map), text)
    return text

def generate_twin_question(question_text, image=None):
    prompt = (
        "Yüklenen LGS sorusunu incele. Önce öğrencinin yüklediği bu soruyu adım adım anlaşılır şekilde çöz, MEB alt kazanımını ve altın çözüm taktiğini yaz. "
        "Ardından aynı mantık ve kazanımda ancak farklı ve eğlenceli bir hikayede MEB tarzı yeni nesil bir 'İkiz Soru', 4 şıkkı ve adım adım çözümünü üret. "
        "ÖNEMLİ: Kesinlikle $m^2$ gibi dolar ($) veya LaTeX kodu kullanma; birimleri doğrudan m², cm², cm³, 2³, √5 gibi düz okunaklı karakterlerle yaz. "
        "Yanıtı SADECE geçerli bir JSON objesi olarak ver, başka hiçbir metin yazma. Format:\n"
        '{\n'
        '  "kazanim": "8.1.1.1. Kısa ve net MEB Alt Kazanımı",\n'
        '  "altin_taktik": "Bu tarz soruları 10 saniyede çözdüren süper püf noktası!",\n'
        '  "orijinal_adimlar": ["1. Adım: ...", "2. Adım: ...", "3. Adım: ..."],\n'
        '  "orijinal_cevap": "Sorunun Doğru Cevabı / Şıkkı",\n'
        '  "ikiz_soru": "Yeni nesil ikiz sorunun hikayesi ve soru kökü...",\n'
        '  "secenekler": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
        '  "dogru_index": 1,\n'
        '  "ikiz_ipucu": "İkiz soruyu çözerken dikkat edilecek ipucu",\n'
        '  "ikiz_adimlar": ["1. Adım: ...", "2. Adım: ...", "3. Adım: ..."]\n'
        '}\n\n'
        f"Ek Açıklama / Soru Metni: {question_text}"
    )
    raw = ask_gemini(prompt, image=image)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return clean_math_text({
        "kazanim": "LGS Soru & İkiz Soru Analizi",
        "altin_taktik": "Sorudaki anahtar kelimelere ve birimlere dikkat et!",
        "orijinal_adimlar": [raw],
        "orijinal_cevap": "✅ Çözüm tamamlandı",
        "ikiz_soru": "Yukarıdaki çözüm adımlarını inceleyerek benzer soruyu kendin de çözmeyi dene!",
        "secenekler": ["A) Seçenek A", "B) Seçenek B", "C) Seçenek C", "D) Seçenek D"],
        "dogru_index": 0,
        "ikiz_ipucu": "Adımları takip et!",
        "ikiz_adimlar": [raw]
    })

def solve_page_questions_structured(image):
    prompt = (
        "Bu kitap/test sayfasındaki soruları incele ve her bir soruyu 8. sınıf LGS öğrencisi için eğlenceli, adım adım anlaşılır şekilde çöz. "
        "ÖNEMLİ: Kesinlikle $ işareti veya LaTeX kodu ($m^2$, \\frac vb.) KULLANMA! Birimleri ve üslü sayıları doğrudan m², cm², 10³, √2 gibi düz Unicode karakterlerle yaz. "
        "Yanıtı SADECE geçerli bir JSON dizisi olarak ver, başka hiçbir açıklama yazma. Format:\n"
        '[\n'
        '  {\n'
        '    "soru_no": "Soru 1",\n'
        '    "kazanim": "Kısa Konu / MEB Kazanımı",\n'
        '    "ipucu": "Soruyu çözdüren anahtar ipucu",\n'
        '    "adimlar": ["1. Adım: ...", "2. Adım: ..."],\n'
        '    "dogru_sik": "C"\n'
        '  }\n'
        ']'
    )
    raw = ask_gemini(prompt, image=image)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return clean_math_text([{"soru_no": "Sayfa Çözümü", "kazanim": "Genel Çözüm", "ipucu": "Adımları takip et!", "adimlar": [raw], "dogru_sik": "✅"}])

def generate_hap_ozet_structured(content_text="", image=None):
    prompt = (
        "Bu ders/konu içeriğini 8. sınıf LGS öğrencisi için çok eğlenceli, akılda kalıcı bir 'Hap Özet' yap. "
        "ÖNEMLİ: Kesinlikle $ işareti veya LaTeX kodu KULLANMA; m², cm², 10³ gibi doğrudan Unicode semboller kullan. "
        "Yanıtı SADECE geçerli bir JSON objesi olarak ver, başka hiçbir açıklama yazma. Format:\n"
        '{\n'
        '  "baslik": "Konunun Havalı Başlığı",\n'
        '  "maddeler": [\n'
        '    {"emoji": "⚡", "baslik": "1. Anahtar Nokta", "detay": "Kısa, vurucu ve net açıklama."},\n'
        '    {"emoji": "🧠", "baslik": "2. Anahtar Nokta", "detay": "Kısa, vurucu ve net açıklama."},\n'
        '    {"emoji": "🔥", "baslik": "3. Anahtar Nokta", "detay": "Kısa, vurucu ve net açıklama."}\n'
        '  ],\n'
        '  "altin_taktik": "LGS sınavında bu konudan soru çözerken hayat kurtaran 1 cümlelik altın taktik!",\n'
        '  "ses_metni": "Podcast gibi samimi okunacak 3-4 cümlelik akıcı özet metni."\n'
        '}\n\n'
        f"İçerik:\n{content_text[:4000]}"
    )
    raw = ask_gemini(prompt, image=image)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return clean_math_text({
        "baslik": "Konu Hap Özeti",
        "maddeler": [{"emoji": "📌", "baslik": "Özet", "detay": raw}],
        "altin_taktik": "Sorularda anahtar kelimelerin altını çizmeyi unutma!",
        "ses_metni": raw[:500]
    })

def generate_lgs_quiz_list(content_text="", image=None):
    prompt = (
        "Bu içerikten veya sayfadaki sorulardan ilham alarak aynı kazanımda MEB LGS tarzı 2 adet çoktan seçmeli yeni nesil 'İkiz Soru' hazırla. "
        "ÖNEMLİ: Kesinlikle $m^2$ gibi $ işareti veya LaTeX kodu KULLANMA! Birimleri ve üslü/köklü sayıları m², cm², cm³, 2⁵, √3 gibi doğrudan okunaklı Unicode karakterlerle yaz. "
        "Yanıtı SADECE geçerli bir JSON dizisi olarak ver, başka hiçbir açıklama yazma. Format:\n"
        '[\n'
        '  {\n'
        '    "soru": "Soru metni...",\n'
        '    "secenekler": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
        '    "dogru_index": 0,\n'
        '    "ipucu": "Kısa ipucu...",\n'
        '    "cozum": "Adım adım net çözüm açıklaması..."\n'
        '  }\n'
        ']\n'
        "Not: dogru_index 0 (A), 1 (B), 2 (C) veya 3 (D) olmalıdır.\n\n"
        f"İçerik:\n{content_text[:4000]}"
    )
    raw = ask_gemini(prompt, image=image)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return []

def generate_flashcards_list(content_text):
    prompt = (
        "Aşağıdaki içerikten LGS sınavına yönelik 4 adet arkalı önlü Flashcard hazırla. "
        "ÖNEMLİ: Kesinlikle $ işareti veya LaTeX kodu KULLANMA; m², cm², 10³ gibi doğrudan Unicode semboller kullan. "
        "Yanıtı SADECE geçerli bir JSON dizisi olarak ver, başka hiçbir açıklama yazma. Format:\n"
        '[{"soru": "Kartın ön yüzündeki soru veya kavram?", "cevap": "Kartın arka yüzündeki net ve akılda kalıcı cevap."}]\n\n'
        f"İçerik:\n{content_text[:4000]}"
    )
    raw = ask_gemini(prompt)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return clean_math_text([{"soru": "Flashcard Özeti", "cevap": raw}])

def analyze_exam_sheet(image=None, netler_ozeti=""):
    prompt = (
        "Sen 8. sınıf LGS öğrencisine koçluk yapan enerjik, samimi ve motive edici bir eğitim koçusun. "
        f"Öğrencinin bu denemedeki 6 derslik Doğru/Yanlış/Boş/Net tablosu ve puanı şöyledir:\n{netler_ozeti}\n\n"
        "Yüklenen deneme fotoğraflarını (varsa) ve bu net tablosunu inceleyerek SADECE geçerli bir JSON objesi döndür, başka hiçbir açıklama yazma. "
        "Kesinlikle $ işareti veya LaTeX kodu kullanma (m², cm² gibi düz semboller kullan). JSON formatı:\n"
        '{\n'
        '  "genel_performans": "Öğrencinin deneme sonucunu değerlendiren, motive edici, samimi 2-3 cümlelik Genel Performans yorumu.",\n'
        '  "ders_analizleri": [\n'
        '    {"emoji": "📘", "ders": "Türkçe", "durum": "Harika / Geliştirilmeli vb.", "kazanim_ve_taktik": "Eksik görülen MEB alt kazanımı ve net artıracak kısa taktik"},\n'
        '    {"emoji": "📐", "ders": "Matematik", "durum": "...", "kazanim_ve_taktik": "..."},\n'
        '    {"emoji": "🧬", "ders": "Fen Bilimleri", "durum": "...", "kazanim_ve_taktik": "..."},\n'
        '    {"emoji": "🏛️", "ders": "T.C. İnkılap Tarihi", "durum": "...", "kazanim_ve_taktik": "..."},\n'
        '    {"emoji": "🕌", "ders": "Din Kültürü", "durum": "...", "kazanim_ve_taktik": "..."},\n'
        '    {"emoji": "🇬🇧", "ders": "İngilizce", "durum": "...", "kazanim_ve_taktik": "..."}\n'
        '  ],\n'
        '  "haftanin_hedefi": "Bir sonraki denemede puanı +15-20 artırmak için en kritik 1 cümlelik aksiyon hedefi!"\n'
        '}'
    )
    raw = ask_gemini(prompt, image=image)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return clean_math_text(json.loads(match.group(0)))
    except Exception:
        pass
    return clean_math_text({
        "genel_performans": raw[:400],
        "ders_analizleri": [],
        "haftanin_hedefi": "Yanlış yapılan soruların konularını Hızlı Öğren istasyonundan tekrar et!"
    })


def extract_exam_scores(image):
    """Deneme sonuç/optik görsellerinden 6 dersin Doğru/Yanlış/Boş sayılarını okur.
    Dönüş: {"turkce": {"D":..,"Y":..,"B":..}, "mat":..., "fen":..., "ink":..., "din":..., "ing":...} veya {}"""
    max_map = {"turkce": 20, "mat": 20, "fen": 20, "ink": 10, "din": 10, "ing": 10}
    prompt = (
        "Bu görseller bir 8. sınıf LGS deneme sınavına ait (sonuç belgesi, karne, optik form veya cevap anahtarı olabilir). "
        "Görsellerden 6 dersin Doğru, Yanlış ve Boş sayılarını oku. Soru sayıları: Türkçe 20, Matematik 20, Fen Bilimleri 20, "
        "T.C. İnkılap Tarihi 10, Din Kültürü 10, İngilizce 10. Bir dersin bilgisi görselde yoksa o dersi null yaz. "
        "Doğru+Yanlış+Boş toplamı o dersin soru sayısını geçmemeli. "
        "Yanıtı SADECE geçerli bir JSON objesi olarak ver, başka hiçbir metin yazma. Format:\n"
        '{"turkce": {"D": 15, "Y": 3, "B": 2}, "mat": {"D": 12, "Y": 4, "B": 4}, "fen": {"D": 0, "Y": 0, "B": 0}, '
        '"ink": {"D": 0, "Y": 0, "B": 0}, "din": {"D": 0, "Y": 0, "B": 0}, "ing": {"D": 0, "Y": 0, "B": 0}}'
    )
    raw = ask_gemini(prompt, image=image)
    sonuc = {}
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        veri = json.loads(match.group(0))
        for anahtar, maks in max_map.items():
            d_obj = veri.get(anahtar)
            if not isinstance(d_obj, dict):
                continue
            d = max(0, min(maks, int(d_obj.get("D", 0) or 0)))
            y = max(0, min(maks - d, int(d_obj.get("Y", 0) or 0)))
            sonuc[anahtar] = {"D": d, "Y": y, "B": maks - d - y}
    except Exception:
        return {}
    return sonuc


@st.cache_data
def mufredat_yukle():
    """MEB 8. Sınıf LGS müfredat sınırlarını ve kapsam dışı yasaklı alanları diskten tek seferlik okur ve önbelleğe alır."""
    dosya_yolu = Path(__file__).parent / "lgs_mufredat_sinirlar.json"
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return json.load(f)


DERS_KODU_HARITASI = {
    "MAT_8": "MAT_8",
    "Matematik": "MAT_8",
    "FEN_8": "FEN_8",
    "Fen Bilimleri": "FEN_8",
    "TUR_8": "TUR_8",
    "Türkçe": "TUR_8",
    "INK_8": "INK_8",
    "İnkılap Tarihi": "INK_8",
    "T.C. İnkılap Tarihi": "INK_8",
    "T.C. İnkılap Tarihi ve Atatürkçülük": "INK_8",
    "DIN_8": "DIN_8",
    "Din Kültürü": "DIN_8",
    "Din Kültürü ve Ahlak Bilgisi": "DIN_8",
    "ING_8": "ING_8",
    "İngilizce": "ING_8",
}

UI_DERS_ADI_HARITASI = {
    "MAT_8": "Matematik",
    "FEN_8": "Fen Bilimleri",
    "TUR_8": "Türkçe",
    "INK_8": "İnkılap Tarihi",
    "DIN_8": "Din Kültürü",
    "ING_8": "İngilizce",
}


def _build_meb_konulari_dict():
    try:
        muf = mufredat_yukle()
        sonuc = {}
        for d_kod, d_bilgi in muf.get("dersler", {}).items():
            ui_ad = UI_DERS_ADI_HARITASI.get(d_kod, d_bilgi.get("ders_adi", d_kod))
            uniteler = [u["unite_adi"] for u in d_bilgi.get("uniteler", [])]
            sonuc[ui_ad] = uniteler
            sonuc[d_bilgi.get("ders_adi", ui_ad)] = uniteler
        return sonuc
    except Exception:
        return {
            "Türkçe": ["Sözcükte, Cümlede ve Parçada Anlam / Sözel Mantık", "Fiilimsiler (Eylemsiler)", "Cümlenin Ögeleri", "Fiilde Çatı", "Cümle Türleri / Metin Türleri / Anlatım Bozuklukları / Yazım ve Noktalama"],
            "Matematik": ["Çarpanlar ve Katlar / Üslü İfadeler", "Kareköklü İfadeler / Veri Analizi", "Basit Olayların Olma Olasılığı / Cebirsel İfadeler ve Özdeşlikler", "Doğrusal Denklemler / Eşitsizlikler", "Üçgenler / Eşlik ve Benzerlik", "Dönüşüm Geometrisi / Geometrik Cisimler"],
            "Fen Bilimleri": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri", "Basit Makineler", "Enerji Dönüşümleri ve Çevre Bilimi", "Elektrik Yükleri ve Elektrik Enerjisi"],
            "İnkılap Tarihi": ["Bir Kahraman Doğuyor", "Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar", "Millî Bir Destan: Ya İstiklal Ya Ölüm!", "Atatürkçülük ve Çağdaşlaşan Türkiye", "Demokratikleşme Çabaları", "Atatürk Dönemi Türk Dış Politikası", "Atatürk'ün Ölümü ve Sonrası"],
            "İngilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone", "The Internet", "Adventures", "Tourism", "Chores", "Science", "Natural Forces"],
            "Din Kültürü": ["Kader İnancı", "Zekât ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Örnekliği", "Kur'an-ı Kerim ve Özellikleri"],
        }


MEB_8_SINIF_KONULARI = _build_meb_konulari_dict()


def _coz_ders_ve_unite(ders_kodu_veya_adi, unite_no_veya_konu=None):
    """Seçilen ders ve ünite/konudan (ders_kodu, unite_no, ders_obj, unite_obj) döndürür."""
    mufredat = mufredat_yukle()
    dersler = mufredat["dersler"]
    ders_kodu = DERS_KODU_HARITASI.get(str(ders_kodu_veya_adi).strip(), "MAT_8")
    if ders_kodu not in dersler:
        ders_kodu = "MAT_8"
    ders_obj = dersler[ders_kodu]
    uniteler = ders_obj["uniteler"]

    secili_unite = None
    if isinstance(unite_no_veya_konu, int):
        secili_unite = next((u for u in uniteler if int(u["unite_no"]) == unite_no_veya_konu), None)
    elif unite_no_veya_konu is not None:
        konu_str = str(unite_no_veya_konu).strip()
        if konu_str.isdigit():
            secili_unite = next((u for u in uniteler if int(u["unite_no"]) == int(konu_str)), None)
        else:
            # Tam veya kısmi ünite adı eşleşmesi
            for u in uniteler:
                if u["unite_adi"].lower() == konu_str.lower() or u["unite_adi"].lower() in konu_str.lower() or konu_str.lower() in u["unite_adi"].lower():
                    secili_unite = u
                    break
            if not secili_unite:
                m_no = re.search(r"(\d+)", konu_str)
                if m_no:
                    u_no = int(m_no.group(1))
                    secili_unite = next((u for u in uniteler if int(u["unite_no"]) == u_no), None)

    if not secili_unite:
        secili_unite = uniteler[0]

    return ders_kodu, int(secili_unite["unite_no"]), ders_obj, secili_unite


def _olustur_mufredat_system_prompt(ders_kodu: str, unite_no: int) -> str:
    """Token tasarrufu için JSON içinden SADECE seçilen dersin genel_kisitlamalar listesini
    ve seçilen ünitenin aktif_kazanimlar ile kapsam_disi_yasakli_alanlar listelerini çeker."""
    mufredat = mufredat_yukle()
    ders_kodu, unite_no, ders, unite = _coz_ders_ve_unite(ders_kodu, unite_no)

    system_prompt = f"""Sen uzman bir MEB 8. Sınıf LGS soru yazarısın.
DERS: {ders['ders_adi']} ({ders_kodu}) | ÜNİTE {unite['unite_no']}: {unite['unite_adi']}

ÜRETİM ÖNCESİ KONTROL: {mufredat['validasyon_kurallari']['uretim_oncesi_kontrol']}

AKTİF KAZANIMLAR (Yalnızca bu kapsamda kal):
{chr(10).join(['- ' + k for k in unite['aktif_kazanimlar']])}

KESİN YASAKLI ALANLAR (Bu kavramlara/işlemlere girersen çıktı geçersiz sayılır):
{chr(10).join(['- ' + g for g in ders['genel_kisitlamalar']])}
{chr(10).join(['- ' + y for y in unite['kapsam_disi_yasakli_alanlar']])}

DENETİM: {mufredat['validasyon_kurallari']['uretim_sonrasi_filtre']}
Kesinlikle $ işareti veya LaTeX kodu ($m^2$, \\frac vb.) kullanma; m², cm², cm³, 2⁵, √3 gibi doğrudan okunaklı Unicode karakterler kullan."""
    return system_prompt


def _mufredat_destekli_gemini_json(prompt: str, ders_kodu: str, unite_no: int):
    """Seçilen ders ve ünitenin system_instruction sınırlarıyla (temperature=0.4, application/json) Gemini çağrısı yapar."""
    current_key = _get_gemini_key()
    genai.configure(api_key=current_key, transport="rest")
    system_prompt = _olustur_mufredat_system_prompt(ders_kodu, unite_no)

    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash-lite",
        system_instruction=system_prompt,
        generation_config={
            "temperature": 0.4,
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
        },
    )
    response = model.generate_content(prompt)
    return response.text


def _normalize_lgs_soru_dict(ham: dict, sira_no: int = 1, varsayilan_kazanim: str = "") -> dict:
    """Standart JSON anahtarlarını (soru_koku, hikaye_veya_oncul, siklar, dogru_cevap, cozum_aciklamasi, ilgili_kazanim)
    ve arayüz uyumluluk anahtarlarını (soru, secenekler, dogru_index, cozum, kazanim, ipucu) garanti altına alır."""
    temiz = clean_math_text(ham if isinstance(ham, dict) else {})

    hikaye = str(temiz.get("hikaye_veya_oncul") or "").strip()
    soru_koku = str(temiz.get("soru_koku") or "").strip()
    eski_soru = str(temiz.get("soru") or "").strip()

    if not soru_koku and eski_soru:
        soru_koku = eski_soru

    if hikaye and soru_koku and hikaye not in soru_koku:
        birlesik_soru = f"{hikaye}\n\n{soru_koku}"
    else:
        birlesik_soru = soru_koku or hikaye or eski_soru

    siklar_ham = temiz.get("siklar")
    siklar_obj = {"A": "", "B": "", "C": "", "D": ""}
    harfler = ["A", "B", "C", "D"]

    if isinstance(siklar_ham, dict):
        for h in harfler:
            val = str(siklar_ham.get(h) or siklar_ham.get(h.lower()) or "").strip()
            val = re.sub(r"^[A-Da-d][\)\.\-\:\s]+", "", val).strip()
            siklar_obj[h] = val
    elif isinstance(temiz.get("secenekler"), list):
        for idx, h in enumerate(harfler):
            if idx < len(temiz["secenekler"]):
                val = str(temiz["secenekler"][idx]).strip()
                val = re.sub(r"^[A-Da-d][\)\.\-\:\s]+", "", val).strip()
                siklar_obj[h] = val

    secenekler_list = [f"{h}) {siklar_obj[h]}" for h in harfler]

    dogru_cevap_raw = str(temiz.get("dogru_cevap") or "").strip().upper()
    if dogru_cevap_raw and dogru_cevap_raw[0] in harfler:
        dogru_harf = dogru_cevap_raw[0]
        dogru_idx = harfler.index(dogru_harf)
    else:
        dogru_idx = int(temiz.get("dogru_index", 0) or 0)
        dogru_idx = max(0, min(3, dogru_idx))
        dogru_harf = harfler[dogru_idx]

    cozum_aciklamasi = str(temiz.get("cozum_aciklamasi") or temiz.get("cozum") or "").strip()
    ilgili_kazanim = str(temiz.get("ilgili_kazanim") or temiz.get("kazanim") or varsayilan_kazanim).strip()
    ipucu = str(temiz.get("ipucu") or f"Bu soruda '{ilgili_kazanim}' kazanımındaki temel kurala dikkat et.").strip()

    return {
        "soru_no": f"Soru {sira_no}",
        "soru_koku": soru_koku,
        "hikaye_veya_oncul": hikaye,
        "siklar": siklar_obj,
        "dogru_cevap": dogru_harf,
        "cozum_aciklamasi": cozum_aciklamasi,
        "ilgili_kazanim": ilgili_kazanim,
        # Mevcut optik test ekranı ile %100 uyumluluk alanları:
        "soru": birlesik_soru,
        "secenekler": secenekler_list,
        "dogru_index": dogru_idx,
        "cozum": cozum_aciklamasi,
        "kazanim": ilgili_kazanim,
        "ipucu": ipucu,
    }


def lgs_soru_uret(ders_kodu: str, unite_no: int, zorluk: str) -> dict:
    """Seçilen ders_kodu (MAT_8, FEN_8 vb.) ve unite_no için MEB müfredat sınırlarına %100 uygun
    1 adet yeni nesil LGS sorusu üretir ve standart JSON objesi olarak döndürür."""
    ders_kodu, unite_no, ders, unite = _coz_ders_ve_unite(ders_kodu, unite_no)
    prompt = (
        f"{zorluk} seviyesinde 1 adet yeni nesil LGS sorusu üret. "
        "Yanıtı SADECE aşağıdaki anahtarları eksiksiz içeren geçerli bir JSON objesi olarak döndür:\n"
        "{\n"
        '  "hikaye_veya_oncul": "Yeni nesil sorunun günlük hayat kurgusu, tablosu, metni veya öncülleri",\n'
        '  "soru_koku": "Buna göre ... aşağıdakilerden hangisidir? şeklindeki net soru kökü",\n'
        '  "siklar": {\n'
        '    "A": "A şıkkı içeriği",\n'
        '    "B": "B şıkkı içeriği",\n'
        '    "C": "C şıkkı içeriği",\n'
        '    "D": "D şıkkı içeriği"\n'
        "  },\n"
        '  "dogru_cevap": "A",\n'
        '  "cozum_aciklamasi": "Adım adım kazanım odaklı net çözüm açıklaması",\n'
        '  "ilgili_kazanim": "Sorunun ölçtüğü spesifik MEB aktif kazanımı"\n'
        "}"
    )
    try:
        raw_text = _mufredat_destekli_gemini_json(prompt, ders_kodu, unite_no)
        veri = json.loads(raw_text)
        if isinstance(veri, list) and veri:
            veri = veri[0]
        return _normalize_lgs_soru_dict(veri, sira_no=1, varsayilan_kazanim=f"{unite['unite_adi']} ({zorluk})")
    except Exception as e:
        return _normalize_lgs_soru_dict({
            "hikaye_veya_oncul": f"{ders['ders_adi']} - {unite['unite_adi']} ünitesi kapsamında soru üretilirken bağlantı hatası oluştu: {e}",
            "soru_koku": "Lütfen tekrar deneyiniz.",
            "siklar": {"A": "Seçenek A", "B": "Seçenek B", "C": "Seçenek C", "D": "Seçenek D"},
            "dogru_cevap": "A",
            "cozum_aciklamasi": "Tekrar denediğinizde yeni soru üretilecektir.",
            "ilgili_kazanim": unite["unite_adi"],
        })


def get_ai_lgs_topics(ders, force_ai=False):
    """Seçilen 8. sınıf LGS dersi için lgs_mufredat_sinirlar.json içindeki ünite listesini döndürür."""
    ders_kodu, _, ders_obj, _ = _coz_ders_ve_unite(ders, 1)
    mufredat_uniteleri = [u["unite_adi"] for u in ders_obj.get("uniteler", [])]
    if not force_ai:
        return mufredat_uniteleri
    # force_ai=True ise ünitelerin aktif kazanımlarını da alt başlık olarak ekle
    detayli = []
    for u in ders_obj.get("uniteler", []):
        detayli.append(u["unite_adi"])
        for kaz in u.get("aktif_kazanimlar", []):
            detayli.append(f"{u['unite_adi']} — {kaz}")
    return detayli if detayli else mufredat_uniteleri


def _fetch_test_batch(ders, konu, zorluk, adet, baslangic_no=1, ders_kodu=None, unite_no=None):
    cozulen_kod, cozulen_unite_no, ders_obj, unite_obj = _coz_ders_ve_unite(
        ders_kodu or ders,
        unite_no if unite_no is not None else konu,
    )
    prompt = (
        f"'{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ({konu}) ve '{zorluk}' zorluk seviyesinde "
        f"TAM {adet} ADET çoktan seçmeli yeni nesil LGS sorusu hazırla (Soru {baslangic_no}'den Soru {baslangic_no + adet - 1}'e kadar).\n"
        "Her bir soru objesi ZORUNLU olarak şu JSON anahtarlarına sahip olmalıdır:\n"
        "- hikaye_veya_oncul\n"
        "- soru_koku\n"
        "- siklar (A, B, C, D anahtarlarına sahip JSON objesi olarak)\n"
        "- dogru_cevap ('A', 'B', 'C' veya 'D')\n"
        "- cozum_aciklamasi\n"
        "- ilgili_kazanim\n\n"
        "Yanıtı SADECE aşağıdaki şemaya uygun geçerli bir JSON dizisi (array) olarak döndür:\n"
        "[\n"
        "  {\n"
        '    "hikaye_veya_oncul": "Yeni nesil sorunun hikayesi, tablosu, metni veya öncülleri...",\n'
        '    "soru_koku": "Buna göre ... aşağıdakilerden hangisidir?",\n'
        '    "siklar": {"A": "...", "B": "...", "C": "...", "D": "..."},\n'
        '    "dogru_cevap": "A",\n'
        '    "cozum_aciklamasi": "1. Adım: ... 2. Adım: ...",\n'
        '    "ilgili_kazanim": "İlgili MEB aktif kazanımı"\n'
        "  }\n"
        "]"
    )
    try:
        raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            for k in ("sorular", "questions", "items", "data"):
                if isinstance(parsed.get(k), list):
                    parsed = parsed[k]
                    break
            else:
                parsed = [parsed]
        if isinstance(parsed, list):
            return [
                _normalize_lgs_soru_dict(item, sira_no=baslangic_no + i, varsayilan_kazanim=f"{unite_obj['unite_adi']} ({zorluk})")
                for i, item in enumerate(parsed)
                if isinstance(item, dict)
            ]
    except Exception:
        pass
    return []


def generate_custom_lgs_test(ders, konu, zorluk, soru_sayisi=5, ders_kodu=None, unite_no=None):
    """Seçilen ders, ünite/konu, zorluk ve soru sayısına (5, 10, 20) göre MEB müfredat denetimli interaktif LGS testi üretir."""
    soru_sayisi = int(soru_sayisi)
    if soru_sayisi <= 10:
        sonuc = _fetch_test_batch(ders, konu, zorluk, soru_sayisi, baslangic_no=1, ders_kodu=ders_kodu, unite_no=unite_no)
    else:
        ilk_yari = _fetch_test_batch(ders, konu, zorluk, 10, baslangic_no=1, ders_kodu=ders_kodu, unite_no=unite_no)
        ikinci_yari = _fetch_test_batch(ders, konu, zorluk, soru_sayisi - 10, baslangic_no=11, ders_kodu=ders_kodu, unite_no=unite_no)
        sonuc = ilk_yari + ikinci_yari

    temiz_liste = []
    for idx, item in enumerate(sonuc, 1):
        if isinstance(item, dict):
            norm_item = _normalize_lgs_soru_dict(item, sira_no=idx, varsayilan_kazanim=f"{konu} • {zorluk}")
            temiz_liste.append(norm_item)
    return temiz_liste


def generate_sinotest_activity(ders, konu, zorluk, adet, calisma_turu, ders_kodu=None, unite_no=None):
    """6 farklı çalışma türü (Test Oluştur, Flash Kart, Boşluk Doldur, Doğru/Yanlış, Eşleştir, Karıştırma) için
    MEB müfredat sınırlarına (%100 aktif kazanım + yasaklı alan filtresi) uygun içerik üretir."""
    adet = int(adet)
    cozulen_kod, cozulen_unite_no, ders_obj, unite_obj = _coz_ders_ve_unite(
        ders_kodu or ders,
        unite_no if unite_no is not None else konu,
    )
    if calisma_turu == "Test Oluştur":
        return generate_custom_lgs_test(ders, konu, zorluk, adet, ders_kodu=cozulen_kod, unite_no=cozulen_unite_no)

    elif calisma_turu == "Flash Kart":
        prompt = (
            f"8. Sınıf MEB LGS '{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ve '{zorluk}' zorluk seviyesinde TAM {min(adet, 15)} ADET arkalı-önlü bilgi kartı (Flash Kart) hazırla. "
            "Kesinlikle $ işareti veya LaTeX kodu kullanma (m², cm², 2⁵, √3 gibi düz Unicode kullan). "
            "SADECE geçerli bir JSON dizisi döndür:\n"
            '[\n'
            '  {\n'
            '    "kazanim": "Alt kazanım / kavram adı",\n'
            '    "on_yuz": "Kartın ön yüzündeki net kavram veya kritik LGS sorusu",\n'
            '    "arka_yuz": "Kartın arka yüzündeki net, akılda kalıcı cevap ve konu özeti",\n'
            '    "ipucu": "LGS sınavında dikkat edilmesi gereken püf noktası"\n'
            '  }\n'
            ']'
        )
        try:
            raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        except Exception:
            raw = ask_gemini(prompt)
        veriler = []
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                veriler = clean_math_text(json.loads(m.group(0)))
        except Exception:
            veriler = []
        norm = []
        for idx, item in enumerate(veriler if isinstance(veriler, list) else [], 1):
            if not isinstance(item, dict):
                continue
            on_yuz = item.get("on_yuz") or item.get("soru") or item.get("kavram") or item.get("front") or ""
            arka_yuz = item.get("arka_yuz") or item.get("cevap") or item.get("aciklama") or item.get("back") or ""
            if on_yuz and arka_yuz:
                norm.append({
                    "kazanim": item.get("kazanim") or f"{konu} • Kart {idx}",
                    "on_yuz": str(on_yuz).strip(),
                    "arka_yuz": str(arka_yuz).strip(),
                    "ipucu": str(item.get("ipucu") or "Bu kavram LGS'de öncüllü sorularda sıkça karşımıza çıkar.").strip()
                })
        return norm

    elif calisma_turu == "Boşluk Doldur":
        prompt = (
            f"8. Sınıf MEB LGS '{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ve '{zorluk}' zorluk seviyesinde TAM {min(adet, 15)} ADET boşluk doldurma sorusu hazırla. "
            "Şık (A, B, C, D) KULLANMA! Her cümlede tek bir kritik kavramın yerine '_______' koy ve doğru kelimeyi 'cevap' alanına yaz. "
            "Kesinlikle $ işareti veya LaTeX kodu kullanma. SADECE geçerli bir JSON dizisi döndür:\n"
            '[\n'
            '  {\n'
            '    "kazanim": "İlgili alt konu",\n'
            '    "cumle": "Cümlenin başı _______ cümlenin devamı.",\n'
            '    "cevap": "Boşluğa gelecek doğru kavram",\n'
            '    "ipucu": "Kavramı hatırlatacak kısa ipucu",\n'
            '    "cozum": "Neden bu kavramın geldiğinin kısa açıklaması"\n'
            '  }\n'
            ']'
        )
        try:
            raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        except Exception:
            raw = ask_gemini(prompt)
        veriler = []
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                veriler = clean_math_text(json.loads(m.group(0)))
        except Exception:
            veriler = []
        norm = []
        for idx, item in enumerate(veriler if isinstance(veriler, list) else [], 1):
            if not isinstance(item, dict):
                continue
            cumle = item.get("cumle") or item.get("soru") or item.get("ifade") or ""
            cevap = item.get("cevap") or item.get("dogru_cevap") or ""
            if not cevap and isinstance(item.get("secenekler"), list):
                d_i = int(item.get("dogru_index", 0))
                if 0 <= d_i < len(item["secenekler"]):
                    cevap = re.sub(r"^[A-Da-d][\)\.\-\s]+", "", str(item["secenekler"][d_i])).strip()
            if "___" not in str(cumle) and cevap and str(cevap) in str(cumle):
                cumle = str(cumle).replace(str(cevap), "_______", 1)
            elif "___" not in str(cumle):
                cumle = str(cumle).strip() + " (_______)"
            if cumle and cevap:
                norm.append({
                    "kazanim": item.get("kazanim") or f"{konu} • Soru {idx}",
                    "cumle": str(cumle).strip(),
                    "cevap": str(cevap).strip(),
                    "ipucu": str(item.get("ipucu") or "Cümledeki anahtar kelimelere dikkat et.").strip(),
                    "cozum": str(item.get("cozum") or f"Boşluğa '{cevap}' gelmelidir.").strip()
                })
        return norm

    elif calisma_turu == "Doğru/Yanlış":
        prompt = (
            f"8. Sınıf MEB LGS '{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ve '{zorluk}' zorluk seviyesinde TAM {min(adet, 15)} ADET Doğru/Yanlış etkinliği ifadesi hazırla. "
            "İfadelerin yaklaşık yarısı Doğru (true), yarısı Yanlış (false) olsun. "
            "Kesinlikle $ işareti veya LaTeX kodu kullanma. SADECE geçerli bir JSON dizisi döndür:\n"
            '[\n'
            '  {\n'
            '    "kazanim": "İlgili alt konu",\n'
            '    "ifade": "Net ve anlaşılır bilgi cümlesi.",\n'
            '    "dogru_mu": true,\n'
            '    "ipucu": "Kısa ipucu",\n'
            '    "cozum": "Neden Doğru veya Yanlış olduğunun net açıklaması"\n'
            '  }\n'
            ']'
        )
        try:
            raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        except Exception:
            raw = ask_gemini(prompt)
        veriler = []
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                veriler = clean_math_text(json.loads(m.group(0)))
        except Exception:
            veriler = []
        norm = []
        for idx, item in enumerate(veriler if isinstance(veriler, list) else [], 1):
            if not isinstance(item, dict):
                continue
            ifade = item.get("ifade") or item.get("soru") or item.get("cumle") or ""
            dogru_mu_raw = item.get("dogru_mu")
            if isinstance(dogru_mu_raw, bool):
                dogru_mu = dogru_mu_raw
            elif isinstance(dogru_mu_raw, str):
                dogru_mu = dogru_mu_raw.strip().lower() in ("true", "doğru", "dogru", "d", "1", "evet")
            else:
                dogru_mu = (int(item.get("dogru_index", 0)) == 0)
            if ifade:
                norm.append({
                    "kazanim": item.get("kazanim") or f"{konu} • Madde {idx}",
                    "ifade": str(ifade).strip(),
                    "dogru_mu": bool(dogru_mu),
                    "ipucu": str(item.get("ipucu") or "Kavramın tanımını ve istisnalarını düşün.").strip(),
                    "cozum": str(item.get("cozum") or "").strip()
                })
        return norm

    elif calisma_turu == "Eşleştir":
        cift_sayisi = min(adet, 10)
        prompt = (
            f"8. Sınıf MEB LGS '{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ve '{zorluk}' zorluk seviyesinde TAM {cift_sayisi} ADET kavram-açıklama eşleştirme çifti hazırla. "
            "Kesinlikle $ işareti veya LaTeX kodu kullanma. SADECE geçerli bir JSON dizisi döndür:\n"
            '[\n'
            '  {\n'
            '    "sol": "Kavram / Terim / Örnek Cümle",\n'
            '    "sag": "Tam Karşılığı / Tanımı / Anlam Özelliği",\n'
            '    "aciklama": "Neden eşleştiğinin kısa açıklaması"\n'
            '  }\n'
            ']'
        )
        try:
            raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        except Exception:
            raw = ask_gemini(prompt)
        veriler = []
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                veriler = clean_math_text(json.loads(m.group(0)))
        except Exception:
            veriler = []
        norm = []
        for idx, item in enumerate(veriler if isinstance(veriler, list) else [], 1):
            if not isinstance(item, dict):
                continue
            sol = item.get("sol") or item.get("kavram") or item.get("terim") or item.get("soru") or ""
            sag = item.get("sag") or item.get("karsilik") or item.get("tanim") or item.get("cevap") or ""
            if sol and sag:
                norm.append({
                    "sol": str(sol).strip(),
                    "sag": str(sag).strip(),
                    "aciklama": str(item.get("aciklama") or f"{sol} -> {sag}").strip()
                })
        return norm

    elif calisma_turu == "Karıştırma":
        prompt = (
            f"8. Sınıf MEB LGS '{ders_obj['ders_adi']}' dersi, '{unite_obj['unite_adi']}' ünitesi ve '{zorluk}' zorluk seviyesinde TAM {min(adet, 10)} ADET interaktif 'Kelime / Adım Karıştırma (Sıraya Dizme)' etkinliği hazırla. "
            "Kesinlikle A/B/C/D şıkkı KULLANMA! Her soruda öğrenciye bir yönerge/ipucu ('yonerge') ver ve doğru cümleyi, kuralı veya işlem sırasını oluşturan 4 ila 7 parçayı DOĞRU SIRASIYLA 'parcalar' dizisi olarak ver (sistem bunları ekranda karıştırıp öğrenciye tıklatarak sıraya dizdirecek). "
            "Kesinlikle $ işareti veya LaTeX kodu kullanma. SADECE geçerli bir JSON dizisi döndür:\n"
            '[\n'
            '  {\n'
            '    "kazanim": "İlgili alt konu",\n'
            '    "yonerge": "Aşağıdaki karışık parçaları anlamlı ve kurallı bir cümle / doğru kural olacak şekilde sıraya dizin:",\n'
            '    "parcalar": ["1. parça", "2. parça", "3. parça", "4. parça"],\n'
            '    "ipucu": "İlk ve son parçaya dikkat et",\n'
            '    "cozum": "Doğru diziliş ve açıklaması"\n'
            '  }\n'
            ']'
        )
        try:
            raw = _mufredat_destekli_gemini_json(prompt, cozulen_kod, cozulen_unite_no)
        except Exception:
            raw = ask_gemini(prompt)
        veriler = []
        try:
            m = re.search(r"\[.*\]", raw, re.DOTALL)
            if m:
                veriler = clean_math_text(json.loads(m.group(0)))
        except Exception:
            veriler = []
        norm = []
        for idx, item in enumerate(veriler if isinstance(veriler, list) else [], 1):
            if not isinstance(item, dict):
                continue
            parcalar = item.get("parcalar") or item.get("kelimeler") or item.get("adimlar") or []
            if isinstance(parcalar, str):
                parcalar = [p.strip() for p in parcalar.split() if p.strip()]
            parcalar = [str(p).strip() for p in parcalar if str(p).strip()]
            if len(parcalar) >= 2:
                dogru_dizilis = " ".join(parcalar)
                norm.append({
                    "kazanim": item.get("kazanim") or f"{konu} • Etkinlik {idx}",
                    "yonerge": str(item.get("yonerge") or item.get("soru") or "Karışık verilen parçaları doğru sırayla tıklayarak dizin:").strip(),
                    "parcalar": parcalar,
                    "dogru_dizilis": dogru_dizilis,
                    "ipucu": str(item.get("ipucu") or "Anlam ve kural bütünlüğüne dikkat et.").strip(),
                    "cozum": str(item.get("cozum") or f"Doğru sıralama: {dogru_dizilis}").strip()
                })
        return norm

    return []


