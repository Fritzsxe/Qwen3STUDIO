const STUDIO = {
    state: {
        models: [],
        currentModel: null,
        speakers: [],
        selectedSpeaker: null,
        text: ''
    },

    async init() {
        // Registra listener de conclusão de job via WS
        WS.on('JOB_COMPLETED', (msg) => {
            console.log("Job concluído recebido no Studio:", msg);
            this.showResult(msg.result);
            this.updateHistory();
        });

        WS.on('INIT_STATUS', (msg) => {
            this.updateSpeakers(msg.data.supported_speakers);
        });

        // Carrega estado persistido
        const saved = Persistence.load();
        this.state.text = saved.text || '';
        this.state.selectedSpeaker = saved.speaker || null;

        const inputEl = document.getElementById('s-text-input');
        if (inputEl) inputEl.value = this.state.text;

        await this.syncWithBackend();
        this.bindEvents();
        this.updateHistory();
    },

    async syncWithBackend() {
        try {
            const status = await API.getStatus();
            this.state.models = await API.listModels();

            this.renderModels();

            if (status.model_key) {
                document.getElementById('s-model-select').value = status.model_key;
                this.updateSpeakers(status.supported_speakers);
            } else {
                // Tenta carregar speakers do modelo selecionado no combo se ele estiver baixado
                this.updateSpeakers(status.supported_speakers || []);
            }

            // Update badges
            if (status.gpu) {
                document.getElementById('gpu-badge').innerText = status.gpu.name || "N/A";
                document.getElementById('vram-badge').innerText = `${(status.gpu.allocated_gb || 0).toFixed(1)} / ${(status.gpu.total_gb || 4).toFixed(1)} GB`;
            }
        } catch (e) {
            console.error("Erro ao sincronizar com backend:", e);
        }
    },

    renderModels() {
        const select = document.getElementById('s-model-select');
        if (!select) return;
        select.innerHTML = '';
        this.state.models.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.key;
            opt.innerText = m.name + (m.downloaded ? "" : " (⬇️)");
            select.appendChild(opt);
        });
    },

    updateSpeakers(speakers) {
        const grid = document.getElementById('s-speaker-grid');
        if (!grid) return;
        grid.innerHTML = '';

        // Fallback se não houver speakers (modelo não carregado)
        const displaySpeakers = (speakers && speakers.length > 0) ? speakers : ['aiden', 'dylan', 'eric', 'ono_anna', 'ryan', 'serena', 'sohee', 'uncle_fu', 'vivian'];

        displaySpeakers.forEach(s => {
            const card = document.createElement('div');
            card.className = 's-card glass';
            if (this.state.selectedSpeaker === s) card.classList.add('selected');
            card.innerText = s;
            card.onclick = () => {
                document.querySelectorAll('.s-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                this.state.selectedSpeaker = s;
                Persistence.save({ speaker: s });
            };
            grid.appendChild(card);
        });
    },

    async updateHistory() {
        try {
            const history = await API.getHistory();
            const container = document.getElementById('s-history-list');
            container.innerHTML = '';

            if (history.length === 0) {
                container.innerHTML = '<p style="font-size:0.7rem; opacity:0.5; text-align:center">Nenhuma geração ainda.</p>';
                return;
            }

            history.forEach(item => {
                try {
                    const div = document.createElement('div');
                    div.className = 'history-item glass';
                    const params = JSON.parse(item.params);
                    const result = JSON.parse(item.result);

                    div.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem">
                            <span class="tag">${params.speaker || 'Voice'}</span>
                            <span style="font-size: 0.6rem; opacity: 0.5">${new Date(item.timestamp * 1000).toLocaleTimeString()}</span>
                        </div>
                        <div style="font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity:0.8">
                            ${params.text}
                        </div>
                    `;
                    div.onclick = () => this.showResult(result);
                    container.appendChild(div);
                } catch (err) {
                    console.error("Erro ao processar item do histórico:", err);
                }
            });
        } catch (e) {
            console.error("Erro ao atualizar histórico:", e);
        }
    },

    bindEvents() {
        document.getElementById('s-text-input').oninput = (e) => {
            this.state.text = e.target.value;
            Persistence.save({ text: this.state.text });
        };

        document.getElementById('s-btn-generate').onclick = () => this.generate();
        document.getElementById('studio-back').onclick = () => APP.switchScene('mode-selection');

        document.getElementById('s-btn-convert').onclick = () => {
            if (this.lastResultPath) API.convertMp3(this.lastResultPath);
        };
    },

    async generate() {
        const data = {
            model: document.getElementById('s-model-select').value,
            text: this.state.text,
            speaker: this.state.selectedSpeaker || 'aiden',
            dtype: document.getElementById('s-dtype-select').value
        };

        if (!data.text) return alert("Por favor, digite um texto.");

        try {
            const res = await API.generateCustom(data);
            console.log("Job criado:", res.job_id);
            // O feedback visual virá via WebSocket (JOB_STARTED, etc)
        } catch (e) {
            alert("Erro ao solicitar geração: " + e.message);
        }
    },

    showResult(result) {
        if (!result || !result.path) return;

        this.lastResultPath = result.path;
        const view = document.getElementById('s-result-view');
        const metrics = document.getElementById('s-metrics');
        const player = document.getElementById('s-audio-player');

        view.classList.remove('hidden');

        // Extrai apenas o nome do arquivo para a rota da API
        const filename = result.path.split(/[\\/]/).pop();
        player.src = `/api/audio/${filename}`;
        player.play().catch(e => console.log("Auto-play bloqueado pelo navegador"));

        metrics.innerHTML = `
            <div class="metric-tile">
                <span class="metric-lbl">Duração</span>
                <span class="metric-val">${result.duration.toFixed(2)}s</span>
            </div>
            <div class="metric-tile">
                <span class="metric-lbl">Geração</span>
                <span class="metric-val">${result.generation_time.toFixed(2)}s</span>
            </div>
            <div class="metric-tile">
                <span class="metric-lbl">RTF</span>
                <span class="metric-val">${result.rtf.toFixed(2)}</span>
            </div>
            <div class="metric-tile">
                <span class="metric-lbl">Freq</span>
                <span class="metric-val">${(result.sample_rate/1000).toFixed(1)}k</span>
            </div>
        `;
    }
};
