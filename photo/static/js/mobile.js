const MOBILE = {
    state: {
        speakers: ['aiden', 'dylan', 'serena', 'vivian', 'ryan', 'eric', 'ono_anna', 'sohee', 'uncle_fu'],
        model: '0.6b-customvoice'
    },

    async init() {
        console.log("Mobile Mode Loaded");

        try {
            const status = await API.getStatus();
            if (status.supported_speakers && status.supported_speakers.length > 0) {
                this.state.speakers = status.supported_speakers;
            }
        } catch (e) {}

        this.renderSpeakers();
        this.bindEvents();

        WS.on('JOB_COMPLETED', (msg) => {
            alert("Geração concluída! Reproduzindo...");
            const filename = msg.result.path.split(/[\\/]/).pop();
            const audio = new Audio(`/api/audio/${filename}`);
            audio.play();
        });
    },

    renderSpeakers() {
        const select = document.getElementById('m-speaker');
        if (!select) return;
        select.innerHTML = '';
        this.state.speakers.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s;
            opt.innerText = s.charAt(0).toUpperCase() + s.slice(1);
            select.appendChild(opt);
        });
    },

    bindEvents() {
        const btn = document.getElementById('btn-m-generate');
        if (btn) btn.onclick = () => this.generate();

        const back = document.querySelector('#scene-mobile .btn-back');
        if (back) back.onclick = () => APP.switchScene('mode-selection');
    },

    async generate() {
        const text = document.getElementById('m-text').value;
        const speaker = document.getElementById('m-speaker').value;

        if (!text) return alert("Digite algo.");

        try {
            const res = await API.generateCustom({
                model: this.state.model,
                text: text,
                speaker: speaker,
                dtype: 'float32'
            });
            console.log("Mobile job created:", res.job_id);
        } catch (e) {
            alert("Erro: " + e.message);
        }
    }
};
