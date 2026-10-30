const Typography = {
    animate(elementId, text, options = {}) {
        const el = document.getElementById(elementId);
        if (!el) return;

        const words = text.split(' ');
        el.innerHTML = '';
        el.classList.add('animated-text');

        words.forEach((word, index) => {
            const span = document.createElement('span');
            span.innerText = word + ' ';
            span.className = 'animated-word';
            el.appendChild(span);

            setTimeout(() => {
                span.classList.add('show');
            }, (options.delay || 50) * index);
        });
    },

    fadeOut(elementId) {
        const el = document.getElementById(elementId);
        if (!el) return;
        const spans = el.querySelectorAll('.animated-word');
        spans.forEach((span, index) => {
            setTimeout(() => {
                span.classList.remove('show');
            }, 30 * index);
        });
    }
};
