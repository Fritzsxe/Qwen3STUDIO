const APP = {
    state: {
        activeJobId: null,
        currentScene: 'splash'
    },

    async init() {
        // Inicializa WebSocket
        WS.connect();

        // Listeners Globais
        WS.on('*', (msg) => this.handleGlobalEvent(msg));

        // Início real do splash
        this.runSplashSequence();
    },

    bindEvents() {
        document.getElementById('btn-show-qr').onclick = async (e) => {
            e.stopPropagation();
            const container = document.getElementById('lan-qr-container');
            const img = document.getElementById('lan-qr');
            const urlEl = document.getElementById('lan-url');

            const info = await fetch('/api/lan-info').then(r => r.json());
            img.src = '/api/qr';
            urlEl.innerText = info.lan;
            container.classList.toggle('hidden');
        };
    },

    async runSplashSequence() {
        this.bindEvents();
        const logs = document.getElementById('init-logs');
        const addLog = (t) => {
            const div = document.createElement('div');
            div.innerText = `> ${t}`;
            logs.appendChild(div);
            logs.scrollTop = logs.scrollHeight;
        };

        await new Promise(r => setTimeout(r, 800));
        addLog("Detectando hardware...");

        try {
            const diag = await API.getDiagnostics();
            if (diag.model && diag.model.gpu) {
                addLog(`NVIDIA ${diag.model.gpu.name} detectada.`);
                addLog(`Arquitetura Turing pronta.`);
                document.getElementById('gpu-badge').innerText = diag.model.gpu.name;
            }
        } catch (e) {
            addLog("ERRO: Falha ao acessar diagnóstico.");
        }

        addLog("Sincronizando modelos locais...");
        const status = await API.getStatus();
        addLog(`Runtime v${status.version} conectado.`);

        await new Promise(r => setTimeout(r, 1200));

        // Determina para onde ir
        const saved = Persistence.load();
        const nextScene = (saved.scene && saved.scene !== 'splash') ? saved.scene : 'mode-selection';

        addLog(`Iniciando ${nextScene.toUpperCase()}...`);
        await new Promise(r => setTimeout(r, 500));

        this.switchScene(nextScene);
    },

    switchScene(sceneId) {
        console.log(`Mudando para cena: ${sceneId}`);
        const scenes = document.querySelectorAll('.scene');
        scenes.forEach(s => {
            s.classList.remove('active');
            s.style.display = 'none'; // Força desaparecimento físico
        });

        const target = document.getElementById(sceneId);
        if (target) {
            target.style.display = 'flex'; // Restaura display antes da classe active
            // Pequeno delay para permitir que o display:flex seja processado antes da animação de opacidade
            setTimeout(() => {
                target.classList.add('active');
            }, 50);
        } else {
            console.error(`ERRO CRÍTICO: Cena '${sceneId}' não encontrada no DOM.`);
            // Fallback para seleção de modo se o destino falhar
            if (sceneId !== 'mode-selection') this.switchScene('mode-selection');
            return;
        }

        this.state.currentScene = sceneId;
        Persistence.save({ scene: sceneId });

        if (sceneId === 'studio') STUDIO.init();
        if (sceneId === 'experience') EXPERIENCE.init();
        if (sceneId === 'mobile') MOBILE.init();
    },

    handleGlobalEvent(msg) {
        console.log("Global WS:", msg);

        if (msg.type === 'INIT_STATUS') {
            const diag = msg.data;
            if (diag.gpu) {
                const gpuBadge = document.getElementById('gpu-badge');
                const vramBadge = document.getElementById('vram-badge');

                if (gpuBadge) gpuBadge.innerText = diag.gpu.name || "N/A";
                if (vramBadge) {
                    const allocated = (diag.gpu.allocated_gb || 0).toFixed(1);
                    const total = (diag.gpu.total_gb || 0).toFixed(1);
                    vramBadge.innerText = `${allocated} / ${total} GB`;
                }
            }
        }

        // Atualiza UI baseada no Job
        if (msg.type === 'JOB_STARTED') {
            this.showJobStatus("INICIANDO...");
        } else if (msg.type === 'MODEL_LOAD_STARTED') {
            this.showJobStatus("CARREGANDO MODELO...");
        } else if (msg.type === 'GENERATION_STARTED') {
            this.showJobStatus("GERANDO ÁUDIO...");
        } else if (msg.type === 'JOB_COMPLETED') {
            this.hideJobStatus();
            if (this.state.currentScene === 'studio') STUDIO.updateHistory();
        }
    },

    showJobStatus(text) {
        const el = document.getElementById('s-active-job');
        if (el) {
            el.classList.remove('hidden');
            document.getElementById('job-status-text').innerText = text;
        }
    },

    hideJobStatus() {
        const el = document.getElementById('s-active-job');
        if (el) el.classList.add('hidden');
    }
};

// Vincula cliques iniciais
document.querySelectorAll('.mode-card').forEach(card => {
    card.onclick = () => {
        const mode = card.dataset.mode;
        APP.switchScene(mode);
    };
});

window.onload = () => APP.init();
