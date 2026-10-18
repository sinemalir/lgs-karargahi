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


MEB_8_SINIF_KONULARI = {
    "Türkçe": [
        "Sözcükte ve Söz Öbeklerinde Anlam",
        "Cümlede Anlam ve Yorum",
        "Paragrafta Anlam ve Ana Düşünce",
        "Sözel Mantık ve Muhakeme",
        "Görsel Okuma ve Grafik Yorumlama",
        "Fiilimsiler (Eylemsiler)",
        "Cümlenin Ögeleri",
        "Fiilde Çatı",
        "Cümle Türleri",
        "Yazım Kuralları ve Noktalama İşaretleri",
        "Anlatım Bozuklukları",
        "Metin Türleri ve Söz Sanatları",
    ],
    "Matematik": [
        "Çarpanlar ve Katlar (EBOB - EKOK)",
        "Üslü İfadeler",
        "Kareköklü İfadeler",
        "Veri Analizi (Çizgi, Sütun ve Daire Grafiği)",
        "Basit Olayların Olma Olasılığı",
        "Cebirsel İfadeler ve Özdeşlikler",
        "Doğrusal Denklemler ve Eğim",
        "Eşitsizlikler",
        "Üçgenler ve Eşlik - Benzerlik",
        "Dönüşüm Geometrisi",
        "Geometrik Cisimler (Silindir, Piramit, Koni)",
    ],
    "Fen Bilimleri": [
        "Mevsimler ve İklim",
        "DNA ve Genetik Kod (Kalıtım, Mutasyon, Biyoteknoloji)",
        "Basınç (Katı, Sıvı ve Gaz Basıncı)",
        "Madde ve Endüstri (Periyodik Sistem, Kimyasal Tepkimeler, Asit-Baz)",
        "Basit Makineler",
        "Enerji Dönüşümleri ve Çevre Bilimi (Besin Zinciri, Fotosentez, Solunum)",
        "Elektrik Yükleri ve Elektrik Enerjisi",
    ],
    "İnkılap Tarihi": [
        "Bir Kahraman Doğuyor",
        "Milli Uyanış: Bağımsızlık Yolunda Atılan Adımlar",
        "Milli Bir Destan: Ya İstiklal Ya Ölüm!",
        "Atatürkçülük ve Çağdaşlaşan Türkiye",
        "Demokratikleşme Çabaları",
        "Atatürk Dönemi Türk Dış Politikası",
        "Atatürk'ün Ölümü ve Sonrası",
    ],
    "İngilizce": [
        "Unit 1: Friendship",
        "Unit 2: Teen Life",
        "Unit 3: In The Kitchen",
        "Unit 4: On The Phone",
        "Unit 5: The Internet",
        "Unit 6: Adventures",
        "Unit 7: Tourism",
        "Unit 8: Chores",
        "Unit 9: Science",
        "Unit 10: Natural Forces",
    ],
    "Din Kültürü": [
        "Kader İnancı (Kader ve Kaza, İnsanın İradesi)",
        "Zekat ve Sadaka İbadeti",
        "Din ve Hayat (Din, Birey ve Toplum)",
        "Hz. Muhammed'in (s.a.v.) Örnekliği",
        "Kur'an-ı Kerim ve Özellikleri",
    ],
}


def get_ai_lgs_topics(ders, force_ai=False):
    """Seçilen 8. sınıf LGS dersi için yapay zeka destekli konu listesini döndürür."""
    varsayilan = MEB_8_SINIF_KONULARI.get(ders, MEB_8_SINIF_KONULARI["Matematik"])
    if not force_ai:
        # Hızlı ve kesintisiz deneyim için MEB müfredat konularını + yapay zeka alt başlıklarını getirir
        prompt = (
            f"8. Sınıf MEB LGS '{ders}' dersinin en önemli tüm ünite ve alt konularını listele. "
            "SADECE geçerli bir JSON string dizisi döndür, başka hiçbir metin yazma. "
            'Örnek: ["1. Konu Adı", "2. Konu Adı"]'
        )
        raw = ask_gemini(prompt)
        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                parsed = clean_math_text(json.loads(match.group(0)))
                if isinstance(parsed, list) and len(parsed) >= 4:
                    return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return varsayilan
    else:
        prompt = (
            f"8. Sınıf MEB LGS '{ders}' dersi için sınavda en çok çıkan 10 spesifik alt konu ve kazanım başlığı öner. "
            "SADECE geçerli bir JSON string dizisi döndür, başka hiçbir metin yazma."
        )
        raw = ask_gemini(prompt)
        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                parsed = clean_math_text(json.loads(match.group(0)))
                if isinstance(parsed, list) and len(parsed) >= 4:
                    return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return varsayilan


def _fetch_test_batch(ders, konu, zorluk, adet, baslangic_no=1):
    prompt = (
        f"8. Sınıf MEB LGS müfredatına %100 uygun olarak '{ders}' dersi, '{konu}' konusu ve '{zorluk}' zorluk seviyesinde "
        f"TAM {adet} ADET çoktan seçmeli yeni nesil LGS sorusu hazırla (Soru {baslangic_no}'den Soru {baslangic_no + adet - 1}'e kadar). "
        "ÖNEMLİ KURALLAR:\n"
        "1. Kesinlikle $ işareti veya LaTeX kodu ($m^2$, \\frac vb.) KULLANMA! Birimleri ve üslü/köklü sayıları m², cm², cm³, 2⁵, √3 gibi doğrudan okunaklı Unicode karakterlerle yaz.\n"
        "2. Her sorunun 4 şıkkı (A, B, C, D), 1 kısa ipucu ve adım adım net çözümü olsun.\n"
        "3. Yanıtı SADECE geçerli bir JSON dizisi olarak ver, başka hiçbir açıklama yazma. Format:\n"
        "[\n"
        "  {\n"
        f'    "soru_no": "Soru {baslangic_no}",\n'
        f'    "kazanim": "{konu} ({zorluk})",\n'
        '    "soru": "Soru hikayesi ve soru kökü...",\n'
        '    "secenekler": ["A) ...", "B) ...", "C) ...", "D) ..."],\n'
        '    "dogru_index": 0,\n'
        '    "ipucu": "Soruyu çözdüren anahtar ipucu...",\n'
        '    "cozum": "1. Adım: ... 2. Adım: ... Doğru Cevap: A"\n'
        "  }\n"
        "]"
    )
    raw = ask_gemini(prompt)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            veriler = clean_math_text(json.loads(match.group(0)))
            if isinstance(veriler, list):
                return veriler
    except Exception:
        pass
    return []


def generate_custom_lgs_test(ders, konu, zorluk, soru_sayisi=5):
    """Seçilen ders, konu, zorluk ve soru sayısına (5, 10, 20) göre interaktif LGS testi üretir."""
    soru_sayisi = int(soru_sayisi)
    if soru_sayisi <= 10:
        sonuc = _fetch_test_batch(ders, konu, zorluk, soru_sayisi, baslangic_no=1)
    else:
        ilk_yari = _fetch_test_batch(ders, konu, zorluk, 10, baslangic_no=1)
        ikinci_yari = _fetch_test_batch(ders, konu, zorluk, soru_sayisi - 10, baslangic_no=11)
        sonuc = ilk_yari + ikinci_yari

    # Numaraları ve alanları standartlaştır
    temiz_liste = []
    for idx, item in enumerate(sonuc, 1):
        if isinstance(item, dict):
            item["soru_no"] = f"Soru {idx}"
            if not item.get("kazanim"):
                item["kazanim"] = f"{konu} • {zorluk}"
            temiz_liste.append(item)
    return temiz_liste

