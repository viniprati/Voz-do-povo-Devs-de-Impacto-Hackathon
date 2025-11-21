/* ==========================================================================
   SCRIPT.JS - Lógica do Frontend "Voz do Povo" (Completo)
   ========================================================================== */

const API_URL = "";
let currentPL = null;
let synth = window.speechSynthesis; // API nativa de voz
let utterance = null;

// 1. DADOS (MOCK DATABASE)
const PL_DATA = [
    { 
        id: 1, 
        title: "PL 2630/2020 (Fake News)", 
        summary: "Regras para redes sociais e combate à desinformação.", 
        fullText: "O projeto institui a Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet. Estabelece obrigações para provedores de redes sociais visando combater a desinformação (fake news) e contas robôs." 
    },
    { 
        id: 2, 
        title: "Reforma Tributária", 
        summary: "Mudança nos impostos do consumo (IVA) e Cashback.", 
        fullText: "A proposta unifica cinco tributos (PIS, Cofins, IPI, ICMS e ISS) em uma cobrança única (IVA). Cria o Cashback para devolver impostos a famílias de baixa renda e o Imposto Seletivo para produtos nocivos." 
    },
    { 
        id: 3, 
        title: "Taxação de Importações", 
        summary: "Imposto para compras internacionais (Shein/Shopee).", 
        fullText: "Dispõe sobre o tratamento tributário nas importações. Compras até US$ 50 pagam apenas ICMS (17%). Acima de US$ 50, paga-se 60% de imposto federal mais o ICMS estadual." 
    }
];

// 2. SISTEMA DE TEMA (DARK MODE)
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

// Verifica preferência salva ao carregar
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    const icon = document.getElementById('theme-icon');
    if(icon) icon.classList.replace('fa-moon', 'fa-sun');
}

// 3. SIMULAÇÃO DE GPS (UX)
function simulateGPS() {
    const toast = document.getElementById('gps-toast');
    if (toast) {
        toast.classList.remove('hidden');
        // Animação de saída após 4 segundos
        setTimeout(() => {
            toast.style.transition = "opacity 0.5s";
            toast.style.opacity = '0';
            setTimeout(() => toast.classList.add('hidden'), 500);
        }, 4000);
    }
}

// 4. NAVEGAÇÃO (SPA)
function navigateTo(viewName) {
    stopAudio(); // Para o áudio ao mudar de tela
    
    // Esconde todas as telas
    document.querySelectorAll('.view').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });

    // Mostra a tela alvo
    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        // Pequeno delay para animação CSS funcionar
        setTimeout(() => targetView.classList.add('active'), 10);
    }

    // Scroll para o topo
    window.scrollTo(0, 0);
}

// 5. SELEÇÃO DO PROJETO DE LEI
function selectPL(id) {
    const pl = PL_DATA.find(item => item.id === id);
    if (!pl) return;

    currentPL = pl;

    // Preenche dados na tela de detalhes
    document.getElementById('pl-title-display').innerText = pl.title;
    document.getElementById('pl-summary-display').innerText = pl.summary;

    // Reseta estados da tela de detalhes
    document.getElementById('ai-result').classList.add('hidden');
    document.getElementById('vote-section').classList.add('hidden');
    document.getElementById('tags-container').classList.add('hidden');
    document.getElementById('user-interest').value = "";
    
    navigateTo('details');
}

// 6. SISTEMA DE ÁUDIO
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
        // Começar a falar o texto gerado
        const text = document.getElementById('text-output').innerText;
        if (text) speak(text);
    }
}

function stopAudio() {
    synth.cancel();
    updatePlayButton(false);
}

function speak(text) {
    // Cancela qualquer fala anterior
    synth.cancel();

    utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR'; // Voz em Português Brasil
    utterance.rate = 1.1;     // Velocidade dinâmica
    
    // Eventos para controlar o ícone do botão
    utterance.onstart = () => updatePlayButton(true);
    utterance.onend = () => updatePlayButton(false);
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

// 7. SISTEMA DE VOTAÇÃO
function vote(type) {
    // Mostra as tags para justificar o voto
    const tagsContainer = document.getElementById('tags-container');
    tagsContainer.classList.remove('hidden');
    
    // Feedback visual simples
    const msg = type === 'up' ? "👍 Voto computado: Concordo!" : "👎 Voto computado: Discordo!";
    alert(msg);
}

// 8. INTEGRAÇÃO COM IA (BACKEND)
async function getAIExplanation() {
    const userInterest = document.getElementById('user-interest').value.trim();
    
    if (!currentPL || !userInterest) {
        alert("Por favor, digite um tema (ex: Futebol, Cozinha)!");
        return;
    }

    // Elementos UI
    const resultBox = document.getElementById('ai-result');
    const loader = document.getElementById('loader');
    const audioCard = document.getElementById('audio-card');
    const contentBox = document.getElementById('explanation-content');
    const textOutput = document.getElementById('text-output');
    const voteSection = document.getElementById('vote-section');

    // Reset UI antes de carregar
    stopAudio();
    resultBox.classList.remove('hidden');
    loader.classList.remove('hidden');
    audioCard.classList.add('hidden');
    contentBox.classList.add('hidden');
    voteSection.classList.add('hidden');

    try {
        // Chamada ao Backend Python
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pl_text: currentPL.fullText,
                user_interest: userInterest
            })
        });

        if (!response.ok) throw new Error('Erro no servidor');

        let data = await response.json();
        
        // Tratamento de erro se o JSON vier como string
        if (typeof data === 'string') {
            try { data = JSON.parse(data); } catch(e) { data = {explanation: data}; }
        }

        // Exibe o texto gerado
        textOutput.innerText = data.explanation;

        // Atualiza visualização final
        loader.classList.add('hidden');
        audioCard.classList.remove('hidden'); // Mostra Player
        contentBox.classList.remove('hidden'); // Mostra Texto
        voteSection.classList.remove('hidden'); // Mostra Votação

    } catch (error) {
        console.error(error);
        loader.classList.add('hidden');
        alert("Erro ao conectar com a IA. Verifique se o arquivo 'main.py' está rodando.");
    }
}

// INICIALIZAÇÃO DO APP
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('home');
    setTimeout(simulateGPS, 1000); // Dispara simulação de GPS após 1s
});