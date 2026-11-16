# 🚗 Monitor Mitsubishi ASX - Belo Horizonte e Região (MG)

Sistema automatizado de monitoramento contínuo para compra de **Mitsubishi ASX** seminova em Belo Horizonte e Região Metropolitana (MG), executado via **GitHub Actions** em intervalos periódicos e com notificações detalhadas via **Telegram**.

Inspirado e adaptado da arquitetura do [monitor-voos](https://github.com/davidsimonmarques/monitor-voos).

---

## 📌 Fontes Mapeadas

### 🌐 Portais Automotivos
1. **Seminovos BH** (`seminovos.com.br`)
2. **Webmotors** (`webmotors.com.br`)
3. **Mercado Livre Veículos** (`mercadolivre.com.br`)
4. **OLX** (`mg.olx.com.br` / DDD 31)
5. **iCarros** (`icarros.com.br`)
6. **Mobiauto** (`mobiauto.com.br`)

### 🏬 Lojas e Concessionárias Locais de BH e Região
1. [Lokamig Seminovos](https://www.seminovoslokamig.com.br/)
2. [Rota 66 BH](https://www.rota66bh.com.br/)
3. [Kavak Seminovos](https://www.kavak.com/br/seminovos)
4. [Compra e Venda Seu Carro](https://www.compraevendaseucarro.com.br/Veiculos)
5. [Carbig Seminovos](https://carbig.com/seminovos)
6. [Reicar BH](https://reicarbh.com.br/Veiculos)
7. [Tutti Veículos](https://www.tuttiveiculos.com.br/veiculos)
8. [Grande BH Veículos](https://grandebhveiculos.com.br/BuscarVeiculo)
9. [Portal Auto Shopping](https://www.portalautoshopping.com.br/buscar)
10. [WCar Veículos BH](https://wcarveiculosbh.com.br/BuscarVeiculo)
11. [Galaxy Motors MG](https://galaxymotorsmg.com.br/)

---

## 🎯 Regras de Negócio e Filtros

### 1. Filtros Eliminatórios Estritos
* **Modelo:** Mitsubishi ASX.
* **Ano/Modelo:** `>= 2014` (unidades anteriores são automaticamente descartadas).
* **Preço:** Teto rígido de **R$ 70.000,00** para unidades elegíveis principais.
* **Câmbio:** Automático / CVT obrigatório (descarte imediato de versões manuais).
* **Bancos:** Revestimento em **couro obrigatório** (confirmado na descrição e atributos).
* **Histórico de Procedência:** Descarte imediato de unidades com menção a **leilão**, **sinistro**, **recuperação**, batida ou perda total. Se não mencionado, é registrado explicitamente: *"Não informado no anúncio"*. Se houver certificação/selo (ex: Seminovos BH "Leilão Não"), registra como certificado.

### 2. Nota Ponderada (0.0 a 10.0)
Avalia de forma transparente o equilíbrio de mercado:
* **Preço (até 3.0 pts):** Pontuação escalonada conforme desconto em relação ao teto.
* **Quilometragem (até 2.5 pts):** Bonificação para baixa km proporcional aos anos de uso.
* **Ano/Modelo (até 1.5 pts):** Modelos mais recentes (2016-2020+) ganham pontuação progressiva.
* **Opcionais Reais Verificados (até 2.5 pts):**
  * ☀️ **Teto Solar Elétrico / Panorâmico (Skyview):** Item de altíssimo valor e diferencial na ASX (+0.8 pt).
  * 📷 **Câmera de ré:** (+0.4 pt).
  * 📺 **Central multimídia:** (+0.4 pt).
  * 📡 **Sensor de estacionamento traseiro:** (+0.3 pt).
  * ❄️ **Ar-condicionado (automático/digital):** (+0.2 pt).
  * ⛰️ **Tração 4x4 AWD:** (+0.3 pt).
* **Laudo Cautelar / Perícia (até 0.5 pt):** Bônus para laudo 100% aprovado.

### 3. Vendedor e Laudo Cautelar
* Identifica automaticamente se é **Loja/Revenda** ou **Particular**.
* Se for **Particular**, analisa o perfil/nome para indicar se é **Homem** ou **Mulher** (ex: *Particular (Homem - Carlos)*).
* Status do laudo cautelar informado com transparência em cada alerta.

### 4. Validação ao Vivo Obrigatória
* Antes de qualquer anúncio ser aprovado e notificado, o sistema **abre individualmente a página final** via requisição HTTP com impersonação de navegador real.
* Confirma que o anúncio está ativo (não foi vendido nem pausado), checa se o câmbio é automático, se tem bancos de couro e se atende aos critérios eliminatórios.
* **Proibido reutilizar links sem revalidação.**

### 5. Regra de Contraproposta (R$ 70k a R$ 80k)
* Se em uma varredura **não houver nenhuma nova ASX elegível até R$ 70.000**, o monitor declara isso com clareza na notificação.
* Em seguida, mapeia e lista as melhores unidades ativas entre **R$ 70.000,00 e R$ 80.000,00** para oportunidade de **contraproposta / negociação**.

---

## 📲 Formato das Notificações no Telegram

### Exemplo: Nova ASX Elegível (<= R$ 70k)
```
🔥 [NOVA ASX ELEGÍVEL] Mitsubishi ASX 2015
⭐ Nota Ponderada: 8.6 / 10.0
Preço R$ 68.900,00 (+2.2 pts) | Km 112.000 km (+1.8 pts) | Ano 2015 (+0.7 pts) | Opcionais: Teto Solar (+0.8), Multimídia (+0.4), Câmera Ré (+0.4), Sensor Estac. (+0.3) | Laudo Cautelar Aprovado (+0.5 pt)

💰 Preço: R$ 68.900,00
🛣️ Quilometragem: 112.000 km
🏷️ Versão: 2.0 16V 4x4 AWD Flex CVT
🎨 Cor: Prata
📍 Localização: Buritis (Belo Horizonte/MG)
⚙️ Câmbio: Automático (CVT) ✅
💺 Bancos: Couro ✅

Opcionais Verificados:
☀️ Teto Solar Elétrico/Panorâmico: SIM ✅
📷 Câmera de Ré: SIM ✅
📡 Sensor de Ré: SIM ✅
📺 Multimídia: SIM ✅
❄️ Ar-condicionado: SIM ✅
⛰️ Tração 4x4 AWD: SIM ✅

👤 Vendedor: Particular (Homem - Carlos)
📋 Laudo Cautelar: Aprovado 100% (Sem apontamentos)
🛡️ Histórico: Sem histórico de leilão ou sinistro
🏪 Origem: Seminovos BH

🔗 Link Direto (Validado ao vivo):
https://seminovos.com.br/mitsubishi-asx-2015-4986044
```

### Exemplo: Sem novas entradas <= R$ 70k (Contrapropostas)
```
📢 MONITOR MITSUBISHI ASX - BH E REGIÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━
ℹ️ Nenhuma nova entrada elegível até R$ 70.000,00 encontrada nesta varredura.
Todos os anúncios abaixo desse valor foram desqualificados por filtros eliminatórios (sem couro, câmbio manual, histórico negativo ou já notificados).

🎯 OPORTUNIDADES PARA CONTRAPROPOSTA (R$ 70k a R$ 80k):
Unidades ativas e validadas ao vivo recomendadas para negociação:

Opção #1 para Contraproposta:
🎯 [CONTRAPROPOSTA] Mitsubishi ASX 2016
⭐ Nota Ponderada: 8.2 / 10.0
💰 Preço: R$ 74.900,00
🛣️ Quilometragem: 104.000 km
📍 Localização: Contagem/MG
👤 Vendedor: Particular (Mulher - Juliana)
...
```

---

## 🚀 Como Configurar e Executar

### 1. Criar o Bot no Telegram
1. Abra o Telegram e converse com o [@BotFather](https://t.me/BotFather).
2. Digite `/newbot` e siga as instruções para criar o bot. Guarde o `TELEGRAM_BOT_TOKEN`.
3. Inicie uma conversa com seu novo bot clicando em **Start**.
4. Obtenha seu `TELEGRAM_CHAT_ID`:
   * Fale com o bot [@userinfobot](https://t.me/userinfobot) para ver seu Id numérico; ou
   * Acesse no navegador: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates` e localize o campo `"chat":{"id": 123456789}`.

### 2. Configurar os GitHub Secrets no Repositório
No seu repositório no GitHub:
1. Acesse **Settings** > **Secrets and variables** > **Actions**.
2. Clique em **New repository secret** e adicione:
   * `TELEGRAM_BOT_TOKEN`: Token gerado pelo @BotFather.
   * `TELEGRAM_CHAT_ID`: Seu ID numérico do Telegram.

### 3. Execução Automatizada (GitHub Actions)
O workflow em `.github/workflows/monitor.yml` está configurado para:
* Executar automaticamente a cada **3 horas** (`cron: '0 */3 * * *'`).
* Permitir disparo manual a qualquer momento via aba **Actions** > **Run workflow**.
* Gravar e comitar automaticamente o arquivo `data/seen_ads.json` para que anúncios já vistos não sejam reenviados repetidamente.

---

## 💻 Execução Local

```bash
# 1. Clonar repositório
git clone https://github.com/davidsimonmarques/monitor-asx.git
cd monitor-asx

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar arquivo de configuração
cp .env.example .env
# Preencha suas credenciais no .env

# 5. Executar os testes unitários
python -m unittest discover tests

# 6. Rodar o monitor
python main.py
```

---

## 🛠️ Estrutura do Código

```
monitor-asx/
├── .github/
│   └── workflows/
│       └── monitor.yml        # Automação periódica no GitHub Actions
├── config.py                  # Parâmetros de busca, filtros e constantes
├── scoring.py                 # Algoritmo de nota 0-10, gênero do vendedor e laudo
├── validator.py               # Validação ao vivo obrigatória (abre página por página)
├── storage.py                 # Persistência de anúncios vistos (seen_ads.json)
├── notifier.py                # Formatação e envio de mensagens para o Telegram
├── scrapers/
│   ├── base.py                # Scraper base com impersonação de navegador real
│   ├── olx.py                 # Scraper OLX BH & Região
│   ├── seminovosbh.py         # Scraper Seminovos BH
│   ├── mercadolivre.py        # Scraper Mercado Livre Veículos
│   ├── webmotors.py           # Scraper Webmotors
│   ├── icarros.py             # Scraper iCarros
│   ├── mobiauto.py            # Scraper Mobiauto
│   └── local_dealers.py       # Scraper para as 11 lojas locais de BH
├── tests/
│   ├── test_scoring.py        # Testes de pontuação e identificação de vendedor
│   └── test_validator.py      # Testes de validação ao vivo e filtros eliminatórios
├── main.py                    # Orquestrador principal do pipeline
├── requirements.txt           # Dependências Python
├── .env.example               # Modelo de variáveis de ambiente
└── README.md                  # Documentação do projeto
```
