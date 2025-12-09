import os
import time
import random
import requests
import urllib3
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# 1. AYARLAR
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

app = Flask(__name__)

# 2. BAĞLANTILARI KUR
print("\n--- SİSTEM BAŞLATILIYOR ---")
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # En hızlı ve zeki model
    model = genai.GenerativeModel('gemini-flash-latest') 
    print("✅ Yapay Zeka: HAZIR")
except Exception as e:
    print(f"❌ Yapay Zeka Hatası: {e}")

try:
    sp_auth = SpotifyClientCredentials(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET")
    )
    sp = spotipy.Spotify(auth_manager=sp_auth)
    print("✅ Müzik Servisi: HAZIR")
except Exception as e:
    print(f"❌ Müzik Servisi Hatası: {e}")


# --- 3. BEYİN KISMI (Burada Mantıksal Çıkarım Yapılıyor) ---

def ask_gemini_logic(text, choice_type):
    """
    Bu fonksiyon senin cümleni alır, analiz eder ve 
    API'lerin anlayacağı dile çevirir.
    """
    print(f"\n🧠 ANALİZ EDİLİYOR: '{text}' ({choice_type})")
    
    if choice_type == 'red': # FİLM ANALİZİ
        prompt = f"""
        Sen uzman bir psikolog ve film eleştirmenisin.
        Kullanıcı bana şu cümleyi kurdu: "{text}"
        
        GÖREVİN:
        1. Bu cümlenin altındaki duyguyu anla (Örn: Aşık olduysa Romantik, Yorulduysa Sakin, Kızgınsa Aksiyon).
        2. Bu duyguya EN UYGUN TMDB tür ID'lerini seç.
        
        ID REFERANS:
        28=Aksiyon, 12=Macera, 35=Komedi, 80=Suç, 18=Dram, 
        10751=Aile, 14=Fantastik, 36=Tarih, 27=Korku, 10402=Müzik, 
        9648=Gizem, 10749=Romantik, 878=Bilim Kurgu, 53=Gerilim.

        CEVAP FORMATI (Tek satır, araya || koy):
        Duygu Özeti || ID1,ID2
        
        ÖRNEK:
        Aşık ve Mutlu || 10749,35
        """
    else: # MÜZİK ANALİZİ
        prompt = f"""
        Sen uzman bir DJ'sin.
        Kullanıcı bana şu cümleyi kurdu: "{text}"
        
        GÖREVİN:
        1. Bu cümlenin modunu analiz et.
        2. Spotify'da aratıldığında tam bu moda uygun şarkıları getirecek 2-3 İngilizce anahtar kelime ver.
        
        CEVAP FORMATI (Tek satır, araya || koy):
        Duygu Özeti || ingilizce kelimeler
        
        ÖRNEK:
        Hüzünlü ve Yalnız || sad piano cello ambient
        """

    # Hata olursa tekrar deneme mekanizması (Retry Logic)
    for attempt in range(3): # 3 kere dene
        try:
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            if "||" in result:
                parts = result.split("||")
                mood_name = parts[0].strip()
                search_params = parts[1].strip()
                
                print(f"✅ ÇIKARIM YAPILDI: {mood_name} -> {search_params}")
                return mood_name, search_params
            else:
                # Format yanlışsa tekrar denesin
                print("⚠️ Format hatası, tekrar deneniyor...")
                time.sleep(1)

        except Exception as e:
            print(f"⚠️ API Meşgul ({attempt+1}/3), bekleniyor... Hata: {e}")
            time.sleep(2) # 2 saniye bekle ve tekrar dene
    
    # 3 kere denedi yine olmadıysa (İnternet yoksa)
    print("❌ Analiz Başarısız.")
    return "Karmaşık Ruh Hali", None


# --- 4. VERİ ÇEKME MOTORLARI ---

def fetch_movie(genres):
    if not genres: genres = "18" # Yedek (Dram)
    print(f"🎬 TMDB Sorgusu: {genres}")
    
    try:
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            'api_key': os.getenv("TMDB_API_KEY"),
            'with_genres': genres,
            'sort_by': 'popularity.desc',
            'vote_count.gte': 200,
            'language': 'tr-TR',
            'page': random.randint(1, 2)
        }
        res = requests.get(url, params=params, verify=False)
        data = res.json()
        
        if data.get('results'):
            m = random.choice(data['results'])
            return {
                'type': 'movie',
                'title': m['title'],
                'desc': m.get('overview', 'Özet yok.'),
                'rating': m.get('vote_average'),
                'image': f"https://image.tmdb.org/t/p/w780{m['poster_path']}" if m.get('poster_path') else None
            }
    except Exception as e:
        print(f"🔴 Film API Hatası: {e}")
    return None

def fetch_music(query):
    if not query: query = "top hits"
    print(f"🎵 Spotify Sorgusu: {query}")
    
    try:
        results = sp.search(q=query, type='playlist', limit=5)
        items = results.get('playlists', {}).get('items')
        
        if items:
            chosen = random.choice(items)
            return {
                'type': 'music',
                'title': chosen['name'],
                'desc': f"Senin için: {query}",
                'image': chosen['images'][0]['url'] if chosen.get('images') else None,
                'url': chosen['external_urls']['spotify']
            }
    except Exception as e:
        print(f"🔴 Spotify Hatası: {e}")
    return None

# --- 5. ROTALAR ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/make_choice', methods=['POST'])
def make_choice():
    try:
        data = request.json
        user_input = data.get('user_input')
        pill = data.get('pill_color')

        if not user_input or len(user_input) < 2:
            return jsonify({'error': 'Lütfen hislerini anlat Neo.'}), 400

        # 1. ADIM: ZEKİ ANALİZ (Bekleme mekanizmalı)
        mood, params = ask_gemini_logic(user_input, pill)
        
        # Eğer yapay zeka cevap veremezse (İnternet kopuk vs.)
        if not params:
            return jsonify({'error': 'Matrix şu an aşırı yüklü. 5 saniye sonra tekrar dene.'}), 503

        # 2. ADIM: SONUÇ GETİRME
        result = None
        if pill == 'red':
            result = fetch_movie(params)
        elif pill == 'green':
            result = fetch_music(params)
        
        if result:
            result['mood'] = mood
            return render_template('result.html', **result)
        else:
            return jsonify({'error': 'Bu duyguya uygun içerik bulunamadı.'}), 404

    except Exception as e:
        print(f"SİSTEM HATASI: {e}")
        return jsonify({'error': 'Bilinmeyen bir hata oluştu.'}), 500

if __name__ == '__main__':
    app.run(debug=True)