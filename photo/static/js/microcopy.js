const Microcopy = {
    phrases: {
        intro: [
            "O que vamos sintetizar hoje?",
            "Transforme seu texto em vida.",
            "Qual história vamos contar agora?",
            "A sua voz local está pronta."
        ],
        voice: [
            "Quem deve falar por você?",
            "Escolha a personalidade da voz.",
            "Qual timbre melhor define essa ideia?",
            "Dê um rosto à essa mensagem."
        ],
        text: [
            "E sobre o que vamos falar?",
            "Insira suas palavras aqui.",
            "A página em branco aguarda sua voz.",
            "O que o mundo deveria ouvir?"
        ]
        generate: [
            "Aguarde enquanto damos vida às palavras.",
            "Processando sua solicitação na GPU.",
            "Quase pronto...",
            "Sintetizando áudio localmente."
        ]
    },

    get(category) {
        const list = this.phrases[category] || ["O processamento continua..."];
        return list[Math.floor(Math.random() * list.length)];
    }
};
