# SatAgro — Apoio à Decisão na Reforma do Canavial com Dados da NASA

**NASA Space Apps Challenge 2026**  
**Desafio:** *Field Shift: Adapting Farms with NASA Data*  
**Equipe:** *Latino Party*  
**Região-Piloto:** Sertãozinho (SP)  
**Cultura de Referência:** Cana-de-açúcar (janela de reforma do canavial)

---

## 🌾 Visão Geral

O **SatAgro** é um sistema web de apoio à decisão agronômica que traduz dados de observação da Terra da NASA em **diagnósticos climáticos explicáveis**, **alertas de risco agroclimático** e **comparações multicritério de estratégias de rotação de culturas** para a reforma do canavial.

Diferente de sistemas com caixas-pretas ou estimativas genéricas, o SatAgro fundamenta cada indicador em:
1. **Dados reais da NASA POWER** (Precipitação `PRECTOTCORR`, Temperaturas `T2M`/`T2M_MAX`/`T2M_MIN`, Umidade `RH2M` e Radiação Solar `ALLSKY_SFC_SW_DWN`).
2. **Literatura agronômica de referência** (IAC, Embrapa Meio Ambiente, Embrapa Soja, FAO 56).
3. **Explicabilidade total**: explicitação da fonte, resolução espacial (~0.5°), incerteza e recomendação expressa de validação agronômica local.

---

## 🏛️ Arquitetura do Sistema

```text
NASA/
├── .cache/
│   └── nasa_power/            # Cache determinístico em JSON das consultas à NASA
├── .streamlit/
│   └── config.toml            # Configuração visual sóbria (paleta azul #0B3D91, #2E6FD8 e laranja #F57C00)
├── satagro/
│   ├── __init__.py
│   ├── nasa_power.py          # Cliente HTTP real com a API NASA POWER v2.0 e cache local
│   ├── indicators.py          # Cálculo de indicadores (chuva anual, sazonalidade, ET0, balanço hídrico)
│   ├── agronomic_data.py      # Biblioteca agronômica das estratégias de reforma e critérios
│   ├── alerts.py              # Diagnóstico de riscos (erosão, veranico, pragas, geada)
│   └── rotation_engine.py     # Motor de decisão multicritério (MCDA) e sensibilidade a cenários
├── tests/
│   ├── test_nasa_power.py     # Testes da API, cache e tratamento de falhas
│   ├── test_indicators.py     # Testes das equações agroclimáticas e alertas
│   ├── test_engine.py         # Testes de ordenação, pesos e sensibilidade
│   └── test_flow_integration.py # Teste pontual e ponta-a-ponta do fluxo completo
├── app.py                     # Interface Web responsiva em Streamlit
├── requirements.txt           # Dependências congeladas
└── README.md                  # Documentação do projeto
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.11 ou 3.12 (recomendado)
- Conexão com a internet para a primeira consulta à API da NASA (as consultas subsequentes são salvas no cache local).

### Passo 1: Clonar / Acessar o Diretório
```bash
cd d:\NASA
```

### Passo 2: Criar e Ativar o Ambiente Virtual
No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Passo 3: Instalar as Dependências
```powershell
pip install -r requirements.txt
```

### Passo 4: Executar a Aplicação Streamlit
```powershell
streamlit run app.py
```
A aplicação abrirá automaticamente no navegador em: `http://localhost:8501`.

---

## 🧪 Execução dos Testes Automatizados

O protótipo conta com 12 testes unitários e de integração cobrindo coleta, cache, cálculos de indicadores, geração de alertas e ordenação de estratégias:

```powershell
python -m unittest discover -s tests
```

---

## 📊 Estratégias de Reforma Comparadas

| Estratégia | Tipo | Ciclo | Destaques Agronômicos |
| :--- | :--- | :--- | :--- |
| **Prática Atual (Pousio Convencional)** | Linha de Base | 60–120 dias | Simplicidade operacional máxima; altíssimo risco de erosão (75% da chuva do ano cai no solo descoberto); zero receita. |
| **Cana + Soja (*Glycine max*)** | Grão Comercial | 95–115 dias | Fixação biológica de nitrogênio (40–70 kg N/ha residual); receita financeira na entressafra; sensível a veranicos. |
| **Cana + Crotalária (*C. spectabilis/juncea*)** | Adubo Verde | 70–90 dias | Máxima proteção do solo contra erosão; aporte de até 180 kg N/ha; supressão biológica de nematoides; sem renda direta. |
| **Cana + Amendoim (*Arachis hypogaea*)** | Oleaginosa | 120–130 dias | Vocação regional de Sertãozinho e Jaboticabal; altíssimo valor agregado por ha; arranquio mecânico exige atenção à erosão pós-colheita. |

---

## 🔬 Delimitação de Escopo

### ✅ Efetivamente Implementado no MVP:
- Integração real com API da NASA POWER (sem simulações arbitrárias).
- Cache determinístico local para garantir disponibilidade offline após o primeiro carregamento.
- Seleção de coordenadas livre via mapa e botões predefinidos (Sertãozinho-SP, Ribeirão Preto-SP, Piracicaba-SP, Rio Verde-GO).
- Indicadores climáticos verificáveis com unidades e equações documentadas.
- Diagnósticos de risco (erosão, veranico, pragas canavieiras, estresse térmico/geada).
- Motor de decisão multicritério ponderado pelas prioridades do agricultor (1 a 5).
- Controle deslizante de cenários climáticos (variação de precipitação e temperatura).
- Fichas padronizadas por estratégia (por que foi sugerida, evidências, benefícios, lacunas, riscos, confiança e revisão agronômica necessária).

### 🔮 Planejado para Fases Futuras (Fase 2):
- Integração de imagens Sentinel-2 / Landsat 8/9 (10–30m) para vigor vegetativo intra-talhão.
- Umidade do solo SMAP em alta resolução espacial.
- Modelo Digital de Elevação SRTM para análise microtopográfica de declividade.
- Focos de calor ativos via NASA FIRMS.
- Upload de arquivos GeoJSON/KML com limites exatos da fazenda.
- Previsões meteorológicas operacionais de curto prazo (7 a 15 dias).

---

## 📚 Referências Científicas
- **ALLEN, R. G. et al.** *Crop evapotranspiration: guidelines for computing crop water requirements.* Rome: FAO, 1998. (FAO Irrigation and Drainage Paper, 56).
- **AMBROSANO, E. J. et al.** *Adubação verde com leguminosas na reforma do canavial.* Campinas: Instituto Agronômico (IAC).
- **EMBRAPA MEIO AMBIENTE / EMBRAPA SOJA.** *Práticas conservacionistas e fixação biológica de nitrogênio em cana-de-açúcar.*
- **NASA POWER Project.** *Prediction Of Worldwide Energy Resources (v2.0).* NASA Langley Research Center. [power.larc.nasa.gov](https://power.larc.nasa.gov/).
