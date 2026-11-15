"""
SatAgro - Base de Dados e Regras Agronômicas
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Biblioteca agronômica que parametriza as estratégias de reforma do canavial
com base em literatura de referência (IAC, Embrapa, CTC, FAO).
Todas as pontuações e regras são transparentes, documentadas e auditáveis.
"""

from __future__ import annotations

from typing import Any, Dict, List


CRITERIA_METADATA = {
    "protecao_solo": {
        "name": "Proteção do Solo e Erosão",
        "description": "Capacidade de cobrir o solo rapidamente durante o verão e dissipar a energia das gotas de chuva.",
        "scientific_basis": "Modelos USLE/RUSLE e boletins de conservação de solo do IAC/Embrapa.",
        "unit": "Índice normalizado (0 a 1)",
    },
    "fixacao_nitrogenio": {
        "name": "Fixação de N e Matéria Orgânica",
        "description": "Aporte de nitrogênio biológico (FBN) simbiótico e acúmulo de biomassa vegetal no perfil do solo.",
        "scientific_basis": "Pesquisas de adubação verde do IAC (Ambrosano et al.) e Embrapa Soja.",
        "unit": "Índice normalizado (0 a 1)",
    },
    "quebra_pragas": {
        "name": "Quebra de Ciclo de Pragas e Nematoides",
        "description": "Interrupção de hospedeiros de pragas da cana (broca, cigarrinha) e redução de populações de nematoides fitoparasitas.",
        "scientific_basis": "Literatura nematológica (Embrapa Agropecuária Oeste / IAC).",
        "unit": "Índice normalizado (0 a 1)",
    },
    "resiliencia_hidrica": {
        "name": "Resiliência Hídrica e a Veranicos",
        "description": "Tolerância a períodos curtos de estiagem (veranicos de janeiro) e eficiência no uso de água.",
        "scientific_basis": "Coeficientes de cultura (Kc) FAO 56 e Doorenbos & Kassam (1979).",
        "unit": "Índice normalizado (0 a 1)",
    },
    "renda_adicional": {
        "name": "Renda Direta na Janela de Reforma",
        "description": "Capacidade de gerar liquidez financeira direta pela comercialização da colheita antes da cana-planta.",
        "scientific_basis": "Mercado regional de grãos e oleaginosas do Estado de São Paulo.",
        "unit": "Índice normalizado (0 a 1)",
    },
    "simplicidade_operacional": {
        "name": "Simplicidade Operacional e Baixo Custo",
        "description": "Facilidade de manejo, menor dependência de maquinário especializado e menor custo inicial de implantação.",
        "scientific_basis": "Custos operacionais de reforma do canavial (PECEGE / Conab / IAC).",
        "unit": "Índice normalizado (0 a 1)",
    },
}


STRATEGIES_DATABASE: Dict[str, Dict[str, Any]] = {
    "atual": {
        "id": "atual",
        "name": "Prática Atual (Reforma Convencional / Pousio)",
        "crop_type": "Pousio / Solo Descoberto",
        "cycle_days": "60 a 120 dias",
        "scores": {
            "protecao_solo": 0.15,
            "fixacao_nitrogenio": 0.05,
            "quebra_pragas": 0.20,
            "resiliencia_hidrica": 0.40,
            "renda_adicional": 0.00,
            "simplicidade_operacional": 0.95,
        },
        "why_suggested": "Referência de comparação (linha de base da fazenda). Apresenta a máxima simplicidade operacional.",
        "evidence": "Prática histórica consolidada em áreas sem integração com grãos; dados climáticos NASA indicam 75% da chuva caindo no solo exposto.",
        "benefits": "Menor custo inicial com sementes e defensivos; ausência de operações de colheita ou dessecação intermediária.",
        "unknowns": "Teor inicial de matéria orgânica e histórico de compactação da área.",
        "risks": "Erosão laminar e em sulcos severa sob chuvas intensas de verão (perda de 20-40 t/ha de solo fértil); lixiviação de nutrientes.",
        "confidence": "Alta (impactos do solo exposto são amplamente documentados na ciência agronômica)",
        "specialist_review": "Agrônomo deve avaliar a declividade da área e implementar terraceamento imediato caso a reforma permaneça em pousio."
    },
    "soja": {
        "id": "soja",
        "name": "Cana + Soja (Glycine max)",
        "crop_type": "Grão Comercial Leguminoso",
        "cycle_days": "95 a 115 dias (cultivares precoces)",
        "scores": {
            "protecao_solo": 0.65,
            "fixacao_nitrogenio": 0.70,
            "quebra_pragas": 0.60,
            "resiliencia_hidrica": 0.55,
            "renda_adicional": 0.85,
            "simplicidade_operacional": 0.60,
        },
        "why_suggested": "Equilíbrio entre amortização financeira dos custos da reforma e enriquecimento biológico do solo com nitrogênio.",
        "evidence": "FBN documentada pela Embrapa Soja (residual de 40-70 kg N/ha para a cana-planta); cobertura foliar relevante após 40 DAE.",
        "benefits": "Receita em caixa na entressafra; redução da necessidade de adubação nitrogenada de fundação na cana; controle de plantas daninhas na dessecação.",
        "unknowns": "Níveis prévios de nematoides (espécies hospedeiras) e presença de maquinário de colheita na microrregião.",
        "risks": "Sensibilidade a veranicos durante o enchimento de grãos; risco de compactação do solo na colheita mecanizada em janeiro/fevereiro chuvoso.",
        "confidence": "Alta (rotação consagrada no interior de SP com ampla base empírica e comercial)",
        "specialist_review": "Validar escolha de cultivar de ciclo precoce compatível com a janela de plantio da cana e verificar tolerância a nematoides."
    },
    "crotalaria": {
        "id": "crotalaria",
        "name": "Cana + Crotalária (Crotalaria spectabilis / juncea)",
        "crop_type": "Adubo Verde / Cobertura de Solo",
        "cycle_days": "70 a 90 dias até florescimento/dessecação",
        "scores": {
            "protecao_solo": 0.95,
            "fixacao_nitrogenio": 0.95,
            "quebra_pragas": 0.90,
            "resiliencia_hidrica": 0.85,
            "renda_adicional": 0.10,
            "simplicidade_operacional": 0.75,
        },
        "why_suggested": "Máxima regeneração do solo, aporte abundante de biomassa orgânica e supressão natural de nematoides.",
        "evidence": "Estudos do IAC comprovam até 150-180 kg N/ha acumulados na biomassa e ação de planta-armadilha para Pratylenchus zeae e Meloidogyne.",
        "benefits": "Dissipação completa do impacto das gotas de chuva; retenção hídrica superior; redução drástica de nematoides; palhada durável para a cana-planta.",
        "unknowns": "Análise nematológica laboratorial para determinar se a espécie indicada é C. spectabilis ou C. juncea.",
        "risks": "Não gera renda líquida direta pela venda de produto colhido; requer dessecação/manejo rigoroso no início do florescimento para não lignificar.",
        "confidence": "Alta (amplamente respaldada por pesquisas da Embrapa e IAC sobre adubação verde)",
        "specialist_review": "Definir a espécie de crotalária de acordo com o histórico fitossanitário e calibrar data de manejo da biomassa com a equipe de plantio."
    },
    "amendoim": {
        "id": "amendoim",
        "name": "Cana + Amendoim (Arachis hypogaea)",
        "crop_type": "Oleaginosa / Cultura Comercial",
        "cycle_days": "120 a 130 dias (cultivares rasteiras)",
        "scores": {
            "protecao_solo": 0.60,
            "fixacao_nitrogenio": 0.65,
            "quebra_pragas": 0.70,
            "resiliencia_hidrica": 0.50,
            "renda_adicional": 0.95,
            "simplicidade_operacional": 0.45,
        },
        "why_suggested": "Aproveitamento da vocação regional histórica da região de Sertãozinho e Jaboticabal com alta remuneração por hectare.",
        "evidence": "Polo agroindustrial do amendoim concentrado em SP; fixação biológica relevante e parceria tradicional entre canavieiros e arrendatários.",
        "benefits": "Altíssimo valor agregado por hectare; excelente fixação de N; quebra eficaz do ciclo biológico de pragas da gramínea (cana).",
        "unknowns": "Disponibilidade de arrancadores e colhedores especializados na data exata; textura do solo (exige solos arenosos a médios).",
        "risks": "O arranquio das vagens revolve os primeiros 10 cm de solo; se ocorrer chuva torrencial logo após o arranquio, há risco acentuado de erosão.",
        "confidence": "Alta na viabilidade econômica regional; Média quanto ao impacto de erosão em anos de precipitação atípica.",
        "specialist_review": "Avaliar textura do solo (evitar solos muito argilosos que dificultam o arranquio) e monitorar previsões meteorológicas na colheita."
    }
}
