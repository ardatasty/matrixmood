// --- Morpheus'un Konuşma Sistemi ---
const textEl = document.getElementById('morpheusText');
let typingTimer;

function speak(text) {
    // Varsa eski yazma işlemini durdur
    clearTimeout(typingTimer);
    textEl.innerHTML = "";
    let i = 0;
    function type() {
        if (i < text.length) {
            textEl.innerHTML += text.charAt(i);
            i++;
            typingTimer = setTimeout(type, 30);
        }
    }
    type();
}

// Sayfa Açılışı
window.onload = () => {
    speak("Zihnin uyanıyor... Ne hissediyorsun?");
    startMatrix();
};

// --- Hover (Işık) Efekti ---
const ambient = document.getElementById('ambientLight');
const morpheus = document.querySelector('.morpheus-img');

function hoverEffect(color) {
    if (color === 'red') {
        // SOL TARAF KIRMIZI (Linear Gradient)
        ambient.style.background = 'linear-gradient(90deg, rgba(255,0,0,0.3) 0%, rgba(0,0,0,0) 60%)';
        morpheus.style.filter = "drop-shadow(-15px 0 20px rgba(255,0,0,0.4))";
        speak("Gerçekler acıdır... Ama özgürleştirir. Hazır mısın?");
    } else {
        // SAĞ TARAF YEŞİL (Linear Gradient)
        ambient.style.background = 'linear-gradient(-90deg, rgba(0,255,0,0.3) 0%, rgba(0,0,0,0) 60%)';
        morpheus.style.filter = "drop-shadow(15px 0 20px rgba(0,255,0,0.4))";
        speak("Huzurlu bir yalan... Müziğin içinde kaybolmak.");
    }
}

function resetEffect() {
    ambient.style.background = 'radial-gradient(circle at center, transparent 0%, #000 90%)';
    morpheus.style.filter = "drop-shadow(0 10px 20px #000)";
    
    // Eğer input doluysa ona göre konuş, boşsa varsayılan
    const inputVal = document.getElementById('userInput').value;
    if(inputVal.length > 0) speak("Bu ilginç bir his...");
    else speak("Seçimini bekliyorum.");
}

// --- Seçim ve Scroll İşlemi ---
function makeChoice(color) {
    const input = document.getElementById('userInput').value;
    const resultSection = document.getElementById('resultSection');
    const resultContent = document.getElementById('resultContent');
    const loading = document.getElementById('loading');

    if (input.length < 2) {
        speak("Sessizlik... Bana bir şeyler söylemelisin.");
        return;
    }

    // Morpheus tepki versin
    speak(`"${input}"... Anlaşıldı. Veri akışı başlıyor.`);

    // 1. Sonuç bölümüne kaydır
    resultSection.classList.add('result-active');
    resultSection.scrollIntoView({ behavior: 'smooth' });
    
    // 2. Yükleniyor göster
    loading.style.display = 'block';
    resultContent.innerHTML = '';

    // 3. Veriyi Çek
    fetch('/make_choice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_input: input, pill_color: color })
    })
    .then(r => r.text())
    .then(html => {
        loading.style.display = 'none';
        
        // Hata kontrolü (Basit JSON parse denemesi)
        try {
            const data = JSON.parse(html);
            if(data.error) {
                resultContent.innerHTML = `<h2 style="color:red; text-align:center">${data.error}</h2>`;
                speak("Bir hata oluştu.");
                return;
            }
        } catch(e) {}

        // 4. HTML'i bas
        resultContent.innerHTML = html;
        speak("İşte senin için bulduklarım. Aşağıda.");
    })
    .catch(err => {
        loading.style.display = 'none';
        resultContent.innerHTML = "<h2 style='color:red'>Bağlantı Hatası.</h2>";
    });
}

// --- Matrix Yağmuru ---
function startMatrix() {
    const c = document.getElementById('matrixCanvas');
    const ctx = c.getContext('2d');
    c.width = window.innerWidth; c.height = window.innerHeight;
    const chars = '01'.split('');
    const drops = Array(Math.floor(c.width/20)).fill(1);

    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.fillStyle = '#0F0';
        ctx.font = '15px monospace';
        drops.forEach((y, i) => {
            const text = chars[Math.floor(Math.random()*chars.length)];
            ctx.fillText(text, i*20, y*20);
            if(y*20 > c.height && Math.random() > 0.98) drops[i] = 0;
            drops[i]++;
        });
    }
    setInterval(draw, 50);
}