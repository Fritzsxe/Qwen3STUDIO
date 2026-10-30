/**
 * ==============================================================================
 * QWEN3STUDIO · PROTOTYPE ENGINE v3.2 PRO
 * Audio · Sinal · Movimento · Precisão · Editorial Motion Design
 * ==============================================================================
 */

// 1. BANCO EDITORIAL DE FRASES & CARTUCHOS
const PHRASE_BANK = {
    welcome: [
        "Encontre a voz certa para esta ideia.",
        "Dê personalidade ao seu silêncio.",
        "Qual timbre melhor define esta mensagem?",
        "A voz que materializa seu pensamento.",
        "Escolha como suas palavras devem soar."
    ],
    welcomeSub: [
        "Síntese neural local de alta fidelidade operando com resolução de 24 kHz e processamento FP32 on-device.",
        "Arquitetura neural Qwen3 operando com latência ultrabaixa para produções narrativas e corporativas.",
        "Explore nuances harmônicas e entonação natural sem envio de dados para servidores externos."
    ],
    cartridges: {
        narrativa: "A quietude da madrugada sempre revela detalhes que o dia apaga. O som da chuva nas janelas cria um ritmo próprio, quase hipnótico, conduzindo os pensamentos para lugares distantes.",
        documentario: "No coração da floresta temperada, os ciclos biológicos operam em uma escala de precisão milenar. Cada espécie desenvolveu sinais acústicos próprios para navegar e proteger seu ecossistema.",
        audiobook: "Ele fechou o livro vagarosamente, como se temesse interromper o destino dos personagens. Havia algo no último parágrafo que continuava ecoando em sua mente com insistência incomum.",
        comercial: "Engenharia de precisão acústica. Fidelidade absoluta de sinal. O Qwen3-TTS redefine o padrão de síntese vocal diretamente na sua máquina de trabalho.",
        tecnico: "Inicializando decodificação neural espectral. Buffer de 24000 Hertz alocado. Tensores Float32 processados com sucesso pelo motor local.",
        editorial: "A tipografia ganha voz quando o timbre respeita o ritmo do texto. A modulação de frequências transforma ideias abstratas em presença auditiva memorável.",
        podcast: "Sejam muito bem-vindos ao episódio de hoje. Vamos conversar sobre novas fronteiras no áudio generativo.",
        mensagem: "Olá! Deixo este recado para confirmar nossa reunião de alinhamento amanhã às dez da manhã.",
        poesia: "O tempo que corre nos ponteiros é o mesmo vento que desenha as dunas no deserto."
    }
};

// 2. BANCO DE VOZES OFICIAIS (DENSO & PROFISSIONAL)
const VOICES = [
    { id: 'vivian', name: 'Vivian', gender: 'Feminino', lang: 'Mandarim/Global', timbre: 'Clara, aveludada e narrativa contemplativa', freq: 440 },
    { id: 'aiden', name: 'Aiden', gender: 'Masculino', lang: 'Inglês/Global', timbre: 'Expressivo, dinâmico e equilibrado', freq: 220 },
    { id: 'dylan', name: 'Dylan', gender: 'Masculino', lang: 'Inglês/Global', timbre: 'Jovem, vibrante e dicção corporativa', freq: 240 },
    { id: 'serena', name: 'Serena', gender: 'Feminino', lang: 'Mandarim/Global', timbre: 'Doce, íntima e tom acolhedor', freq: 480 },
    { id: 'ryan', name: 'Ryan', gender: 'Masculino', lang: 'Inglês/Global', timbre: 'Caloroso, amigável e comunicação direta', freq: 200 },
    { id: 'eric', name: 'Eric', gender: 'Masculino', lang: 'Inglês/Global', timbre: 'Profundo, firme, presença de rádio & doc', freq: 175 },
    { id: 'ono_anna', name: 'Ono Anna', gender: 'Feminino', lang: 'Japonês/Global', timbre: 'Delicada, precisa e entonação melódica', freq: 520 },
    { id: 'sohee', name: 'Sohee', gender: 'Feminino', lang: 'Coreano/Global', timbre: 'Moderna, brilhante e ritmo articulado', freq: 490 },
    { id: 'uncle_fu', name: 'Uncle Fu', gender: 'Masculino', lang: 'Mandarim/Global', timbre: 'Maduro, rouco e peso cinematográfico', freq: 160 }
];

// 3. PAREDE DE IDIOMAS DO QWEN3
const LANGUAGES = [
    { code: 'PT', name: 'Português', sub: 'Brasil / Portugal', region: 'americas popular', apiName: 'Portuguese' },
    { code: 'EN', name: 'English', sub: 'Global / US / UK', region: 'americas europe popular', apiName: 'English' },
    { code: 'ZH', name: '中文 (Mandarin)', sub: 'Standard Chinese', region: 'asia popular', apiName: 'Chinese' },
    { code: 'ES', name: 'Español', sub: 'LatAm / Espanha', region: 'americas europe popular', apiName: 'Spanish' },
    { code: 'FR', name: 'Français', sub: 'França / Canadá', region: 'europe', apiName: 'French' },
    { code: 'DE', name: 'Deutsch', sub: 'Alemanha / Áustria', region: 'europe', apiName: 'German' },
    { code: 'JA', name: '日本語', sub: 'Tokyo Accent', region: 'asia', apiName: 'Japanese' },
    { code: 'KO', name: '한국어', sub: 'Seoul Standard', region: 'asia', apiName: 'Korean' },
    { code: 'IT', name: 'Italiano', sub: 'Standard Italian', region: 'europe', apiName: 'Italian' },
    { code: 'RU', name: 'Русский', sub: 'Standard Russian', region: 'europe', apiName: 'Russian' },
    { code: 'YUE', name: 'Cantonese', sub: 'Hong Kong / GD', region: 'asia', apiName: 'Cantonese' },
    { code: 'AR', name: 'العربية', sub: 'Modern Standard', region: 'asia', apiName: 'Arabic' }
];

// 4. BUFFER DE HISTÓRICO LOCAL E SINCRONIZAÇÃO SQLITE
let HISTORY_DATA = [
    { id: 'sample-1', voice: 'Vivian', text: 'A quietude da madrugada sempre revela detalhes que o dia apaga.', time: 'Recente', dur: '6.4s', format: 'WAV 24kHz', audioUrl: null },
    { id: 'sample-2', voice: 'Aiden', text: 'Engenharia de precisão acústica. Som de alta fidelidade.', time: 'Recente', dur: '4.8s', format: 'WAV 24kHz', audioUrl: null }
];

// 5. ESTADO CENTRAL DO SISTEMA
const state = {
    mode: 'experience',
    scene: 'splash',
    voice: VOICES[0], // Vivian
    language: LANGUAGES[0], // Português
    text: '',
    durationEstimate: 0,
    isPlaying: false,
    activeAudioNode: null,
    audioCtx: null,
    currentJobId: null,
    currentJobStatus: null,
    lastResult: null,
    lastAudioUrl: null,
    realAudio: null,
    activeModel: '0.6b-customvoice',
    backendOnline: false,
    timers: [],
    playbackTimerInterval: null,
    playbackSeconds: 0,
    totalPlaybackSeconds: 8.4
};

// 6. GERENCIADOR DE ÁUDIO SINTETIZADO (WEB AUDIO API LOCAL)
function getAudioContext() {
    if (!state.audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        state.audioCtx = new AudioContext();
    }
    if (state.audioCtx.state === 'suspended') {
        state.audioCtx.resume();
    }
    return state.audioCtx;
}

function playHarmonicTone(baseFreq, duration = 2.0, onEnded = null) {
    try {
        const ctx = getAudioContext();
        if (state.activeAudioNode) {
            try { state.activeAudioNode.stop(); } catch(e) {}
            state.activeAudioNode = null;
        }

        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        // Timbre harmônico suave com envelope ADSR
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(baseFreq, now);
        osc.frequency.exponentialRampToValueAtTime(baseFreq * 1.05, now + duration * 0.4);
        osc.frequency.exponentialRampToValueAtTime(baseFreq, now + duration);

        gain.gain.setValueAtTime(0.001, now);
        gain.gain.linearRampToValueAtTime(0.15, now + 0.08); // Attack
        gain.gain.exponentialRampToValueAtTime(0.08, now + duration * 0.6); // Decay
        gain.gain.linearRampToValueAtTime(0.0001, now + duration); // Release

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + duration);
        state.activeAudioNode = osc;

        osc.onended = () => {
            state.activeAudioNode = null;
            if (onEnded) onEnded();
        };
    } catch (err) {
        console.warn("WebAudio fallback:", err);
        if (onEnded) setTimeout(onEnded, duration * 1000);
    }
}

function getOrCreateRealAudio() {
    if (!state.realAudio) {
        state.realAudio = new Audio();
        state.realAudio.preload = 'auto';

        state.realAudio.addEventListener('timeupdate', () => {
            const curTime = state.realAudio.currentTime;
            const dur = state.realAudio.duration || state.totalPlaybackSeconds || 1;
            const percent = Math.min(100, Math.max(0, (curTime / dur) * 100));

            if (state.mode === 'experience' && state.scene === 'result') {
                state.playbackSeconds = curTime;
                updatePlayerTimeDisplay();
                const progBar = document.getElementById('waveform-progress');
                if (progBar) progBar.style.width = `${percent}%`;

                const bars = document.querySelectorAll('.w-bar');
                const activeBarIdx = Math.floor((percent / 100) * bars.length);
                bars.forEach((b, idx) => {
                    if (idx <= activeBarIdx) b.classList.add('played');
                    else b.classList.remove('played');
                });
            } else if (state.mode === 'studio') {
                const dockFill = document.getElementById('dock-waveform-fill');
                if (dockFill) dockFill.style.width = `${percent}%`;
            }
        });

        state.realAudio.addEventListener('ended', () => {
            stopAllAudio();
            if (state.mode === 'experience') {
                resetPlayerState();
            } else if (state.mode === 'studio') {
                const btn = document.getElementById('btn-dock-play');
                if (btn) btn.innerText = '▶';
                const dockFill = document.getElementById('dock-waveform-fill');
                if (dockFill) dockFill.style.width = '0%';
            } else if (state.mode === 'mobile') {
                const btn = document.getElementById('btn-mobile-play');
                if (btn) btn.innerText = '▶';
            }
        });

        state.realAudio.addEventListener('error', (err) => {
            console.warn("Elemento de áudio real:", err);
            stopAllAudio();
        });
    }
    return state.realAudio;
}

// 7. TIPOGRAFIA VIVA SUTIL (SEM RANDOMIZAR CAIXA NEM QUEBRAS ARTIFICIAIS)
function renderSubtleLivingText(elementId, text) {
    const container = document.getElementById(elementId);
    if (!container) return;

    container.innerHTML = '';
    const words = text.split(' ');

    words.forEach((word, wordIdx) => {
        const wordSpan = document.createElement('span');
        wordSpan.className = 'living-word';

        word.split('').forEach((char, charIdx) => {
            const charSpan = document.createElement('span');
            charSpan.className = 'living-char';
            charSpan.innerText = char;

            // Microvariação tipográfica puramente editorial (ênfase leve na primeira palavra chave)
            if (wordIdx === 0 && charIdx < 3) {
                charSpan.style.fontWeight = '800';
            } else if (wordIdx % 2 === 1) {
                charSpan.style.fontWeight = '500';
            } else {
                charSpan.style.fontWeight = '700';
            }

            wordSpan.appendChild(charSpan);

            // Entrada suave escalonada
            const delay = (wordIdx * 45) + (charIdx * 18);
            const timer = setTimeout(() => {
                charSpan.classList.add('settled');
            }, delay);
            state.timers.push(timer);
        });

        container.appendChild(wordSpan);
    });
}

// 8. NAVEGAÇÃO DE CENAS COM TRANSIÇÕES DASH
function navigateTo(sceneId) {
    const currentScene = document.querySelector('.scene.active');
    const targetScene = document.getElementById(`scene-${sceneId}`);
    if (!targetScene) return;

    // Limpeza rigorosa de timers da cena anterior
    state.timers.forEach(t => clearTimeout(t));
    state.timers = [];

    // Interrompe reprodução ativa se houver
    stopAllAudio();

    if (currentScene && currentScene !== targetScene) {
        currentScene.classList.add('dash-out');
        const outTimer = setTimeout(() => {
            currentScene.classList.remove('active', 'dash-out');
            currentScene.style.display = 'none';
            activateScene(targetScene, sceneId);
        }, 450);
        state.timers.push(outTimer);
    } else {
        activateScene(targetScene, sceneId);
    }
}

function activateScene(targetEl, sceneId) {
    targetEl.style.display = 'flex';
    targetEl.offsetHeight; // Força repaint
    targetEl.classList.add('active', 'dash-in');
    state.scene = sceneId;

    const inTimer = setTimeout(() => {
        targetEl.classList.remove('dash-in');
    }, 700);
    state.timers.push(inTimer);

    // Inicialização específica da cena
    setupSceneContent(sceneId);
}

function setupSceneContent(sceneId) {
    if (sceneId === 'welcome') {
        const randomHeadline = PHRASE_BANK.welcome[Math.floor(Math.random() * PHRASE_BANK.welcome.length)];
        const randomSub = PHRASE_BANK.welcomeSub[Math.floor(Math.random() * PHRASE_BANK.welcomeSub.length)];
        renderSubtleLivingText('welcome-title', randomHeadline);
        document.getElementById('welcome-subtitle').innerText = randomSub;
    } else if (sceneId === 'voice-gallery') {
        renderVoiceGallery();
    } else if (sceneId === 'language') {
        renderLanguageWall();
    } else if (sceneId === 'text-editor') {
        setupEditorScene();
    } else if (sceneId === 'generating') {
        runGeneratingCycle();
    } else if (sceneId === 'result') {
        setupResultScene();
    }
}

// 9. ALTERNÂNCIA DE MODOS (EXPERIENCE / STUDIO / MOBILE)
function switchMode(mode) {
    if (state.mode === mode) return;
    state.mode = mode;

    stopAllAudio();

    // Atualiza classes ativas nos contêineres de modo
    document.querySelectorAll('.mode-view').forEach(view => {
        view.classList.remove('active');
        view.style.display = 'none';
    });

    let targetView;
    if (mode === 'experience') targetView = document.getElementById('experience-container');
    else if (mode === 'studio') targetView = document.getElementById('studio-view');
    else if (mode === 'mobile') targetView = document.getElementById('mobile-view');

    if (targetView) {
        targetView.style.display = 'flex';
        targetView.offsetHeight;
        targetView.classList.add('active');
    }

    // Atualiza posição do indicador DASH na Pill
    updateNavIndicator(mode);

    // Inicialização do Modo
    if (mode === 'studio') {
        initStudioMode();
    } else if (mode === 'mobile') {
        initMobileMode();
    } else if (mode === 'experience') {
        if (state.scene === 'splash') {
            navigateTo('welcome');
        }
    }
}

function updateNavIndicator(mode) {
    const navItems = document.querySelectorAll('.nav-item');
    const indicator = document.getElementById('nav-indicator');
    if (!indicator) return;

    let activeBtn = null;
    navItems.forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
            activeBtn = btn;
        } else {
            btn.classList.remove('active');
        }
    });

    if (activeBtn) {
        indicator.style.left = `${activeBtn.offsetLeft}px`;
        indicator.style.width = `${activeBtn.offsetWidth}px`;
    }
}

// 10. RENDERIZAÇÃO DA GALERIA DE VOZES (ALTA DENSIDADE)
function renderVoiceGallery() {
    const grid = document.getElementById('voice-cards-grid');
    if (!grid) return;

    grid.innerHTML = '';
    VOICES.forEach(v => {
        const isSelected = v.id === state.voice.id;
        const card = document.createElement('div');
        card.className = `voice-pro-card ${isSelected ? 'selected' : ''}`;
        card.id = `v-card-${v.id}`;

        card.innerHTML = `
            <div class="voice-card-top">
                <div class="vc-name-group">
                    <span class="vc-name">${v.name}</span>
                    <span class="vc-tag">${v.gender} · ${v.lang}</span>
                </div>
                <span class="vc-selected-badge">ATIVO</span>
            </div>
            <p class="vc-descriptor">${v.timbre}</p>
            <div class="vc-footer">
                <div class="vc-mini-wave">
                    <span class="mini-bar"></span>
                    <span class="mini-bar"></span>
                    <span class="mini-bar"></span>
                    <span class="mini-bar"></span>
                    <span class="mini-bar"></span>
                </div>
                <button type="button" class="btn-card-preview" onclick="event.stopPropagation(); previewVoice('${v.id}')">
                    <span>▶</span>
                    <span>Ouvir</span>
                </button>
            </div>
        `;

        card.onclick = () => {
            selectVoice(v);
        };

        grid.appendChild(card);
    });

    document.getElementById('gallery-active-voice-name').innerText = state.voice.name;
}

function selectVoice(voice) {
    state.voice = voice;
    document.querySelectorAll('.voice-pro-card').forEach(c => c.classList.remove('selected'));
    const targetCard = document.getElementById(`v-card-${voice.id}`);
    if (targetCard) targetCard.classList.add('selected');

    document.getElementById('gallery-active-voice-name').innerText = voice.name;
    showToast(`Voz selecionada: ${voice.name} (${voice.gender})`);
}

function previewVoice(voiceId) {
    const voice = VOICES.find(v => v.id === voiceId);
    if (!voice) return;

    const card = document.getElementById(`v-card-${voiceId}`);
    if (card) card.classList.add('playing');

    playHarmonicTone(voice.freq, 2.2, () => {
        if (card) card.classList.remove('playing');
    });
}

// 11. RENDERIZAÇÃO DA PAREDE DE IDIOMAS
function renderLanguageWall(filter = 'all') {
    const grid = document.getElementById('language-wall-grid');
    if (!grid) return;

    grid.innerHTML = '';
    const filteredLangs = LANGUAGES.filter(l => {
        if (filter === 'all') return true;
        return l.region.includes(filter);
    });

    filteredLangs.forEach(l => {
        const isSelected = l.code === state.language.code;
        const item = document.createElement('div');
        item.className = `lang-pro-card ${isSelected ? 'selected' : ''}`;
        item.id = `lang-card-${l.code}`;

        item.innerHTML = `
            <div class="lang-code-badge">${l.code}</div>
            <div class="lang-info">
                <span class="lang-name">${l.name}</span>
                <span class="lang-sub">${l.sub}</span>
            </div>
        `;

        item.onclick = () => {
            selectLanguage(l);
        };

        grid.appendChild(item);
    });

    // Eventos dos chips de filtro
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.onclick = () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            renderLanguageWall(chip.dataset.filter);
        };
    });

    document.getElementById('lang-active-summary').innerText = `${state.language.name} (${state.language.sub})`;
}

function selectLanguage(lang) {
    state.language = lang;
    document.querySelectorAll('.lang-pro-card').forEach(c => c.classList.remove('selected'));
    const target = document.getElementById(`lang-card-${lang.code}`);
    if (target) target.classList.add('selected');

    document.getElementById('lang-active-summary').innerText = `${lang.name} (${lang.sub})`;
    showToast(`Idioma alterado para ${lang.name}`);
}

// 12. EDITOR INSTRUMENTAL
function setupEditorScene() {
    document.getElementById('exp-tag-voice').innerText = `🎙️ ${state.voice.name}`;
    document.getElementById('exp-tag-lang').innerText = `🌐 ${state.language.name}`;

    const textarea = document.getElementById('exp-textarea');
    if (textarea && !textarea.value) {
        textarea.value = PHRASE_BANK.cartridges.narrativa;
    }
    handleExpTextChange();
}

function handleExpTextChange() {
    const textarea = document.getElementById('exp-textarea');
    if (!textarea) return;

    const val = textarea.value;
    state.text = val;
    const charCount = val.length;
    document.getElementById('exp-chars-count').innerText = `${charCount} / 2000`;

    // Estimativa de duração (taxa média de 16 caracteres por segundo em fala natural)
    const dur = Math.max(1.2, (charCount / 16)).toFixed(1);
    state.durationEstimate = dur;
    document.getElementById('exp-dur-estimate').innerText = `≈ ${dur}s`;
}

function loadCartridge(type) {
    const phrase = PHRASE_BANK.cartridges[type] || PHRASE_BANK.cartridges.narrativa;
    const textarea = document.getElementById('exp-textarea');
    if (textarea) {
        textarea.value = phrase;
        handleExpTextChange();
        showToast(`Cartucho carregado: ${type.toUpperCase()}`);
    }
}

function clearExpEditor() {
    const textarea = document.getElementById('exp-textarea');
    if (textarea) {
        textarea.value = '';
        handleExpTextChange();
    }
}

// 13. FLUXO DE GERAÇÃO NEURAL (INTEGRAÇÃO REAL COM MOTOR QWEN3 & WEBSOCKET)
let activeJobPollInterval = null;

async function startGenerationFlow() {
    const text = document.getElementById('exp-textarea').value.trim();
    if (!text) {
        showToast("Por favor, digite um texto para sintetizar.");
        return;
    }
    state.text = text;
    navigateTo('generating');

    setupGeneratingSpectrum();
    updateGenUIProgress(5, "Iniciando comunicação com motor neural...", "ETAPA 1/3 · PREPARANDO REQUISIÇÃO", 1);

    try {
        const payload = {
            model: state.activeModel || "0.6b-customvoice",
            text: state.text,
            language: state.language.apiName || "Portuguese",
            speaker: state.voice.id,
            dtype: "float32"
        };
        const res = await API.generateCustom(payload);
        state.currentJobId = res.job_id;
        state.currentJobStatus = "QUEUED";
        updateGenUIProgress(15, `Job #${res.job_id.slice(0, 8)} registrado na fila local...`, "ETAPA 1/3 · ENFILEIRADO", 1);

        startJobWatchdog(res.job_id, 'experience');
    } catch (err) {
        console.error("Falha ao criar job:", err);
        updateGenUIProgress(0, `Erro de conexão: ${err.message}`, "ERRO · FALHA AO INICIAR", 1);
        showToast("Falha ao disparar síntese: " + (err.message || "Erro de rede"));
        setTimeout(() => {
            if (state.scene === 'generating') navigateTo('text-editor');
        }, 3000);
    }
}

async function cancelGenerationFlow() {
    if (activeJobPollInterval) {
        clearInterval(activeJobPollInterval);
        activeJobPollInterval = null;
    }
    const jobId = state.currentJobId;
    if (jobId) {
        try {
            await API.cancelJob(jobId);
            showToast("Solicitação de cancelamento enviada.");
        } catch(e) {
            console.warn("Cancel request error:", e);
        }
    }
    state.currentJobId = null;
    state.currentJobStatus = null;
    navigateTo('text-editor');
    showToast("Processamento interrompido.");
}

function setupGeneratingSpectrum() {
    const spectrum = document.getElementById('neural-spectrum');
    if (!spectrum) return;
    spectrum.innerHTML = '';
    for (let i = 0; i < 24; i++) {
        const bar = document.createElement('div');
        bar.className = 'spec-bar';
        bar.style.animationDelay = `${(i * 0.04).toFixed(2)}s`;
        bar.style.animationDuration = `${(0.6 + Math.random() * 0.5).toFixed(2)}s`;
        spectrum.appendChild(bar);
    }
}

function updateGenUIProgress(pct, statusText, badgeText, activeStep = 1) {
    const percentEl = document.getElementById('gen-big-percentage');
    const statusEl = document.getElementById('gen-detail-status');
    const badgeEl = document.getElementById('gen-phase-badge');
    const line1 = document.getElementById('step-line-1');
    const line2 = document.getElementById('step-line-2');
    const node2 = document.getElementById('step-node-2');
    const node3 = document.getElementById('step-node-3');

    if (percentEl) percentEl.innerText = `${Math.min(100, Math.max(0, Math.round(pct)))}%`;
    if (statusEl && statusText) statusEl.innerText = statusText;
    if (badgeEl && badgeText) badgeEl.innerText = badgeText;

    if (line1 && line2 && node2 && node3) {
        if (activeStep >= 2) {
            line1.classList.add('active');
            node2.classList.add('active');
        } else {
            line1.classList.remove('active');
            node2.classList.remove('active');
        }
        if (activeStep >= 3) {
            line2.classList.add('active');
            node3.classList.add('active');
        } else {
            line2.classList.remove('active');
            node3.classList.remove('active');
        }
    }
}

function handleJobStatusUpdate(job, context = 'experience') {
    if (!job) return;
    state.currentJobStatus = job.status;

    if (context === 'experience' && state.scene === 'generating') {
        switch (job.status) {
            case 'QUEUED':
                updateGenUIProgress(18, "Aguardando alocação de tensores no pipeline...", "ETAPA 1/3 · ENFILEIRADO", 1);
                break;
            case 'PROCESSING':
            case 'LOADING_MODEL':
                updateGenUIProgress(35, "Carregando pesos e tensores do modelo Qwen3...", "ETAPA 1/3 · CARREGANDO MODELO", 1);
                break;
            case 'GENERATING':
                updateGenUIProgress(65, "Inferência espectral neural e decodificação acústica...", "ETAPA 2/3 · MEL-SPECTROGRAM & INFERÊNCIA", 2);
                break;
            case 'COMPLETED':
                updateGenUIProgress(100, "Amostras PCM 24kHz sintetizadas com fidelidade absoluta.", "ETAPA 3/3 · SÍNTESE CONCLUÍDA", 3);
                onJobCompleted(job.result, context);
                break;
            case 'FAILED':
                updateGenUIProgress(0, `Falha na execução: ${job.error || 'Erro interno'}`, "FALHA NO MOTOR NEURAL", 1);
                showToast("Erro durante a síntese neural: " + (job.error || 'Erro'));
                setTimeout(() => { if (state.scene === 'generating') navigateTo('text-editor'); }, 3000);
                break;
            case 'CANCELLED':
                updateGenUIProgress(0, "Processamento cancelado.", "CANCELADO", 1);
                break;
        }
    } else if (context === 'studio') {
        if (job.status === 'COMPLETED') {
            onJobCompleted(job.result, context);
        } else if (job.status === 'FAILED') {
            const btn = document.querySelector('.btn-studio-generate');
            if (btn) btn.classList.remove('loading');
            showToast("Falha na síntese do Studio: " + (job.error || 'Erro'));
        }
    } else if (context === 'mobile') {
        if (job.status === 'COMPLETED') {
            onJobCompleted(job.result, context);
        } else if (job.status === 'FAILED') {
            showToast("Falha na síntese mobile: " + (job.error || 'Erro'));
        }
    }
}

function onJobCompleted(result, context = 'experience') {
    if (activeJobPollInterval) {
        clearInterval(activeJobPollInterval);
        activeJobPollInterval = null;
    }

    state.lastResult = result || {};
    const filename = result && result.path ? result.path.split(/[\\/]/).pop() : 'output_custom.wav';
    state.lastAudioUrl = API.getAudioUrl(filename);

    const dur = result && result.duration ? result.duration : parseFloat(state.durationEstimate) || 5.0;
    state.totalPlaybackSeconds = dur;
    state.durationEstimate = dur.toFixed(2);

    const audio = getOrCreateRealAudio();
    audio.src = state.lastAudioUrl;
    audio.load();

    fetchHistoryFromBackend();

    if (context === 'experience') {
        setTimeout(() => {
            if (state.scene === 'generating') {
                navigateTo('result');
            }
        }, 500);
    } else if (context === 'studio') {
        const btn = document.querySelector('.btn-studio-generate');
        if (btn) btn.classList.remove('loading');

        const dock = document.getElementById('studio-dock-player');
        if (dock) dock.classList.remove('hidden');

        const dockTitle = document.getElementById('dock-item-title');
        if (dockTitle) dockTitle.innerText = `Sinal gerado · ${state.voice.name}`;

        const dockSpecs = document.getElementById('dock-item-specs');
        const rtfStr = result && result.rtf ? result.rtf.toFixed(2) : '0.24';
        if (dockSpecs) dockSpecs.innerText = `Duração: ${dur.toFixed(1)}s · RTF: ${rtfStr}x · 24.0 kHz Lossless`;

        renderDockWaveform();
        showToast("Sinal de áudio pronto no Dock!");
    } else if (context === 'mobile') {
        const mv = document.getElementById('mobile-last-voice');
        if (mv) mv.innerText = `${state.voice.name} · 24kHz`;
        const ms = document.getElementById('mobile-last-sub');
        if (ms) ms.innerText = `Gerado agora · ${dur.toFixed(1)}s`;
        showToast("Áudio pronto para reprodução!");
    }
}

function startJobWatchdog(jobId, context) {
    if (activeJobPollInterval) clearInterval(activeJobPollInterval);

    activeJobPollInterval = setInterval(async () => {
        try {
            const job = await API.getJob(jobId);
            if (!job) return;
            handleJobStatusUpdate(job, context);
            if (job.status === 'COMPLETED' || job.status === 'FAILED' || job.status === 'CANCELLED') {
                clearInterval(activeJobPollInterval);
                activeJobPollInterval = null;
            }
        } catch (e) {
            console.warn("Watchdog poll:", e);
        }
    }, 1200);
}

function runGeneratingCycle() {
    setupGeneratingSpectrum();
    if (!state.currentJobId) {
        startGenerationFlow();
    }
}

// 14. CENA RESULTADO & MASTER PLAYER
function setupResultScene() {
    document.getElementById('res-voice-name').innerText = state.voice.name;
    document.getElementById('res-voice-lang').innerText = `${state.language.name} · 24.0 kHz`;

    const dur = state.lastResult && state.lastResult.duration ? state.lastResult.duration.toFixed(2) : (state.durationEstimate || '6.40');
    const rtf = state.lastResult && state.lastResult.rtf ? state.lastResult.rtf.toFixed(2) : '0.24';

    const durEl = document.getElementById('res-metric-dur');
    if (durEl) durEl.innerText = `${dur}s`;
    const rtfEl = document.getElementById('res-metric-rtf');
    if (rtfEl) rtfEl.innerText = `${rtf}x`;

    state.totalPlaybackSeconds = parseFloat(dur) || 8.4;

    renderWaveformBars();
    resetPlayerState();
}

function renderWaveformBars() {
    const container = document.getElementById('waveform-bars');
    if (!container) return;
    container.innerHTML = '';

    for (let i = 0; i < 60; i++) {
        const bar = document.createElement('div');
        bar.className = 'w-bar';
        const normalized = Math.sin((i / 60) * Math.PI);
        const randomFactor = 0.4 + Math.random() * 0.6;
        const heightPx = Math.max(6, Math.floor(normalized * 50 * randomFactor));
        bar.style.height = `${heightPx}px`;
        container.appendChild(bar);
    }
}

function resetPlayerState() {
    state.isPlaying = false;
    state.playbackSeconds = 0;
    updatePlayerTimeDisplay();
    const prog = document.getElementById('waveform-progress');
    if (prog) prog.style.width = '0%';
    const playIcon = document.getElementById('master-play-icon');
    if (playIcon) playIcon.innerText = '▶';
    document.querySelectorAll('.w-bar').forEach(b => b.classList.remove('played'));
    if (state.playbackTimerInterval) clearInterval(state.playbackTimerInterval);
}

function toggleMasterPlay() {
    if (state.isPlaying) {
        pauseMasterPlay();
    } else {
        startMasterPlay();
    }
}

function startMasterPlay() {
    state.isPlaying = true;
    const playIcon = document.getElementById('master-play-icon');
    if (playIcon) playIcon.innerText = '⏸';

    if (state.lastAudioUrl) {
        const audio = getOrCreateRealAudio();
        if (!audio.src || !audio.src.endsWith(state.lastAudioUrl)) {
            audio.src = state.lastAudioUrl;
        }
        audio.play().catch(err => {
            console.warn("Audio play blocked, fallback to tone:", err);
            playHarmonicTone(state.voice.freq, state.totalPlaybackSeconds - state.playbackSeconds, () => {
                pauseMasterPlay();
                resetPlayerState();
            });
        });
    } else {
        playHarmonicTone(state.voice.freq, state.totalPlaybackSeconds - state.playbackSeconds, () => {
            pauseMasterPlay();
            resetPlayerState();
        });
    }
}

function pauseMasterPlay() {
    state.isPlaying = false;
    const playIcon = document.getElementById('master-play-icon');
    if (playIcon) playIcon.innerText = '▶';

    if (state.realAudio) {
        try { state.realAudio.pause(); } catch(e) {}
    }
    if (state.activeAudioNode) {
        try { state.activeAudioNode.stop(); } catch(e) {}
        state.activeAudioNode = null;
    }
}

function updatePlayerTimeDisplay() {
    const curMin = Math.floor(state.playbackSeconds / 60).toString().padStart(2, '0');
    const curSec = Math.floor(state.playbackSeconds % 60).toString().padStart(2, '0');
    const totMin = Math.floor(state.totalPlaybackSeconds / 60).toString().padStart(2, '0');
    const totSec = Math.floor(state.totalPlaybackSeconds % 60).toString().padStart(2, '0');
    const timerEl = document.getElementById('res-player-timer');
    if (timerEl) timerEl.innerText = `${curMin}:${curSec} / ${totMin}:${totSec}`;
}

function seekWaveform(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));

    state.playbackSeconds = ratio * state.totalPlaybackSeconds;
    updatePlayerTimeDisplay();
    const prog = document.getElementById('waveform-progress');
    if (prog) prog.style.width = `${ratio * 100}%`;

    if (state.realAudio && !isNaN(state.realAudio.duration) && state.realAudio.duration > 0) {
        state.realAudio.currentTime = ratio * state.realAudio.duration;
    }

    if (state.isPlaying) {
        pauseMasterPlay();
        startMasterPlay();
    }
}

// 15. POPOVER DE EXPORTAÇÃO
function toggleExportPopover(e) {
    e.stopPropagation();
    const popover = document.getElementById('export-popover');
    if (popover) popover.classList.toggle('hidden');
}

async function triggerExport(format) {
    const popover = document.getElementById('export-popover');
    if (popover) popover.classList.add('hidden');

    const voiceName = state.voice ? state.voice.name : 'Qwen3';
    const langCode = state.language ? state.language.code : 'PT';
    const cleanBaseName = `${voiceName}_${langCode}_24kHz`;

    if (format === 'wav') {
        if (state.lastAudioUrl) {
            API.triggerDownload(state.lastAudioUrl, `${cleanBaseName}.wav`);
            showToast(`Download de áudio WAV iniciado (${cleanBaseName}.wav)`);
        } else {
            showToast("Nenhum áudio gerado para download.");
        }
        return;
    }

    if (format === 'mp3') {
        if (!state.lastResult || !state.lastResult.path) {
            showToast("Gere um áudio antes de converter para MP3.");
            return;
        }

        showToast("Iniciando transcodificação FFmpeg para MP3 192k...");

        try {
            const res = await API.convertMp3(state.lastResult.path);
            const convJobId = res.job_id;

            const pollMp3 = setInterval(async () => {
                try {
                    const job = await API.getJob(convJobId);
                    if (job.status === 'COMPLETED') {
                        clearInterval(pollMp3);
                        const mp3Path = job.result && job.result.mp3_path ? job.result.mp3_path : '';
                        const mp3Name = mp3Path.split(/[\\/]/).pop() || `${cleanBaseName}.mp3`;
                        const mp3Url = API.getAudioUrl(mp3Name);
                        API.triggerDownload(mp3Url, `${cleanBaseName}.mp3`);
                        showToast(`Download do MP3 concluído com sucesso!`);
                    } else if (job.status === 'FAILED') {
                        clearInterval(pollMp3);
                        showToast("Falha na conversão para MP3: " + (job.error || 'Erro FFmpeg'));
                    }
                } catch(e) {
                    clearInterval(pollMp3);
                    console.warn("Erro ao checar MP3:", e);
                }
            }, 800);
        } catch(err) {
            showToast("Erro ao requisitar conversão MP3: " + err.message);
        }
    }
}

window.addEventListener('click', (e) => {
    const popover = document.getElementById('export-popover');
    if (popover && !popover.classList.contains('hidden') && !e.target.closest('.export-popover-anchor')) {
        popover.classList.add('hidden');
    }
});

// 16. MODO STUDIO (WORKBENCH PRO)
function initStudioMode() {
    const select = document.getElementById('studio-voice-select');
    if (select) {
        select.innerHTML = '';
        VOICES.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.innerText = `${v.name} (${v.gender} · ${v.lang})`;
            if (v.id === state.voice.id) opt.selected = true;
            select.appendChild(opt);
        });
    }

    const textarea = document.getElementById('studio-pro-textarea');
    if (textarea && !textarea.value) {
        textarea.value = PHRASE_BANK.cartridges.editorial;
    }
    handleStudioTextChange();
    updateStudioActiveInfo();
}

function handleStudioVoiceChange() {
    const select = document.getElementById('studio-voice-select');
    const selectedVoice = VOICES.find(v => v.id === select.value);
    if (selectedVoice) {
        state.voice = selectedVoice;
        updateStudioActiveInfo();
    }
}

function updateStudioActiveInfo() {
    const info = document.getElementById('studio-active-info');
    if (info) info.innerText = `${state.voice.name} · Float32 · 24kHz · Rate ${document.getElementById('studio-rate-val').innerText}`;
}

function previewStudioVoice() {
    const icon = document.getElementById('studio-preview-icon');
    if (icon) icon.innerText = '⏸';

    playHarmonicTone(state.voice.freq, 2.0, () => {
        if (icon) icon.innerText = '▶';
    });
}

function handleStudioTextChange() {
    const textarea = document.getElementById('studio-pro-textarea');
    if (!textarea) return;

    const val = textarea.value;
    const len = val.length;
    document.getElementById('studio-chars-display').innerText = `${len} / 2000 chars`;
    const pct = Math.min(100, (len / 2000) * 100);
    document.getElementById('studio-meter-fill').style.width = `${pct}%`;
}

function loadStudioCartridge(type) {
    const phrase = PHRASE_BANK.cartridges[type] || PHRASE_BANK.cartridges.editorial;
    const textarea = document.getElementById('studio-pro-textarea');
    if (textarea) {
        textarea.value = phrase;
        handleStudioTextChange();
        showToast(`Cartucho studio: ${type.toUpperCase()}`);
    }
}

function clearStudioText() {
    const textarea = document.getElementById('studio-pro-textarea');
    if (textarea) {
        textarea.value = '';
        handleStudioTextChange();
    }
}

async function runStudioGeneration() {
    const textarea = document.getElementById('studio-pro-textarea');
    const text = textarea ? textarea.value.trim() : '';
    if (!text) {
        showToast("Insira um texto para sintetizar no Studio.");
        return;
    }

    const genBtn = document.querySelector('.btn-studio-generate');
    if (genBtn) genBtn.classList.add('loading');
    showToast("Disparando síntese no motor Studio...");

    try {
        const payload = {
            model: state.activeModel || "0.6b-customvoice",
            text: text,
            language: state.language.apiName || "Portuguese",
            speaker: state.voice.id,
            dtype: "float32"
        };
        const res = await API.generateCustom(payload);
        state.currentJobId = res.job_id;
        showToast("Processando síntese de alta precisão na GPU local...");
        startJobWatchdog(res.job_id, 'studio');
    } catch(err) {
        if (genBtn) genBtn.classList.remove('loading');
        showToast("Erro ao processar no Studio: " + err.message);
    }
}

function renderDockWaveform() {
    const container = document.getElementById('dock-waveform-bars');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < 36; i++) {
        const b = document.createElement('div');
        b.className = 'dock-w-bar';
        b.style.height = `${Math.floor(4 + Math.random() * 18)}px`;
        container.appendChild(b);
    }
}

let dockPlaying = false;
function toggleDockPlay() {
    dockPlaying = !dockPlaying;
    const btn = document.getElementById('btn-dock-play');
    if (btn) btn.innerText = dockPlaying ? '⏸' : '▶';

    if (dockPlaying) {
        if (state.lastAudioUrl) {
            const audio = getOrCreateRealAudio();
            if (!audio.src || !audio.src.endsWith(state.lastAudioUrl)) {
                audio.src = state.lastAudioUrl;
            }
            audio.play().catch(e => {
                console.warn("Dock audio fallback:", e);
                playHarmonicTone(state.voice.freq, 3.0, () => {
                    dockPlaying = false;
                    if (btn) btn.innerText = '▶';
                });
            });
        } else {
            playHarmonicTone(state.voice.freq, 3.0, () => {
                dockPlaying = false;
                if (btn) btn.innerText = '▶';
            });
        }
    } else {
        stopAllAudio();
        const dockFill = document.getElementById('dock-waveform-fill');
        if (dockFill) dockFill.style.width = '0%';
    }
}

function seekDockWaveform(e) {
    if (state.realAudio && !isNaN(state.realAudio.duration) && state.realAudio.duration > 0) {
        const rect = e.currentTarget.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        state.realAudio.currentTime = ratio * state.realAudio.duration;
        const dockFill = document.getElementById('dock-waveform-fill');
        if (dockFill) dockFill.style.width = `${ratio * 100}%`;
    }
    showToast("Posição de reprodução ajustada.");
}

function closeDockPlayer() {
    stopAllAudio();
    const dock = document.getElementById('studio-dock-player');
    if (dock) dock.classList.add('hidden');
}

// 17. MODO MOBILE (ADAPTAÇÃO DEDICADA)
function initMobileMode() {
    const carousel = document.getElementById('mobile-voice-carousel');
    if (!carousel) return;

    carousel.innerHTML = '';
    VOICES.forEach(v => {
        const chip = document.createElement('div');
        chip.className = `m-voice-chip ${v.id === state.voice.id ? 'active' : ''}`;
        chip.id = `m-chip-${v.id}`;
        chip.innerText = `${v.name} (${v.lang.split('/')[0]})`;

        chip.onclick = () => {
            state.voice = v;
            document.querySelectorAll('.m-voice-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            document.getElementById('mobile-last-voice').innerText = `${v.name} · 24kHz`;
            showToast(`Mobile: Voz ativa ${v.name}`);
        };

        carousel.appendChild(chip);
    });

    const textarea = document.getElementById('mobile-textarea');
    if (textarea && !textarea.value) {
        textarea.value = PHRASE_BANK.cartridges.podcast;
    }
    handleMobileTextChange();
}

function handleMobileTextChange() {
    const textarea = document.getElementById('mobile-textarea');
    if (!textarea) return;
    const len = textarea.value.length;
    document.getElementById('mobile-char-count').innerText = `${len} / 2000`;
    const dur = Math.max(1.0, (len / 16)).toFixed(1);
    document.getElementById('mobile-dur-est').innerText = `≈ ${dur}s`;
}

function loadMobileCartridge(type) {
    const phrase = PHRASE_BANK.cartridges[type] || PHRASE_BANK.cartridges.podcast;
    const textarea = document.getElementById('mobile-textarea');
    if (textarea) {
        textarea.value = phrase;
        handleMobileTextChange();
    }
}

let mobilePlaying = false;
function toggleMobilePlay() {
    mobilePlaying = !mobilePlaying;
    const btn = document.getElementById('btn-mobile-play');
    if (btn) btn.innerText = mobilePlaying ? '⏸' : '▶';

    if (mobilePlaying) {
        if (state.lastAudioUrl) {
            const audio = getOrCreateRealAudio();
            if (!audio.src || !audio.src.endsWith(state.lastAudioUrl)) {
                audio.src = state.lastAudioUrl;
            }
            audio.play().catch(e => {
                console.warn("Mobile audio play:", e);
                playHarmonicTone(state.voice.freq, 2.5, () => {
                    mobilePlaying = false;
                    if (btn) btn.innerText = '▶';
                });
            });
        } else {
            playHarmonicTone(state.voice.freq, 2.5, () => {
                mobilePlaying = false;
                if (btn) btn.innerText = '▶';
            });
        }
    } else {
        stopAllAudio();
    }
}

async function runMobileGeneration() {
    const textarea = document.getElementById('mobile-textarea');
    const text = textarea ? textarea.value.trim() : '';
    if (!text) {
        showToast("Digite um texto para sintetizar no Mobile.");
        return;
    }

    showToast("Síntese móvel iniciada...");
    try {
        const payload = {
            model: state.activeModel || "0.6b-customvoice",
            text: text,
            language: state.language.apiName || "Portuguese",
            speaker: state.voice.id,
            dtype: "float32"
        };
        const res = await API.generateCustom(payload);
        state.currentJobId = res.job_id;
        startJobWatchdog(res.job_id, 'mobile');
    } catch(err) {
        showToast("Erro na síntese móvel: " + err.message);
    }
}

// 18. DRAWER LATERAL DE HISTÓRICO CONECTADO AO SQLITE
async function fetchHistoryFromBackend() {
    try {
        const rows = await API.getHistory();
        if (Array.isArray(rows) && rows.length > 0) {
            HISTORY_DATA = rows.map((r, i) => {
                let params = {};
                let result = {};
                try { params = typeof r.params === 'string' ? JSON.parse(r.params) : (r.params || {}); } catch(e){}
                try { result = typeof r.result === 'string' ? JSON.parse(r.result) : (r.result || {}); } catch(e){}

                const dur = result.duration ? `${Number(result.duration).toFixed(1)}s` : 'N/A';
                const format = r.type === 'convert_mp3' ? 'MP3 192k' : 'WAV 24kHz';
                const audioPath = result.path || result.mp3_path || '';
                const filename = audioPath ? audioPath.split(/[\\/]/).pop() : '';
                const audioUrl = filename ? API.getAudioUrl(filename) : null;

                let timeStr = 'Recente';
                if (r.timestamp) {
                    const d = new Date(r.timestamp * 1000);
                    timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                }

                return {
                    id: r.id || `hist-${i}`,
                    voice: params.speaker ? (params.speaker.charAt(0).toUpperCase() + params.speaker.slice(1)) : 'Voz Neural',
                    voiceId: params.speaker || 'vivian',
                    text: params.text || 'Síntese concluída',
                    time: timeStr,
                    dur: dur,
                    format: format,
                    audioUrl: audioUrl,
                    raw: r
                };
            });
        }
        if (document.getElementById('history-drawer') && document.getElementById('history-drawer').classList.contains('active')) {
            renderHistoryList();
        }
    } catch(err) {
        console.warn("Falha ao sincronizar histórico com SQLite:", err);
    }
}

function toggleHistory(open) {
    const drawer = document.getElementById('history-drawer');
    const overlay = document.getElementById('history-overlay');
    if (!drawer || !overlay) return;

    if (open) {
        fetchHistoryFromBackend().then(() => renderHistoryList());
        overlay.classList.add('active');
        drawer.classList.add('active');
    } else {
        drawer.classList.remove('active');
        overlay.classList.remove('active');
    }
}

function renderHistoryList() {
    const container = document.getElementById('history-items-list');
    if (!container) return;

    container.innerHTML = '';
    if (HISTORY_DATA.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:var(--text-tertiary); font-size:0.8rem; margin-top:2rem;">Nenhuma síntese registrada no banco de dados.</p>';
        return;
    }

    HISTORY_DATA.slice(0, 10).forEach((item, idx) => {
        const card = document.createElement('div');
        card.className = 'history-card-item';
        card.innerHTML = `
            <div class="hci-header">
                <span class="hci-voice">${item.voice}</span>
                <span class="hci-time">${item.time}</span>
            </div>
            <p class="hci-snippet">${item.text}</p>
            <div class="hci-footer">
                <span>${item.dur} · ${item.format}</span>
                <button type="button" class="btn-sm btn-dash-ghost" onclick="event.stopPropagation(); replayHistoryItem(${idx})">▶ Ouvir</button>
            </div>
        `;

        card.onclick = () => {
            loadHistoryItem(item);
        };

        container.appendChild(card);
    });
}

function replayHistoryItem(idx) {
    const item = HISTORY_DATA[idx];
    if (!item) return;

    showToast(`Reproduzindo histórico: ${item.voice}`);
    if (item.audioUrl) {
        stopAllAudio();
        const audio = getOrCreateRealAudio();
        audio.src = item.audioUrl;
        audio.play().catch(e => {
            console.warn("History audio play fallback:", e);
            const voice = VOICES.find(v => v.name.toLowerCase() === item.voice.toLowerCase()) || VOICES[0];
            playHarmonicTone(voice.freq, 2.5);
        });
    } else {
        const voice = VOICES.find(v => v.name.toLowerCase() === item.voice.toLowerCase()) || VOICES[0];
        playHarmonicTone(voice.freq, 2.5);
    }
}

function loadHistoryItem(item) {
    toggleHistory(false);
    const voice = VOICES.find(v => v.id === item.voiceId || v.name.toLowerCase() === item.voice.toLowerCase());
    if (voice) selectVoice(voice);

    if (item.audioUrl) {
        state.lastAudioUrl = item.audioUrl;
        const audio = getOrCreateRealAudio();
        audio.src = item.audioUrl;
    }

    if (state.mode === 'experience') {
        const textarea = document.getElementById('exp-textarea');
        if (textarea) textarea.value = item.text;
        handleExpTextChange();
        navigateTo('text-editor');
    } else if (state.mode === 'studio') {
        const textarea = document.getElementById('studio-pro-textarea');
        if (textarea) textarea.value = item.text;
        handleStudioTextChange();
    } else if (state.mode === 'mobile') {
        const textarea = document.getElementById('mobile-textarea');
        if (textarea) textarea.value = item.text;
        handleMobileTextChange();
    }
    showToast(`Carregado do histórico: ${item.voice}`);
}

function clearHistorySimulation() {
    HISTORY_DATA = [];
    renderHistoryList();
    showToast("Visualização do buffer recente limpa.");
}

// 19. TOAST NOTIFICAÇÕES DISCRETAS
function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast-item';
    toast.innerHTML = `
        <span style="color:var(--accent-cyan)">◈</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 2600);
}

function stopAllAudio() {
    if (state.activeAudioNode) {
        try { state.activeAudioNode.stop(); } catch(e) {}
        state.activeAudioNode = null;
    }
    if (state.realAudio) {
        try { state.realAudio.pause(); } catch(e) {}
    }
    state.isPlaying = false;
    dockPlaying = false;
    mobilePlaying = false;
    if (state.playbackTimerInterval) clearInterval(state.playbackTimerInterval);
}

// 20. INICIALIZAÇÃO GERAL DO SISTEMA E WEBSOCKET
async function initBackendConnection() {
    try {
        const status = await API.getStatus();
        state.backendOnline = true;
        console.log("Backend status:", status);

        if (status.speakers && Array.isArray(status.speakers)) {
            status.speakers.forEach(spk => {
                const spkId = spk.toLowerCase();
                const existing = VOICES.find(v => v.id === spkId);
                if (!existing) {
                    VOICES.push({
                        id: spkId,
                        name: spk.charAt(0).toUpperCase() + spk.slice(1),
                        gender: 'Voz Neural',
                        lang: 'Global',
                        timbre: 'Timbre oficial Qwen3-TTS',
                        freq: 260
                    });
                }
            });
        }

        if (status.active_job) {
            state.currentJobId = status.active_job.id;
            state.currentJobStatus = status.active_job.status;
            if (status.active_job.status === 'GENERATING' || status.active_job.status === 'PROCESSING') {
                if (state.mode === 'experience') {
                    navigateTo('generating');
                    handleJobStatusUpdate(status.active_job, 'experience');
                    startJobWatchdog(status.active_job.id, 'experience');
                }
            }
        }

        fetchHistoryFromBackend();
    } catch(err) {
        console.warn("Backend não conectado no momento:", err.message);
        state.backendOnline = false;
    }
}

function setupWebSocketListeners() {
    WS.on('JOB_QUEUED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'QUEUED', id: data.job_id }, state.mode);
        }
    });

    WS.on('JOB_STARTED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'PROCESSING', id: data.job_id }, state.mode);
        }
    });

    WS.on('MODEL_LOAD_STARTED', (data) => {
        if (state.scene === 'generating') {
            updateGenUIProgress(30, "Carregando pesos neurais na memória GPU...", "ETAPA 1/3 · CARREGANDO MODELO", 1);
        }
    });

    WS.on('MODEL_LOADED', (data) => {
        if (state.scene === 'generating') {
            updateGenUIProgress(45, "Modelo neural pronto para inferência.", "ETAPA 1/3 · PESOS ALOCADOS", 1);
        }
    });

    WS.on('GENERATION_STARTED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'GENERATING', id: data.job_id }, state.mode);
        }
    });

    WS.on('BACKEND_EVENT', (data) => {
        if (state.scene === 'generating') {
            const pct = data.progress !== undefined ? Math.round(data.progress * 100) : null;
            const msg = data.message || "Processando tensores neurais...";
            let step = 1;
            let badge = "ETAPA 1/3 · ANÁLISE";
            if (pct >= 35 && pct < 80) {
                step = 2;
                badge = "ETAPA 2/3 · INFERÊNCIA NEURAL SPECTRAL";
            } else if (pct >= 80) {
                step = 3;
                badge = "ETAPA 3/3 · SÍNTESE VOCODER 24kHz";
            }
            if (pct !== null) {
                updateGenUIProgress(pct, msg, badge, step);
            }
        }
    });

    WS.on('JOB_COMPLETED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'COMPLETED', id: data.job_id, result: data.result }, state.mode);
        }
    });

    WS.on('JOB_FAILED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'FAILED', id: data.job_id, error: data.error }, state.mode);
        }
    });

    WS.on('JOB_CANCELLED', (data) => {
        if (data.job_id === state.currentJobId) {
            handleJobStatusUpdate({ status: 'CANCELLED', id: data.job_id }, state.mode);
        }
    });
}

window.addEventListener('DOMContentLoaded', () => {
    // Posiciona o indicador DASH inicial
    const activeNav = document.querySelector('.nav-item.active');
    const indicator = document.getElementById('nav-indicator');
    if (activeNav && indicator) {
        indicator.style.left = `${activeNav.offsetLeft}px`;
        indicator.style.width = `${activeNav.offsetWidth}px`;
    }

    // Inicializa comunicação WebSocket e backend
    setupWebSocketListeners();
    WS.connect();
    initBackendConnection();

    // Barra de progresso do Splash cinemático
    const splashProgress = document.getElementById('splash-progress');
    if (splashProgress) {
        setTimeout(() => {
            splashProgress.style.width = '100%';
        }, 100);
    }

    // Transição automática DASH do Splash para o Welcome após 2.2s
    setTimeout(() => {
        if (state.scene === 'splash' && state.mode === 'experience') {
            navigateTo('welcome');
        }
    }, 2200);
});

// Ajuste dinâmico de redimensionamento de janela
window.addEventListener('resize', () => {
    updateNavIndicator(state.mode);
});
