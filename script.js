/* ==========================================================================
   SCRIPT.JS - Lógica do Frontend "Voz do Povo"
   ========================================================================== */

const API_URL = ""; // Vercel usa caminho relativo

let currentPL = null;
let synth = window.speechSynthesis;
let utterance = null;
let currentVoteType = null;
let currentTextToSpeak = ""; // Guarda o texto atual para quando mudar a velocidade

// 1. DADOS DOS PROJETOS DE LEI
const PL_DATA = [
    { 
        id: 1, 
        title: "PL 2630/2020 (Fake News)", 
        summary: "Regras para redes sociais e combate à desinformação.", 
        fullText: "O projeto institui a Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet. Estabelece obrigações para provedores de redes sociais visando combater a desinformação (fake news) e contas robôs.",
        author: "Dep. Orlando Silva",
        email: "dep.orlandosilva@camara.leg.br"
    },
    { 
        id: 2, 
        title: "Reforma Tributária", 
        summary: "Mudança nos impostos do consumo (IVA) e Cashback.", 
        fullText: "A proposta unifica cinco tributos (PIS, Cofins, IPI, ICMS e ISS) em uma cobrança única (IVA). Cria o Cashback para devolver impostos a famílias de baixa renda e o Imposto Seletivo para produtos nocivos.",
        author: "Dep. Aguinaldo Ribeiro",
        email: "dep.aguinaldoribeiro@camara.leg.br"
    },
    { 
        id: 3, 
        title: "Taxação de Importações", 
        summary: "Imposto para compras internacionais (Shein/Shopee).", 
        fullText: "Dispõe sobre o tratamento tributário nas importações. Compras até US$ 50 pagam apenas ICMS (17%). Acima de US$ 50, paga-se 60% de imposto federal mais o ICMS estadual.",
        author: "Ministério da Fazenda",
        email: "gabinete.ministro@fazenda.gov.br"
    }
];

// 2. TEMA (DARK MODE)
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const icon = document.getElementById('theme-icon');
    
    if (document.body.classList.contains('dark-mode')) {
        icon.classList.replace('fa-moon', 'fa-sun');
        localStorage.setItem('theme', 'dark');
    } else {
        icon.classList.replace('fa-sun', 'fa-moon');
        localStorage.setItem('theme', 'light');
    }
}

if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    const icon = document.getElementById('theme-icon');
    if(icon) icon.classList.replace('fa-moon', 'fa-sun');
}

// 3. SIMULAÇÃO GPS
function simulateGPS() {
    const toast = document.getElementById('gps-toast');
    if (toast) {
        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.style.transition = "opacity 0.5s";
            toast.style.opacity = '0';
            setTimeout(() => toast.classList.add('hidden'), 500);
        }, 4000);
    }
}

// 4. NAVEGAÇÃO ENTRE TELAS
function navigateTo(viewName) {
    stopAudio();
    document.querySelectorAll('.view').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        setTimeout(() => targetView.classList.add('active'), 10);
    }
    window.scrollTo(0, 0);
}

// 5. SELEÇÃO DO PL
function selectPL(id) {
    const pl = PL_DATA.find(item => item.id === id);
    if (!pl) return;

    currentPL = pl;

    document.getElementById('pl-title-display').innerText = pl.title;
    document.getElementById('pl-summary-display').innerText = pl.summary;

    document.getElementById('ai-result').classList.add('hidden');
    document.getElementById('vote-section').classList.add('hidden');
    document.getElementById('tags-container').classList.add('hidden');
    document.getElementById('user-interest').value = "";
    
    navigateTo('details');
}

// 6. LÓGICA DE ÁUDIO (ATUALIZADA)
function changeSpeed() {
    if (synth.speaking) {
        stopAudio();
        // Pequeno delay para evitar conflito de áudio
        setTimeout(() => speak(currentTextToSpeak), 50);
    }
}

function toggleAudio() {
    if (synth.speaking) {
        if (synth.paused) {
            synth.resume();
            updatePlayButton(true);
        } else {
            synth.pause();
            updatePlayButton(false);
        }
    } else {
        const text = document.getElementById('text-output').innerText;
        if (text) speak(text);
    }
}

function stopAudio() {
    synth.cancel();
    updatePlayButton(false);
    const progressBar = document.getElementById('speech-progress');
    if(progressBar) progressBar.value = 0;
}

function speak(text) {
    synth.cancel(); // Para qualquer áudio anterior

    currentTextToSpeak = text;
    utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    
    // Pega a velocidade selecionada
    const speedSelect = document.getElementById('speed-select');
    utterance.rate = speedSelect ? parseFloat(speedSelect.value) : 1.0;

    const progressBar = document.getElementById('speech-progress');

    // Atualiza a barrinha enquanto fala
    utterance.onboundary = function(event) {
        const percentage = (event.charIndex / text.length) * 100;
        if(progressBar) progressBar.value = percentage;
    };

    utterance.onstart = () => updatePlayButton(true);
    
    utterance.onend = () => {
        updatePlayButton(false);
        if(progressBar) progressBar.value = 100;
    };

    utterance.onerror = () => updatePlayButton(false);
    
    synth.speak(utterance);
}

function updatePlayButton(isPlaying) {
    const btn = document.getElementById('play-pause-btn');
    if (!btn) return;
    if (isPlaying) {
        btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pausar';
        btn.classList.add('playing');
    } else {
        btn.innerHTML = '<i class="fa-solid fa-play"></i> Ouvir Agora';
        btn.classList.remove('playing');
    }
}

// 7. VOTAÇÃO E EMAIL
function vote(type) {
    currentVoteType = type === 'up' ? "Concordo" : "Discordo";
    const tagsContainer = document.getElementById('tags-container');
    tagsContainer.classList.remove('hidden');
    tagsContainer.scrollIntoView({ behavior: 'smooth' });
}

async function submitReason(reason) {
    if (!currentVoteType || !currentPL) return;

    alert(`📨 Enviando e-mail para: ${currentPL.author}...`);

    try {
        const response = await fetch('/send_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pl_title: currentPL.title,
                author_name: currentPL.author,
                author_email: currentPL.email,
                vote_type: currentVoteType,
                reason: reason
            })
        });

        const data = await response.json();
        alert(`✅ ${data.message}\nSua opinião foi registrada!`);
        
        document.getElementById('vote-section').classList.add('hidden');

    } catch (error) {
        console.error(error);
        alert("Erro ao enviar feedback.");
    }
}

// 8. CONEXÃO COM IA (BACKEND)
async function getAIExplanation() {
    const userInterest = document.getElementById('user-interest').value.trim();
    
    if (!currentPL || !userInterest) {
        alert("Por favor, digite um tema!");
        return;
    }

    const resultBox = document.getElementById('ai-result');
    const loader = document.getElementById('loader');
    const audioCard = document.getElementById('audio-card');
    const contentBox = document.getElementById('explanation-content');
    const textOutput = document.getElementById('text-output');
    const voteSection = document.getElementById('vote-section');

    stopAudio();
    
    // Reseta UI
    resultBox.classList.remove('hidden');
    loader.classList.remove('hidden');
    audioCard.classList.add('hidden');
    contentBox.classList.add('hidden');
    voteSection.classList.add('hidden');

    try {
        const response = await fetch('/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pl_text: currentPL.fullText,
                user_interest: userInterest
            })
        });

        if (!response.ok) throw new Error('Erro no servidor');

        let data = await response.json();
        // Garante que data é um objeto
        if (typeof data === 'string') { 
            try { data = JSON.parse(data); } 
            catch(e) { data = {explanation: data}; } 
        }

        textOutput.innerText = data.explanation;

        loader.classList.add('hidden');
        audioCard.classList.remove('hidden');
        contentBox.classList.remove('hidden');
        voteSection.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        loader.classList.add('hidden');
        alert("Erro ao conectar com a IA.");
    }
}

// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('home');
    setTimeout(simulateGPS, 1000);
});