const API_URL = ""; 

let currentPL = null;
let synth = window.speechSynthesis;
let utterance = null;
let currentVoteType = null;
let currentTextToSpeak = ""; 

const PL_DATA = [
    { 
        id: 1, 
        title: "Proibição de Apologia ao Crime (SP)", 
        summary: "Veda shows financiados pela prefeitura que incentivem drogas ou crime.", 
        pdfUrl: "pdfs/pl_shows_sp.pdf", 
        author: "Ver. Amanda Vettorazzo",
        fullText: "PROJETO DE LEI DA VEREADORA AMANDA VETTORAZZO. Proíbe a contratação de shows e eventos abertos ao público infantojuvenil que envolvam apologia ao crime ou uso de drogas.",
        scope: 'minha_rua',
        trending: false,
        tagName: "🛡️ Segurança",
        tagClass: "urgent"
    },
    { 
        id: 2, 
        title: "PL das Fake News (2630/2020)", 
        summary: "Lei de Liberdade, Responsabilidade e Transparência na Internet.", 
        pdfUrl: "pdfs/pl_fake_news.pdf", 
        author: "Sen. Alessandro Vieira",
        fullText: "PROJETO DE LEI Nº 2630, DE 2020. Institui a Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet. Estabelece normas para redes sociais e combate à desinformação.",
        scope: 'brasil',
        trending: true,
        tagName: "🔥 Polêmica",
        tagClass: "urgent"
    },
    { 
        id: 3, 
        title: "Protocolo Anti-Bullying", 
        summary: "Cria mecanismos de proteção psicológica nas escolas.", 
        pdfUrl: "pdfs/pl_bullying.pdf", 
        author: "Dep. Gilvan Maximo",
        fullText: "PROJETO DE LEI N.º 1.367, DE 2024. Cria o PROTOCOLO 'BULLYING NÃO É BRINCADEIRA'. Obriga escolas a notificarem coordenação pedagógica e conselho tutelar.",
        scope: 'minha_rua',
        trending: false,
        tagName: "🏫 Educação",
        tagClass: "shop"
    },
    { 
        id: 4, 
        title: "Proibição de Linguagem Neutra", 
        summary: "Veda o uso de 'todes/amigues' em escolas e concursos.", 
        pdfUrl: "pdfs/pl_linguagem.pdf", 
        author: "Dep. Mauricio do Vôlei",
        fullText: "PROJETO DE LEI N.º 2.080, DE 2024. Dispõe sobre a proibição do uso e do ensino da linguagem neutra nas instituições de ensino públicas e privadas.",
        scope: 'brasil',
        trending: true,
        tagName: "🗣️ Cultura",
        tagClass: "shop"
    },
    { 
        id: 5, 
        title: "Atualização do Código Civil", 
        summary: "Reforma sobre direitos digitais, família e contratos.", 
        pdfUrl: "pdfs/pl_civil.pdf", 
        author: "Sen. Rodrigo Pacheco",
        fullText: "PROJETO DE LEI N° 4, DE 2025. Atualização do Código Civil. Reconhece direitos digitais, herança digital e proteção especial aos animais.",
        scope: 'brasil',
        trending: true,
        tagName: "⚖️ Legislação",
        tagClass: "money"
    }
];

function filterFeed(filterType, btnElement) {
    if (btnElement) {
        const buttons = document.querySelectorAll('.filter-scroll .filter-pill');
        buttons.forEach(btn => btn.classList.remove('active'));
        btnElement.classList.add('active');
    }

    let filteredData = [];

    if (filterType === 'minha_rua') {
        filteredData = PL_DATA.filter(item => item.scope === 'minha_rua');
    } else if (filterType === 'brasil') {
        filteredData = PL_DATA.filter(item => item.scope === 'brasil');
    } else if (filterType === 'em_alta') {
        filteredData = PL_DATA.filter(item => item.trending === true);
    } else {
        filteredData = PL_DATA; 
    }

    renderCards(filteredData);
}

function renderCards(items) {
    const container = document.getElementById('feed-container');
    container.innerHTML = ""; 

    if (items.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-secondary); padding: 20px;">
                <i class="fa-solid fa-box-open" style="font-size: 2rem; margin-bottom: 10px;"></i>
                <p>Nenhum projeto encontrado nesta categoria.</p>
            </div>
        `;
        return;
    }

    items.forEach(item => {
        const cardHTML = `
            <article class="pl-card" onclick="selectPL(${item.id})">
                <span class="tag-badge ${item.tagClass}">${item.tagName}</span>
                <h3>${item.title}</h3>
                <p>${item.summary}</p>
            </article>
        `;
        container.innerHTML += cardHTML;
    });
}

function navigateTo(viewName) {
    if (viewName !== 'details') {
        stopAudio();
    }

    document.querySelectorAll('.view').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });

    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        setTimeout(() => targetView.classList.add('active'), 10);
    }

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const activeBtn = document.getElementById(`nav-${viewName}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    window.scrollTo(0, 0);
}

function selectPL(id) {
    const pl = PL_DATA.find(item => item.id === id);
    if (!pl) return;

    currentPL = pl;

    document.getElementById('pl-title-display').innerText = pl.title;
    document.getElementById('pl-summary-display').innerText = pl.summary;

    const pdfBtn = document.getElementById('btn-view-pdf');
    const miniPdfBtn = document.getElementById('mini-pdf-btn');

    if (pl.pdfUrl) {
        if(pdfBtn) {
            pdfBtn.href = pl.pdfUrl;
            pdfBtn.classList.remove('hidden');
        }
        if(miniPdfBtn) {
            miniPdfBtn.href = pl.pdfUrl;
            miniPdfBtn.style.display = 'flex';
        }
    } else {
        if(pdfBtn) pdfBtn.classList.add('hidden');
        if(miniPdfBtn) miniPdfBtn.style.display = 'none';
    }

    resetAIView();
    navigateTo('details');
}

function resetAIView() {
    document.getElementById('ai-result').classList.add('hidden');
    document.getElementById('vote-section').classList.add('hidden');
    document.getElementById('tags-container').classList.add('hidden');
    document.getElementById('user-interest').value = "";
    document.getElementById('loader').classList.add('hidden');
}

async function getAIExplanation() {
    const userInterest = document.getElementById('user-interest').value.trim();
    
    if (!currentPL || !userInterest) {
        alert("Por favor, digite um tema! Ex: Futebol, Bar, Novela...");
        return;
    }

    stopAudio();
    const resultBox = document.getElementById('ai-result');
    const loader = document.getElementById('loader');
    const audioCard = document.getElementById('audio-card');
    const contentBox = document.getElementById('explanation-content');
    const voteSection = document.getElementById('vote-section');

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

        if (!response.ok) throw new Error('Erro na resposta do servidor');

        let data = await response.json();
        
        if (typeof data === 'string') { 
            try { data = JSON.parse(data); } 
            catch(e) { data = { explanation: data }; } 
        }

        document.getElementById('text-output').innerText = data.explanation;

        loader.classList.add('hidden');
        audioCard.classList.remove('hidden');
        contentBox.classList.remove('hidden');
        voteSection.classList.remove('hidden');

    } catch (error) {
        console.error(error);
        loader.classList.add('hidden');
        alert("Erro ao conectar com a IA. Verifique se o backend está rodando.");
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

function changeSpeed() {
    if (synth.speaking) {
        stopAudio();
        setTimeout(() => {
            const text = document.getElementById('text-output').innerText;
            if(text) speak(text);
        }, 50);
    }
}

function speak(text) {
    synth.cancel(); 
    currentTextToSpeak = text;
    utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    
    const speedSelect = document.getElementById('speed-select');
    utterance.rate = speedSelect ? parseFloat(speedSelect.value) : 1.0;

    const progressBar = document.getElementById('speech-progress');

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

function vote(type) {
    currentVoteType = type === 'up' ? "Concordo" : "Discordo";
    const tagsContainer = document.getElementById('tags-container');
    tagsContainer.classList.remove('hidden');
    tagsContainer.scrollIntoView({ behavior: 'smooth' });
}

function submitReason(reason) {
    if (!currentVoteType || !currentPL) return;
    alert(`✅ Opinião registrada!\n\nLei: ${currentPL.title}\nVoto: ${currentVoteType}\nMotivo: ${reason}\n\n(Enviado simbolicamente para ${currentPL.author})`);
    document.getElementById('vote-section').classList.add('hidden');
}

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

function simulateGPS() {
    const toast = document.getElementById('gps-toast');
    if (toast) {
        toast.classList.remove('hidden');
        setTimeout(() => {
            toast.style.transition = "opacity 0.5s";
            toast.style.opacity = '0';
            setTimeout(() => {
                toast.classList.add('hidden');
                toast.style.opacity = '1';
            }, 500);
        }, 3000);
    }
}

function openObrasSite() {
    window.open("https://obrasorg.vercel.app/", "_blank");
}

function checkLoginStatus() {
    const userIcon = document.querySelector('.user-icon');
    const existingAvatar = document.querySelector('.user-logged-in');
    const userData = localStorage.getItem('vozDoPovoUser');

    if (userData) {
        const user = JSON.parse(userData);
        
        if (userIcon) {
            userIcon.outerHTML = `
                <div class="user-logged-in" onclick="logout()" title="Sair de ${user.name}">
                    <img src="${user.avatar}" alt="Avatar" style="width: 35px; height: 35px; border-radius: 50%; border: 2px solid white;">
                </div>
            `;
        }
    } else {
        if (userIcon) {
            userIcon.onclick = () => {
                window.location.href = "login.html";
            };
        }
    }
}

function logout() {
    if(confirm("Deseja sair da sua conta Gov.br?")) {
        localStorage.removeItem('vozDoPovoUser');
        window.location.reload();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        const icon = document.getElementById('theme-icon');
        if(icon) icon.classList.replace('fa-moon', 'fa-sun');
    }

    navigateTo('home');
    
    const initialBtn = document.querySelector('.filter-scroll .filter-pill.active') || document.querySelector('.filter-scroll .filter-pill');
    if (initialBtn) {
        filterFeed('minha_rua', initialBtn);
    } else {
        renderCards(PL_DATA);
    }

    setTimeout(simulateGPS, 1500);

    checkLoginStatus();

// ==========================================================================
// FUNÇÃO DE ACESSIBILIDADE (DALTÔNICO)
// ==========================================================================
function toggleDaltonismo() {
    const body = document.body;
    
    // Alterna a classe
    body.classList.toggle('daltonico-mode');
    
    // (Opcional) Salva a preferência no navegador
    if (body.classList.contains('daltonico-mode')) {
        localStorage.setItem('accessibilityMode', 'on');
    } else {
        localStorage.setItem('accessibilityMode', 'off');
    }
}

// Verifica se já estava ativado ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    // ... seus outros códigos de load ...
    
    // Verifica preferência salva
    if (localStorage.getItem('accessibilityMode') === 'on') {
        document.body.classList.add('daltonico-mode');
    }
});
});

