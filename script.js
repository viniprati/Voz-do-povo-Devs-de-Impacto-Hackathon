/* ==========================================================================
   SCRIPT.JS - Lógica do Frontend "Voz do Povo" (Atualizado com PDFs)
   ========================================================================== */

const API_URL = ""; // Vercel usa caminho relativo (ou coloque o link do seu backend)

let currentPL = null;
let synth = window.speechSynthesis;
let utterance = null;
let currentVoteType = null;
let currentTextToSpeak = ""; 

// 1. DADOS DOS PROJETOS DE LEI (Atualizado com os 5 PDFs)
const PL_DATA = [
    { 
        id: 1, 
        title: "Proibição de Apologia ao Crime (SP)", 
        summary: "Veda shows financiados pela prefeitura que incentivem drogas ou crime.", 
        pdfUrl: "pdfs/pl_shows_sp.pdf", // Nome que renomeamos
        author: "Ver. Amanda Vettorazzo",
        email: "amanda@camara.sp.gov.br",
        fullText: `PROJETO DE LEI DA VEREADORA AMANDA VETTORAZZO. Proíbe a contratação de shows, artistas e eventos abertos ao público infantojuvenil que envolvam, no decorrer da apresentação, expressão de apologia ao crime organizado ou ao uso de drogas. Art. 1º- É direito de toda Criança e Adolescente se desenvolver com dignidade, livre da influência do uso de drogas e do crime organizado. Art. 5º - Fica proibida à Administração Pública Municipal contratar shows que envolvam apologia ao crime. Multa de 100% do valor do contrato em caso de descumprimento.`
    },
    { 
        id: 2, 
        title: "PL das Fake News (2630/2020)", 
        summary: "Lei de Liberdade, Responsabilidade e Transparência na Internet.", 
        pdfUrl: "pdfs/pl_fake_news.pdf", // Nome que renomeamos
        author: "Sen. Alessandro Vieira",
        email: "sen.alessandrovieira@senado.leg.br",
        fullText: `PROJETO DE LEI Nº 2630, DE 2020. Institui a Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet. Art. 1º Esta lei estabelece normas para redes sociais e serviços de mensageria privada. Objetivos: fortalecimento do processo democrático, combate à desinformação. Vedações: contas inautênticas (robôs), redes de disseminação artificial. Exige relatórios de transparência das plataformas e cria regras para moderação de conteúdo.`
    },
    { 
        id: 3, 
        title: "Protocolo Anti-Bullying", 
        summary: "Cria mecanismos de proteção psicológica nas escolas.", 
        pdfUrl: "pdfs/pl_bullying.pdf", // Nome que renomeamos
        author: "Dep. Gilvan Maximo",
        email: "dep.gilvanmaximo@camara.leg.br",
        fullText: `PROJETO DE LEI N.º 1.367, DE 2024. Cria o PROTOCOLO “BULLYING NÃO É BRINCADEIRA”. Obriga escolas a notificarem imediatamente a coordenação pedagógica sobre casos de violência física ou psicológica. Art. 4º Define deveres como: notificar pais presencialmente, notificar Conselho Tutelar em casos graves e criar banco de dados de ocorrências. Penaliza a omissão das escolas.`
    },
    { 
        id: 4, 
        title: "Proibição de Linguagem Neutra", 
        summary: "Veda o uso de 'todes/amigues' em escolas e concursos.", 
        pdfUrl: "pdfs/pl_linguagem.pdf", // Nome que renomeamos
        author: "Dep. Mauricio do Vôlei",
        email: "dep.mauriciodovolei@camara.leg.br",
        fullText: `PROJETO DE LEI N.º 2.080, DE 2024. Dispõe sobre a proibição do uso e do ensino da linguagem neutra nas instituições de ensino públicas e privadas. Art. 1º Fica proibido o uso e o ensino da linguagem neutra em todos os níveis educacionais. Art. 2º Entende-se por linguagem neutra qualquer alteração na norma culta para eliminar distinções de gênero. Prevê sanções aos servidores que descumprirem.`
    },
    { 
        id: 5, 
        title: "Atualização do Código Civil", 
        summary: "Reforma sobre direitos digitais, família e contratos.", 
        pdfUrl: "pdfs/pl_civil.pdf", // Nome que renomeamos
        author: "Sen. Rodrigo Pacheco",
        email: "sen.rodrigopacheco@senado.leg.br",
        fullText: `PROJETO DE LEI N° 4, DE 2025. Dispõe sobre a atualização da Lei nº 10.406 (Código Civil). Inovações principais: Reconhece direitos digitais e herança digital; Proteção jurídica especial aos animais como seres sencientes; Regras sobre Inteligência Artificial e criação de imagens de pessoas; Divórcio unilateral direto em cartório; Alteração no regime de bens e sucessões.`
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

// 5. SELEÇÃO DO PL (Atualizada para Linkar o PDF)
function selectPL(id) {
    const pl = PL_DATA.find(item => item.id === id);
    if (!pl) return;

    currentPL = pl;

    // Preenche Textos
    document.getElementById('pl-title-display').innerText = pl.title;
    document.getElementById('pl-summary-display').innerText = pl.summary;

    // --- ATUALIZAÇÃO: Configura o Botão de PDF ---
    const pdfBtn = document.getElementById('btn-view-pdf');
    if (pdfBtn) {
        if (pl.pdfUrl) {
            pdfBtn.href = pl.pdfUrl; // Coloca o link do arquivo
            pdfBtn.classList.remove('hidden'); // Mostra o botão
        } else {
            pdfBtn.classList.add('hidden'); // Esconde se não tiver
        }
    }
    // --------------------------------------------

    // Reseta estados anteriores
    document.getElementById('ai-result').classList.add('hidden');
    document.getElementById('vote-section').classList.add('hidden');
    document.getElementById('tags-container').classList.add('hidden');
    document.getElementById('user-interest').value = "";
    
    navigateTo('details');
}

// 6. LÓGICA DE ÁUDIO
function changeSpeed() {
    if (synth.speaking) {
        stopAudio();
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
        // Simulação de envio (se não tiver backend real rodando)
        console.log("Enviando feedback:", {
            pl: currentPL.title,
            voto: currentVoteType,
            motivo: reason
        });

        // Se tiver backend, descomente abaixo:
        /*
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
        */

        alert(`✅ Opinião registrada!\nMotivo: ${reason}`);
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
        // AQUI CHAMA SEU BACKEND PYTHON
        const response = await fetch('/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pl_text: currentPL.fullText, // Envia o texto do PDF que colocamos no topo
                user_interest: userInterest
            })
        });

        if (!response.ok) throw new Error('Erro no servidor');

        let data = await response.json();
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
        alert("Erro ao conectar com a IA. Verifique se o backend está rodando.");
    }
}

// 9. MANIPULAÇÃO DE ARQUIVO (Caso o usuário queira subir outro PDF)
function handleFileUpload() {
    const fileInput = document.getElementById('pdf-upload');
    const fileNameDisplay = document.getElementById('file-name');
    
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileNameDisplay.innerText = `Arquivo selecionado: ${file.name}`;
        fileNameDisplay.style.display = 'block';
        
        // Em um app real, aqui leríamos o PDF com PDF.js
        // Para o hackathon, apenas simulamos que o texto mudou
        alert("⚠️ Atenção: No modo demonstração, continuaremos usando o texto do PL selecionado.");
    }
}

// FUNÇÃO PARA ABRIR O SITE DE OBRAS
function openObrasSite() {
    window.open("https://obrasorg.vercel.app/", "_blank");
}

// INICIALIZAÇÃO
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('home');
    setTimeout(simulateGPS, 1000);
});