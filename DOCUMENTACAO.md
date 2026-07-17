# 📋 Projeto Orizon — Documentação Completa de Desenvolvimento

> Este arquivo serve como um guia abrangente sobre como o projeto foi idealizado, desenvolvido, os desafios técnicos enfrentados e as respostas para eventuais questionamentos durante a entrevista técnica.

---

## 1. Visão Geral do Projeto
O **Orizon** é um gerenciador de tarefas (To-Do List) avançado, desenvolvido com uma arquitetura robusta unindo **Django REST Framework** (Back-end) e **React** (Front-end), conteinerizado via **Docker** e publicado na nuvem **AWS EC2** com **CI/CD** e **HTTPS/SSL** configurados.

* **Repositório:** [techcarlosandre/Orizon](https://github.com/techcarlosandre/Orizon)
* **Aplicação Online (AWS):** [https://orizon.techcarlos.com.br](https://orizon.techcarlos.com.br)
* **Status do CI/CD:** 100% Verde (passando em todos os linters, testes unitários, testes E2E e deploy automático)

---

## 2. Decisões de Design e Arquitetura

### 2.1 Back-end (Django REST Framework)
* **Autenticação:** Escolhemos **SimpleJWT** (JSON Web Tokens) com rotação de Refresh Tokens e blacklist. Isso garante que a autenticação seja *stateless*, leve e segura, adequada para aplicações SPA (Single Page Applications).
* **Estrutura Modular:** O backend foi dividido em três principais apps: `accounts` (usuários, cadastro, envio de e-mails), `tasks` (gerenciamento de tarefas) e `categories` (organização de categorias).
* **Segurança e 12-Factor App:** Configurações sensíveis (credenciais de e-mail, chaves de API, segredos de produção e conexões de banco de dados) foram desacopladas do código usando variáveis de ambiente e arquivos de configuração distintos para desenvolvimento (`development.py`) e produção (`production.py`).

### 2.2 Front-end (React + Vite)
* **Construção veloz com Vite:** Substituímos o antigo padrão CRA (Create React App) pelo **Vite**, que fornece um ambiente de desenvolvimento instantâneo (HMR) e tempos de build consideravelmente menores através de compilação nativa em ES Modules.
* **Layout Responsivo e UI Dinâmica:** Desenvolvemos um painel com um design escuro (Dark Mode) de alta qualidade estática, utilizando modais dinâmicos próprios em vez de alertas de navegador para manipulação de ações perigosas (exclusões ou alertas de IA).

### 2.3 Banco de Dados (PostgreSQL)
* Adotamos o **PostgreSQL 16** rodando sob um container Docker com persistência via Docker Volumes. O PostgreSQL é robusto, confiável e ideal para lidar com a concorrência e tipos de dados necessários ao Django.

---

## 3. Desafios Superados e Mudanças de Rota (Facilitação)

### 🚀 Desafio 1: Estouro de Memória (OOM - Out Of Memory) na AWS EC2
* **O Problema:** A máquina EC2 do tipo `t2.micro` possui apenas 1 GB de RAM. Durante o deploy automático, ao tentar compilar e empacotar a imagem Docker do Frontend (com build pesado do Node.js) no próprio servidor da AWS, a memória RAM se esgotava por completo. Isso travava o SSH (porta 22) e derrubava os containers de produção ativos.
* **A Rota que evitamos:** Poderíamos ter configurado arquivos Swap na EC2 ou feito upgrade de máquina (o que geraria custos adicionais na AWS).
* **Como Resolvemos (Melhor Rota):** Modificamos o fluxo de CI/CD no **GitHub Actions**. O build das imagens Docker agora ocorre integralmente nos runners do GitHub (que dispõem de 7 GB de RAM gratuitos). A imagem é exportada como um pacote compactado (`.tar.gz`), enviada para o servidor da AWS via protocolo seguro SCP e apenas importada (`docker load`) e reiniciada. O consumo de recursos no servidor caiu para menos de 10% durante o deploy.

### 🚀 Desafio 2: Lock do Git (`index.lock`) no Deploy Manual e Automático em Simultâneo
* **O Problema:** Em determinados momentos, o deploy feito pelo GitHub Actions e os deploys manuais de validação aconteciam no mesmo instante no servidor. Isso gerava um arquivo de bloqueio temporário do git (`.git/index.lock`), abortando execuções subsequentes.
* **Como Resolvemos:** Atualizamos o script do workflow de deploy para remover preventivamente o arquivo `index.lock` caso ele estivesse orfanado antes de atualizar a ramificação principal (`git fetch` / `git reset`).

---

## 4. Perguntas Potenciais em Entrevistas

### 💬 Perguntas do Recrutador (Foco em Resultados e Ajuste)
1. **P: Como você garantiu que o projeto cumpre todas as regras do teste?**
   * *R:* Montei uma matriz de acompanhamento interna para validar todos os critérios, desde o CRUD completo e filtros avançados em React até a cobertura robusta de testes (pytest no backend e Selenium no frontend), culminando no deploy automatizado em um ambiente AWS real.
2. **P: Por que o deploy na nuvem é relevante se o código funciona localmente?**
   * *R:* O deploy expõe a aplicação aos desafios reais do ambiente produtivo, tais como latência de rede, CORS, renovação automática de certificados SSL (HTTPS), conexões de banco de dados isoladas e limites físicos de memória da máquina.

### 💬 Perguntas do Líder Técnico (Foco em Código e Arquitetura)
1. **P: Como as tarefas compartilhadas foram estruturadas no banco de dados?**
   * *R:* Criamos uma tabela intermediária de compartilhamento (`TaskShare`) com chaves estrangeiras apontando para as tarefas e os usuários participantes, além de uma coluna de nível de permissão (leitura ou edição). Os endpoints filtram os registros para exibir tanto as tarefas próprias do usuário autenticado quanto as que foram explicitamente compartilhadas com ele.
2. **P: Por que você utilizou pytest em vez do unittest padrão do Django?**
   * *R:* O `pytest` oferece uma sintaxe mais limpa e moderna (uso de `assert` direto em vez de métodos `self.assertEqual`), fixtures poderosas e reutilizáveis, e fácil integração com ferramentas de medição de cobertura de código (como o `pytest-cov`, no qual atingimos 98% de cobertura).
3. **P: Como o frontend e o backend se comunicam sem sofrer com problemas de CORS in produção?**
   * *R:* Configuramos o servidor **Nginx** atuando como proxy reverso na EC2. Todas as requisições para a rota `/api/*` são capturadas pelo Nginx no domínio principal e direcionadas internamente para a rede Docker onde residem os containers do Django, eliminando a barreira de CORS entre domínios ou portas distintas.

---

# 📧 E-mail de Envio do Teste (Destaque para Cópia)

```text
Assunto: Teste Prático — Desenvolvedor Python (Back-end) - Carlos André

Olá, equipe da AdviceHealth,

Espero que estejam bem!

Finalizei o desenvolvimento do teste prático para a oportunidade de Desenvolvedor Python (Back-end) e gostaria de compartilhar os resultados obtidos.

O projeto foi batizado de Orizon e engloba uma arquitetura completa conectando uma SPA moderna em React a uma API robusta em Django REST Framework, totalmente integrada sob infraestrutura na nuvem AWS.

Seguem abaixo as principais informações para acesso e revisão:

🔗 Link do Repositório (Acesso Público):
https://github.com/techcarlosandre/Orizon

🌐 Aplicação Publicada e Online (Deploy na AWS):
https://orizon.techcarlos.com.br

---

💡 Resumo da Entrega e Tecnologias Empregadas:

1. Back-end (Django REST Framework):
   - CRUD completo de tarefas, categorias e compartilhamento de tarefas com controle de permissão (View/Edit).
   - Autenticação stateless via JSON Web Tokens (JWT) com rotação e blacklist de tokens.
   - Throttling (limite de requisições) para segurança das rotas da API.
   - Banco de dados robusto PostgreSQL 16.

2. Front-end (React + Vite):
   - Interface responsiva com Dark Mode moderno e modais dinâmicos.
   - Validações de segurança client-side e integração simplificada com o backend.

3. Qualidade de Código e Testes (100% automatizados no CI):
   - Testes unitários de backend com pytest atingindo ~98% de cobertura de código.
   - Testes de UI/E2E com Selenium (fluxo de ponta a ponta: cadastro, login, criação de tarefa e logout).
   - Linters aplicados no Frontend e Backend para garantir código limpo.

4. Infraestrutura e DevOps (CI/CD na AWS):
   - Todo o ecossistema é orquestrado via Docker e Docker Compose (com 2 réplicas do backend para balanceamento de carga).
   - Pipeline de CI/CD configurado no GitHub Actions. Toda alteração na branch principal 'main' passa pelos testes e faz o deploy automático na AWS.
   - Comunicação criptografada com HTTPS configurado via Nginx e certificado gratuito renovável do Let's Encrypt.

Instruções completas para execução local simplificada por meio do Docker Compose, documentação dos endpoints da API e guia dos testes estão presentes no arquivo README.md da raiz do repositório.

Fico inteiramente à disposição para esclarecer eventuais dúvidas ou participar de uma rodada de discussão técnica sobre as escolhas de arquitetura do projeto.

Atenciosamente,

Carlos André
E-mail: techcarlosandre@gmail.com
Telefone: (Seu Telefone aqui)
LinkedIn: (Seu LinkedIn aqui)
```
