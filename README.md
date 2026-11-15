# SatAgro — Apoio à Decisão na Reforma do Canavial com Dados da NASA

**NASA Space Apps Challenge 2026**  
**Desafio:** *Field Shift: Adapting Farms with NASA Data*  
**Equipe:** *Latino Party*  
**Região-Piloto:** Sertãozinho (SP)  
**Cultura de Referência:** Cana-de-açúcar (janela de reforma do canavial)

---

## 🌾 Visão Geral

O **SatAgro** é um protótipo web de apoio à decisão agronômica que traduz dados climatológicos abertos da NASA em **diagnósticos regionais transparentes**, **sinais climatológicos exploratórios** e **ordenação heurística multicritério (MCDA)** para a janela de reforma do canavial.

O projeto foi submetido a auditoria técnica independente e estruturado sob rigorosos princípios de **integridade científica e transparência**:
1. **Dados Reais da NASA POWER (v2.10.1):** Extraídos do modelo NASA GMAO MERRA-2 (Precipitação `PRECTOTCORR`, Temperaturas `T2M`/`T2M_MAX`/`T2M_MIN` e Umidade `RH2M`).
2. **Validação Estrita de Dados (P0.3):** Rejeição ativa de valores sentinela (`-999.0`), valores não-finitos ou meses ausentes, sem preenchimento arbitrário com zeros.
3. **Proveniência Autêntica (P0.4):** Extração dinâmica de metadados diretamente do cabeçalho da NASA (série real de 25 anos: 2001–2025; resolução meteorológica nativa de 0,5° × 0,625°).
4. **Honestidade Científica no Motor de Decisão (P0.1):** As notas das rotações são apresentadas estritamente como **avaliações heurísticas ilustrativas**, geradas pela ponderação multicritério dos pesos do produtor com notas conceituais da literatura (IAC, Embrapa, FAO 56), e não como modelo agronômico calibrado para o talhão.
5. **Sinais Climatológicos Exploratórios (P0.5):** Substituição de "alertas determinísticos de risco" por sinais históricos com advertências explícitas sobre o que eles *não* medem (ex.: não inferem erosão real sem declividade e solo, nem veranicos a partir de médias mensais).
6. **Fichas Agronômicas em 4 Camadas (P0.6):** Separação visual e conceitual entre:
   * *(1) Dados Observacionais NASA*
   * *(2) Indicadores Derivados SatAgro*
   * *(3) Literatura Técnica de Referência*
   * *(4) Avaliação Heurística Ilustrativa (MCDA)*
7. **Conjunto de Demonstração Verificado do Piloto (P0.7):** O arquivo `satagro/data/pilot_sertaozinho_verified.json` acompanha o repositório no Git, garantindo execução completa e confiável mesmo sem conexão externa.

---

## 🏛️ Arquitetura do Sistema

```text
NASA/
├── satagro/
│   ├── __init__.py
│   ├── data/
│   │   └── pilot_sertaozinho_verified.json # Conjunto autêntico pré-validado do piloto
│   ├── nasa_power.py          # Cliente HTTP NASA POWER, validação de sentinelas e proveniência
│   ├── indicators.py          # Indicadores climáticos verificáveis (chuva anual, sazonalidade, reforma)
│   ├── agronomic_data.py      # Biblioteca agronômica das estratégias de reforma com 4 camadas
│   ├── alerts.py              # Sinais climatológicos exploratórios com advertências e limitações
│   └── rotation_engine.py     # Motor de ordenação heurística multicritério (MCDA transparente)
├── tests/
│   ├── test_nasa_power.py     # Testes da API, cache e validação
│   ├── test_indicators.py     # Testes dos indicadores e sinais exploratórios
│   ├── test_engine.py         # Testes de ordenação e sensibilidade de pesos
│   ├── test_flow_integration.py # Teste ponta a ponta do fluxo completo
│   └── test_acceptance_codex.py # Bateria de 10 testes de aceitação da auditoria
├── .streamlit/
│   └── config.toml            # Identidade visual oficial (Azul #0B3D91 / #2E6FD8, Laranja #F57C00)
├── app.py                     # Interface Web responsiva em Streamlit
├── requirements.txt           # Dependências congeladas
└── README.md                  # Documentação técnica do projeto
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.11 ou 3.12 (recomendado)

### Passo 1: Acessar o Diretório do Projeto
```powershell
cd d:\NASA
```

### Passo 2: Ativar o Ambiente Virtual
No Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

### Passo 3: Executar a Aplicação Streamlit
```powershell
streamlit run app.py
```
A aplicação abrirá no navegador em `http://localhost:8501`.

> **Nota para demonstração sem rede:** Ao selecionar "Sertãozinho — SP", marque a opção *"Usar Demonstração Verificada do Piloto"* para carregar os dados autênticos empacotados, sem realizar chamadas externas à internet.

---

## 🧪 Execução dos Testes Automatizados

Para executar todos os 20 testes unitários e de integração (incluindo os 10 testes de aceitação da auditoria):

```powershell
python -m unittest discover -s tests
```

---

## 🔬 Delimitação de Escopo

### ✅ Efetivamente Disponível no MVP:
* Consulta e validação de dados da NASA POWER API v2.10.1 (GMAO MERRA-2).
* Rejeição automática de valores sentinela (`-999.0`) e dados incompletos.
* Conjunto de dados verificado do piloto de Sertãozinho empacotado no Git.
* Indicadores climatológicos regionais (chuva anual, sazonalidade seco/chuvoso e chuva na reforma).
* Sinais climatológicos exploratórios com limites e desmistificações expressas.
* Ponderação multicritério (MCDA) parametrizada pelas prioridades do produtor (1 a 5).
* Fichas explicativas estruturadas em 4 camadas independentes.

### 🔮 Planejado para Fases Futuras (Fase 2):
* Imagens de satélite de alta resolução (Sentinel-2 / Landsat 8/9 de 10–30 m) para vigor vegetal intra-talhão.
* Umidade do solo SMAP em alta resolução espacial.
* Topografia SRTM (~30 m) para modelagem física de declividade e erosão real.
* Focos de calor ativos via NASA FIRMS.
* Calibração com análises de solo locais e curvas fenológicas específicas.

---

## 📚 Referências Científicas e Técnicas
- **AMBROSANO, E. J. et al.** *Adubação verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronômico (IAC), Boletim Técnico.
- **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Práticas conservacionistas e fixação biológica de nitrogênio em cana-de-açúcar.*
- **DOORENBOS, J.; KASSAM, A. H.** *Yield response to water.* Rome: FAO, 1979. (FAO Irrigation and Drainage Paper, 33).
- **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.10.1).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
