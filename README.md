# Qwen3STUDIO

Uma interface web intuitiva para o **Qwen3-TTS**, desenvolvida para tornar a síntese neural de voz acessível a todos, sem necessidade de conhecimentos em programação.

Basta iniciar o programa, abrir o navegador e começar a gerar áudio em poucos segundos.

> ⚠️ **Nota:** O Qwen3STUDIO continua em desenvolvimento. Embora suas funcionalidades principais estejam implementadas, alguns erros e problemas de compatibilidade ainda podem ocorrer dependendo do ambiente e do hardware utilizado.

## Funcionalidades

- **Interface sem programação:** Controle completo dos parâmetros do Qwen3-TTS por meio de um painel moderno e intuitivo no navegador.
- **Processamento em tempo real:** Desenvolvido com FastAPI, WebSockets e PyTorch para acompanhamento de tarefas e geração de áudio.
- **Múltiplos modos de interface:** Layouts Studio, Experience e Mobile para diferentes formas de utilização.
- **Local e privado:** A geração de áudio e a inferência dos modelos são executadas localmente na sua máquina. Nenhum servidor externo de inferência é necessário.
- **Múltiplos modos de geração:** Suporte aos fluxos Custom Voice, Voice Design e Voice Clone.
- **Gerenciamento de memória da GPU:** Monitoramento de VRAM, limpeza de memória e opções configuráveis de precisão numérica para diferentes configurações de hardware.
- **Gerenciamento de tarefas:** Processamento por fila, acompanhamento de tarefas, histórico de gerações e solicitações de cancelamento.
- **Acesso pela rede local:** Acesse a interface web por outros dispositivos conectados à mesma rede, incluindo smartphones e tablets.
- **Informações de conexão:** Exibição automática do endereço IP local no terminal durante a inicialização, facilitando a conexão de outros dispositivos.
- **QR Code:** Recurso para facilitar o acesso à interface por dispositivos móveis.
- **Interface de terminal:** Também disponibiliza uma interface de linha de comando independente para quem prefere interagir diretamente pelo terminal.

## Novidades da versão 1.1

A versão 1.1 traz melhorias na experiência de inicialização e no acesso ao Qwen3STUDIO por outros dispositivos.

### Acesso facilitado pela rede local

- Exibição automática do endereço IP local durante a inicialização do servidor.
- Endereço de conexão disponibilizado diretamente no terminal.
- Facilitação do acesso por smartphones, tablets e outros computadores.
- Melhor integração entre o servidor local e os dispositivos conectados à mesma rede.

A atualização simplifica o processo de conexão, eliminando a necessidade de descobrir manualmente o endereço IP do computador.

## Como funciona

O Qwen3STUDIO utiliza uma arquitetura modular que separa a interface do usuário, a comunicação com o servidor, o gerenciamento de tarefas e a inferência de inteligência artificial.

O sistema é dividido em quatro componentes principais:

### 1. Frontend (Interface Web)

O frontend é disponibilizado pelo diretório `static/` e executado diretamente no navegador do usuário.

Ele fornece a interface visual para configurar os parâmetros de geração, selecionar modelos, gerenciar operações e acessar os áudios gerados.

A comunicação com o backend acontece por meio de requisições HTTP à API e conexões WebSocket.

### 2. Servidor Principal (`main.py`)

A aplicação principal é desenvolvida com **FastAPI** e executada pelo **Uvicorn**.

Sua função é atuar como camada de comunicação entre o frontend e o sistema interno de processamento.

Suas responsabilidades incluem:

- Disponibilizar a interface web estática.
- Receber solicitações de geração.
- Fornecer endpoints para modelos, diagnósticos, status e histórico de gerações.
- Gerenciar conexões WebSocket.
- Enviar eventos e atualizações em tempo real aos clientes conectados.
- Disponibilizar acesso aos arquivos de áudio.
- Permitir acesso pela rede local.
- Detectar e exibir o endereço IP local durante a inicialização.
- Disponibilizar QR Codes para facilitar a conexão de outros dispositivos.

O servidor utiliza a porta `7860`.

### 3. Gerenciador de Execução (`runtime.py`)

A camada de runtime é responsável por gerenciar a execução das tarefas de geração.

Em vez de executar a inferência diretamente dentro das requisições da API, as solicitações são encaminhadas ao sistema de gerenciamento de tarefas.

Suas responsabilidades incluem:

- Criar e gerenciar tarefas de geração.
- Processar a fila de tarefas.
- Acompanhar o estado de cada tarefa.
- Gerenciar solicitações de cancelamento.
- Manter o histórico de gerações.
- Comunicar eventos de processamento ao servidor.

Essa separação permite que a interface continue responsiva enquanto a geração de áudio está sendo processada.

### 4. Backend Qwen3-TTS (`qwen3_tts_backend.py`)

Este é o núcleo de inferência do Qwen3STUDIO.

Ele gerencia a interação direta com os modelos Qwen3-TTS utilizando PyTorch.

Suas funcionalidades incluem:

- Carregamento e descarregamento de modelos.
- Detecção de modelos disponíveis e já baixados.
- Gerenciamento de downloads e cache local.
- Suporte a diferentes variantes de modelos.
- Geração Custom Voice.
- Geração Voice Design.
- Geração Voice Clone.
- Monitoramento e gerenciamento de memória da GPU.
- Configuração de precisão numérica de acordo com o hardware.
- Geração e gerenciamento de arquivos de áudio.

O backend também pode funcionar de maneira independente, por meio de sua própria interface de linha de comando (CLI).

## Arquitetura do sistema

O fluxo geral de comunicação funciona da seguinte maneira:

```text
             NAVEGADOR
                 |
                 |
          HTTP API / WebSocket
                 |
                 v
              main.py
          Servidor FastAPI
                 |
                 v
             runtime.py
      Gerenciador de tarefas
                 |
                 v
      qwen3_tts_backend.py
          Motor Qwen3-TTS
                 |
                 v
             PyTorch / GPU
                 |
                 v
          Áudio gerado
```

Cada componente possui uma responsabilidade específica, permitindo que o motor de inferência seja utilizado independentemente da interface web.

## Como iniciar o aplicativo

O Qwen3STUDIO oferece duas maneiras diferentes de interagir com o sistema.

### Interface Web (Recomendada)

Para iniciar a interface pelo navegador, execute:

```bash
python main.py
```

Após a inicialização do servidor, o endereço de acesso será exibido diretamente no terminal.

**Acesso pelo próprio computador:**

```text
http://localhost:7860
```

**Acesso por outros dispositivos na mesma rede:**

```text
http://IP-LOCAL-DO-COMPUTADOR:7860
```

O endereço IP local é detectado automaticamente e apresentado durante a inicialização, evitando que o usuário precise procurá-lo manualmente.

### Acessando pelo celular ou tablet

Para utilizar o Qwen3STUDIO em um dispositivo móvel:

1. Inicie o Qwen3STUDIO no computador.
2. Conecte o celular ou tablet à mesma rede Wi-Fi do computador.
3. Consulte o endereço IP exibido no terminal.
4. Abra o navegador do dispositivo móvel.
5. Digite o endereço de conexão apresentado pelo programa.

O acesso também pode ser facilitado pelo QR Code disponibilizado pela aplicação.

> **Importante:** O computador precisa permanecer ligado e com o servidor em execução durante a utilização. A conexão pode depender das configurações do firewall e da rede local.

### Interface de Terminal (CLI)

O backend de inferência também pode ser iniciado independentemente:

```bash
python qwen3_tts_backend.py
```

Isso inicia a interface de linha de comando, permitindo interagir diretamente com o motor de inferência por meio de comandos no terminal.

A CLI disponibiliza recursos de gerenciamento de modelos, diagnósticos, informações da GPU e comandos de geração.

## Processamento local e privacidade

O Qwen3STUDIO foi desenvolvido com foco em inferência local.

Os modelos são carregados e executados na própria máquina do usuário, utilizando os recursos disponíveis de CPU e GPU.

Os áudios gerados são armazenados localmente nos diretórios de saída da aplicação.

Uma conexão com a internet pode ser necessária para baixar os arquivos dos modelos ou as dependências durante a configuração inicial. Depois que os recursos necessários estiverem disponíveis localmente, a inferência não dependerá de um serviço externo de geração.

## Requisitos e considerações de hardware

O desempenho e a compatibilidade dependem das características do hardware, especialmente da quantidade de memória VRAM disponível.

Diferentes tamanhos de modelos e configurações de precisão possuem requisitos de recursos distintos.

Como orientação geral de hardware:

- **Modelos 0.6B:** recomendado 4 GB de VRAM.
- **Modelos 1.7B:** recomendado 8 GB de VRAM.

Esses valores são recomendações, não requisitos mínimos garantidos. O consumo real de memória e a compatibilidade podem variar conforme a GPU, a precisão utilizada, o ambiente de execução e os demais aplicativos em funcionamento.

## Estado do projeto

**Versão 1.1**

O Qwen3STUDIO conta com frontend web integrado, backend de inferência local, gerenciamento de tarefas por runtime, interface de terminal e suporte ao acesso por dispositivos conectados à rede local.

A versão 1.1 introduz melhorias na experiência de inicialização e facilita a conexão de dispositivos externos, tornando a utilização do sistema mais prática.

O projeto continua em evolução, com possibilidade de novas melhorias, otimizações e testes de compatibilidade em versões futuras.
