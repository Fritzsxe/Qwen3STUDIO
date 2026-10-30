const EXPERIENCE = {
    state: {
        currentStep: 0,
        data: {
            speaker: null,
            text: '',
            model: '0.6b-customvoice'
        }
    },

    steps: [
        { id: 'intro', title: 'intro' },
        { id: 'voice', title: 'voice' },
        { id: 'text', title: 'text' },
        { id: 'generate', title: 'generate' },
        { id: 'result', title: 'result' }
    ],

    init() {
        const container = document.getElementById('exp-scene-container');
        if (!container) return console.error("Container de experiência não encontrado");

        // Listener para conclusão no modo Experience
        WS.on('JOB_COMPLETED', (msg) => {
            if (this.state.currentStep === 3) { // Se estiver na tela de geração
                this.state.lastResult = msg.result;
                this.nextStep();
            }
        });

        // Carrega estado anterior
        const saved = Persistence.load();
        if (saved.exp_step) this.state.currentStep = saved.exp_step;

        this.renderStep();
        this.bindLocalEvents();
    },

    renderStep() {
        const step = this.steps[this.state.currentStep];
        const container = document.getElementById('exp-scene-container');

        // Transição suave interna
        container.style.opacity = '0';

        setTimeout(() => {
            container.innerHTML = `
                <div class="exp-scene-wrapper">
                    <h1 id="exp-title"></h1>
                    <div id="exp-body" class="exp-body-content"></div>
                </div>
            `;

            const titleText = Microcopy.get(step.id);
            Typography.animate('exp-title', titleText);
            this.loadBodyContent(step.id);

            container.style.opacity = '1';
            Persistence.save({ exp_step: this.state.currentStep });
        }, 400);
    },

    async loadBodyContent(stepId) {
        const body = document.getElementById('exp-body');

        if (stepId === 'intro') {
            body.innerHTML = `
                <div class="intro-actions">
                    <button class="btn-titanium-large" onclick="EXPERIENCE.nextStep()">COMEÇAR JORNADA</button>
                </div>
            `;
        } else if (stepId === 'voice') {
            body.innerHTML = '<div id="exp-speaker-grid" class="speaker-grid"></div>';

            let speakers = ['aiden', 'dylan', 'serena', 'vivian', 'ryan', 'eric', 'ono_anna', 'sohee', 'uncle_fu'];
            try {
                const status = await API.getStatus();
                if (status.supported_speakers && status.supported_speakers.length > 0) {
                    speakers = status.supported_speakers;
                }
            } catch (e) {}

            const grid = document.getElementById('exp-speaker-grid');
            speakers.forEach(s => {
                const card = document.createElement('div');
                card.className = 's-card glass';
                card.innerHTML = `<h3>${s}</h3><p>Oficial Qwen3</p>`;
                card.onclick = () => {
                    this.state.data.speaker = s;
                    this.nextStep();
                };
                grid.appendChild(card);
            });
        } else if (stepId === 'text') {
            body.innerHTML = `
                <textarea id="exp-text-input" class="q-input" placeholder="O que devo dizer?"></textarea>
                <div style="margin-top:2rem">
                    <button class="btn-titanium-large" onclick="EXPERIENCE.startGeneration()">GERAR AGORA</button>
                </div>
            `;
            setTimeout(() => document.getElementById('exp-text-input').focus(), 1000);
        } else if (stepId === 'generate') {
            body.innerHTML = `
                <div class="generating-view">
                    <div class="pulse-ring"></div>
                    <div class="status-msg">SINTETIZANDO VOZ...</div>
                </div>
            `;
        } else if (stepId === 'result') {
            const res = this.state.lastResult;
            if (!res) { this.goToStep(0); return; }

            const filename = res.path.split(/[\\/]/).pop();
            body.innerHTML = `
                <div class="result-view glass" style="padding:3rem; border-radius:2rem">
                    <h2>ÁUDIO GERADO</h2>
                    <audio src="/api/audio/${filename}" controls autoplay style="width:400px; margin:2rem 0"></audio>
                    <div class="metrics-dashboard">
                        <div class="metric-tile"><span class="metric-lbl">Duração</span><span class="metric-val">${res.duration.toFixed(2)}s</span></div>
                        <div class="metric-tile"><span class="metric-lbl">Tempo</span><span class="metric-val">${res.generation_time.toFixed(2)}s</span></div>
                        <div class="metric-tile"><span class="metric-lbl">RTF</span><span class="metric-val">${res.rtf.toFixed(2)}</span></div>
                    </div>
                    <div style="margin-top:3rem">
                        <button class="btn-titanium" onclick="EXPERIENCE.goToStep(0)">NOVA GERAÇÃO</button>
                    </div>
                </div>
            `;
        }
    },

    nextStep() {
        if (this.state.currentStep < this.steps.length - 1) {
            this.state.currentStep++;
            this.renderStep();
        }
    },

    async startGeneration() {
        const text = document.getElementById('exp-text-input').value;
        if (!text) return;
        this.state.data.text = text;

        await API.generateCustom({
            model: this.state.data.model,
            text: text,
            speaker: this.state.data.speaker || 'aiden',
            dtype: 'float32'
        });

        this.nextStep();
    },

    bindLocalEvents() {
        document.getElementById('exp-back').onclick = () => {
            if (this.state.currentStep > 0) {
                this.state.currentStep--;
                this.renderStep();
            } else {
                APP.switchScene('mode-selection');
            }
        };
    }
};
