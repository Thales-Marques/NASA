# SatAgro — Apoio a Decisao na Reforma do Canavial com Dados da NASA

**NASA Space Apps Challenge 2026**  
**Desafio:** *Field Shift: Adapting Farms with NASA Data*  
**Equipe:** *Latino Party*  
**Regiao-Piloto:** Sertaozinho (SP)  
**Cultura de Referencia:** Cana-de-acucar (janela de reforma do canavial)

---

## Visao Geral

O **SatAgro** e um prototipo web de apoio a decisao agronomica que traduz dados climatologicos abertos da NASA em **diagnosticos regionais transparentes**, **sinais climatologicos exploratorios** e **ordenacao heuristica multicriterio (MCDA)** para a janela de reforma do canavial.

O projeto foi estruturado sob rigorosos principios de **integridade cientifica, sobriedade e transparencia**:
1. **Dados Reais da NASA POWER (v2.10.1):** Extraidos do modelo NASA GMAO MERRA-2 (Precipitacao `PRECTOTCORR`, Temperaturas `T2M`/`T2M_MAX`/`T2M_MIN` e Umidade `RH2M`).
2. **Validacao Estrita de Dados (P0.3):** Rejeicao ativa de valores sentinela (`-999.0`), valores nao-finitos ou meses ausentes, sem preenchimento arbitrario com zeros.
3. **Proveniencia Autentica (P0.4):** Extracao dinamica de metadados diretamente do cabecalho da NASA (serie real de 25 anos: 2001–2025; resolucao meteorologica nativa de 0,5° × 0,625°).
4. **Honestidade Cientifica no Motor de Decisao (P0.1):** As notas das rotacoes sao apresentadas estritamente como **avaliacoes heuristicas ilustrativas**, geradas pela ponderacao multicriterio dos pesos do produtor com notas conceituais da literatura (IAC, Embrapa, FAO 56), e nao como modelo agronomico calibrado para o talhao.
5. **Sinais Climatologicos Exploratorios (P0.5):** Substituicao de alertas deterministicos de risco por sinais historicos com advertencias explicitas sobre o que eles nao medem (nao inferem erosao real sem declividade e solo, nem veranicos a partir de medias mensais).
6. **Fichas Agronomicas em 4 Camadas (P0.6):** Separacao visual e conceitual entre:
   * *(1) Dados Observacionais NASA*
   * *(2) Indicadores Derivados SatAgro*
   * *(3) Literatura Tecnica de Referencia*
   * *(4) Avaliacao Heuristica Ilustrativa (MCDA)*
7. **Conjunto de Demonstracao Verificado do Piloto (P0.7):** O arquivo `satagro/data/pilot_sertaozinho_verified.json` acompanha o repositorio no Git, garantindo execucao completa e confiavel mesmo sem conexao externa.
8. **Interface Tecnica e Sobria:** Paleta azul e laranja oficial, sem emojis decorativos e sem estetica generica de IA.

---

## Arquitetura do Sistema

```text
NASA/
├── satagro/
│   ├── __init__.py
│   ├── data/
│   │   └── pilot_sertaozinho_verified.json # Conjunto autentico pre-validado do piloto
│   ├── nasa_power.py          # Cliente HTTP NASA POWER, validacao de sentinelas e proveniencia
│   ├── indicators.py          # Indicadores climaticos verificaveis (chuva anual, sazonalidade, reforma)
│   ├── agronomic_data.py      # Biblioteca agronomica das estrategias de reforma com 4 camadas
│   ├── alerts.py              # Sinais climatologicos exploratorios com advertencias e limitacoes
│   └── rotation_engine.py     # Motor de ordenacao heuristica multicriterio (MCDA transparente)
├── tests/
│   ├── test_nasa_power.py     # Testes da API, cache e validacao
│   ├── test_indicators.py     # Testes dos indicadores e sinais exploratorios
│   ├── test_engine.py         # Testes de ordenacao e sensibilidade de pesos
│   ├── test_flow_integration.py # Teste ponta a ponta do fluxo completo
│   └── test_acceptance_codex.py # Bateria de testes de aceitacao da auditoria
├── .streamlit/
│   └── config.toml            # Identidade visual oficial (Azul #0B3D91 / #2E6FD8, Laranja #F57C00)
├── app.py                     # Interface Web responsiva em Streamlit
├── requirements.txt           # Dependencias congeladas
└── README.md                  # Documentacao tecnica do projeto
```

---

## Como Executar Localmente

### Pre-requisitos
- Python 3.11 ou 3.12 (recomendado)

### Passo 1: Acessar o Diretorio do Projeto
```powershell
cd d:\NASA
```

### Passo 2: Ativar o Ambiente Virtual
No Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

### Passo 3: Executar a Aplicacao Streamlit
```powershell
streamlit run app.py
```
A aplicacao abrira no navegador em `http://localhost:8501`.

> **Nota para demonstracao offline:** No modo "Demonstracao (Piloto Sertaozinho - SP)", o sistema carrega os dados autenticos empacotados, sem realizar chamadas externas a internet. No modo "Consulta Online", a aplicacao realiza consultas reais a API da NASA para as coordenadas informadas.

---

## Execucao dos Testes Automatizados

Para executar os testes unitarios, de integracao e de aceitacao:

```powershell
python -m unittest discover -s tests
```

---

## Delimitacao de Escopo

### Efetivamente Disponivel no MVP:
* Consulta e validacao de dados da NASA POWER API v2.10.1 (GMAO MERRA-2).
* Rejeicao automatica de valores sentinela (`-999.0`) e dados incompletos.
* Conjunto de dados verificado do piloto de Sertaozinho empacotado no Git.
* Indicadores climatologicos regionais (chuva anual, sazonalidade seco/chuvoso e chuva na reforma).
* Sinais climatologicos exploratorios com limites e desmistificacoes expressas.
* Ponderacao multicriterio (MCDA) parametrizada pelas prioridades do produtor (1 a 5).
* Fichas explicativas estruturadas em 4 camadas independentes.
* Sincronizacao bidirecional de presets e coordenadas no modo online.
* Forcamento de consulta real a API da NASA ao clicar em "Consultar dados da NASA".

### Planejado para Fases Futuras (Fase 2):
* Imagens de satelite de alta resolucao (Sentinel-2 / Landsat 8/9 de 10–30 m) para vigor vegetal intra-talhao.
* Umidade do solo SMAP em alta resolucao espacial.
* Topografia SRTM (~30 m) para modelagem fisica de declividade e erosao real.
* Focos de calor ativos via NASA FIRMS.
* Calibracao com analises de solo locais e curvas fenologicas especificas.

---

## Referencias Cientificas e Tecnicas
- **AMBROSANO, E. J. et al.** *Adubacao verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronomico (IAC), Boletim Tecnico.
- **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Praticas conservacionistas e fixacao biologica de nitrogenio em cana-de-acucar.*
- **DOORENBOS, J.; KASSAM, A. H.** *Yield response to water.* Rome: FAO, 1979. (FAO Irrigation and Drainage Paper, 33).
- **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.10.1).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
