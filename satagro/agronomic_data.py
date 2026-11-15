"""
SatAgro - Base de Referência Agronômica e Fichas Explicativas
Projeto: SatAgro - NASA Space Apps Challenge 2026
Equipe: Latino Party
Desafio: Field Shift: Adapting Farms with NASA Data

Conforme P0.1 e P0.6:
- Pontuações são apresentadas estritamente como avaliações heurísticas ilustrativas.
- Não atribui notas à NASA.
- Separa rigorosamente dados NASA, indicadores derivados, literatura técnica e heurísticas.
- Remove alegações de perda de solo ou produtividade medidas no talhão.
"""

from __future__ import annotations

from typing import Any, Dict


CRITERIA_METADATA = {
    "protecao_solo": {
        "name": "Proteção do Solo (Cobertura Vegetal)",
        "description": "Potencial teórico da espécie em estabelecer cobertura vegetal sobre a superfície durante os meses chuvosos.",
        "scientific_basis": "Conceitos clássicos de cobertura vegetal e dissipação de energia das chuvas (Boletins Técnicos IAC / Embrapa).",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
    "fixacao_nitrogenio": {
        "name": "Aporte de N e Biomassa Orgânica",
        "description": "Capacidade da espécie em realizar simbiose com bactérias fixadoras de nitrogênio (FBN) e produzir massa vegetal.",
        "scientific_basis": "Estudos de adubação verde e microbiologia do solo (Embrapa Soja / IAC).",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
    "quebra_pragas": {
        "name": "Descontinuidade de Hospedeiros da Cana",
        "description": "Papel da espécie não-gramínea na quebra do ciclo biológico de pragas e nematoides da cana-de-açúcar.",
        "scientific_basis": "Princípios de rotação de culturas para manejo integrado de pragas e nematoides (Embrapa / IAC).",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
    "resiliencia_hidrica": {
        "name": "Tolerância Teórica a Déficit Hídrico",
        "description": "Capacidade intrínseca da cultura em suportar períodos sem chuva durante seu ciclo fenológico.",
        "scientific_basis": "Coeficientes de sensibilidade de cultura (FAO 33 e FAO 56).",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
    "renda_adicional": {
        "name": "Potencial de Renda Comercial Direta",
        "description": "Geração direta de receita através da colheita e venda de grãos/oleaginosas na entressafra.",
        "scientific_basis": "Mercado regional consolidado de grãos e oleaginosas no Estado de São Paulo.",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
    "simplicidade_operacional": {
        "name": "Simplicidade Operacional e Custo de Implantação",
        "description": "Menor necessidade de maquinário de colheita especializado e menor custo inicial com sementes e defensivos.",
        "scientific_basis": "Estrutura operacional e calendários de reforma do setor sucroenergético.",
        "scale": "Escala de referência ilustrativa (0 a 1)",
    },
}


STRATEGIES_DATABASE: Dict[str, Dict[str, Any]] = {
    "atual": {
        "id": "atual",
        "name": "Prática Atual (Reforma Convencional / Pousio)",
        "crop_type": "Pousio / Sem Cultura de Cobertura",
        "cycle_days": "60 a 120 dias (intervalo entre corte e replantio)",
        "reference_scores": {
            "protecao_solo": 0.15,
            "fixacao_nitrogenio": 0.05,
            "quebra_pragas": 0.20,
            "resiliencia_hidrica": 0.40,
            "renda_adicional": 0.00,
            "simplicidade_operacional": 0.95,
        },
        # 1. Dados Observacionais / Estimados NASA
        "nasa_observational_data": (
            "A NASA POWER informa que a região histórica apresenta alta concentração de chuvas nos meses de verão "
            "(cerca de 75% da precipitação anual ocorre entre novembro e março). A NASA não mede a cobertura vegetal "
            "específica do seu talhão neste protótipo."
        ),
        # 2. Indicadores Derivados SatAgro
        "derived_indicators": (
            "Cálculo climatológico indica que o período convencional de reforma coincide com a época de maior índice pluviométrico regional."
        ),
        # 3. Literatura Técnica de Referência
        "technical_literature": (
            "Publicações agronômicas (IAC e Embrapa) documentam amplamente que solos desprovidos de cobertura vegetal "
            "durante chuvas convectivas tropicais estão sujeitos a escoamento superficial acelerado e lixiviação de nutrientes. "
            "O pousio não promove fixação biológica de nitrogênio e não gera receita comercial."
        ),
        # 4. Avaliação Heurística Ilustrativa
        "heuristic_scoring_explanation": (
            "A nota atribuída reflete sua alta simplicidade operacional frente à pontuação muito baixa nos critérios conservacionistas "
            "e econômicos. A pontuação é uma ponderação ilustrativa das prioridades do usuário com notas de referência da literatura, "
            "não um cálculo de produtividade da fazenda."
        ),
        "unknowns": "Condições físicas do solo (declividade, compactação, teor de argila) e histórico local de terraceamento.",
        "confidence": "Qualitativa / Heurística de Referência (fundamentada em conceitos clássicos de conservação do solo)",
        "specialist_review": "O agrônomo deve avaliar se a declividade da área exige contenção física imediata caso a reforma permaneça em pousio."
    },
    "soja": {
        "id": "soja",
        "name": "Cana + Soja (Glycine max)",
        "crop_type": "Grão Comercial Leguminoso",
        "cycle_days": "95 a 115 dias (cultivares precoces)",
        "reference_scores": {
            "protecao_solo": 0.65,
            "fixacao_nitrogenio": 0.70,
            "quebra_pragas": 0.60,
            "resiliencia_hidrica": 0.55,
            "renda_adicional": 0.85,
            "simplicidade_operacional": 0.60,
        },
        # 1. Dados Observacionais / Estimados NASA
        "nasa_observational_data": (
            "A climatologia regional da NASA POWER aponta temperaturas médias de verão em torno de 24–25 °C e acumulados "
            "hídricos que historicamente atendem à exigência média de ciclo da soja no Centro-Sul brasileiro."
        ),
        # 2. Indicadores Derivados SatAgro
        "derived_indicators": (
            "Os indicadores do SatAgro apontam que a janela climática de verão coincide com o ciclo produtivo da cultura."
        ),
        # 3. Literatura Técnica de Referência
        "technical_literature": (
            "Estudos da Embrapa Soja e CTC apontam que a rotação cana-soja permite fixação biológica de nitrogênio simbiótica, "
            "amortização financeira dos custos de reforma pela venda de grãos e cobertura foliar após o fechamento da entrelinha. "
            "Alertam, contudo, para a sensibilidade da soja a estiagens curtas durante a fase de granação e o risco de compactação "
            "do solo se a colheita ocorrer em períodos chuvosos."
        ),
        # 4. Avaliação Heurística Ilustrativa
        "heuristic_scoring_explanation": (
            "Recebe pontuação de destaque quando o produtor prioriza renda direta e fixação de nitrogênio. A pontuação é um índice "
            "heurístico baseado nas preferências do usuário, e não uma estimativa de sacas por hectare."
        ),
        "unknowns": "Infestação de nematoides no talhão (necessidade de cultivar resistente) e disponibilidade regional de colhedoras.",
        "confidence": "Qualitativa / Heurística de Referência (prática amplamente documentada na literatura sucroenergética)",
        "specialist_review": "Validar com o agrônomo a compatibilidade do ciclo da cultivar de soja com a data limite de plantio da cana-planta."
    },
    "crotalaria": {
        "id": "crotalaria",
        "name": "Cana + Crotalária (Crotalaria spectabilis / juncea)",
        "crop_type": "Adubo Verde / Cobertura de Solo",
        "cycle_days": "70 a 90 dias até florescimento/dessecação",
        "reference_scores": {
            "protecao_solo": 0.95,
            "fixacao_nitrogenio": 0.95,
            "quebra_pragas": 0.90,
            "resiliencia_hidrica": 0.85,
            "renda_adicional": 0.10,
            "simplicidade_operacional": 0.75,
        },
        # 1. Dados Observacionais / Estimados NASA
        "nasa_observational_data": (
            "A NASA POWER indica forte radiação solar e temperatura regional favorável ao rápido acúmulo de biomassa vegetal "
            "durante o verão na macrorregião."
        ),
        # 2. Indicadores Derivados SatAgro
        "derived_indicators": (
            "Indicadores do SatAgro mostram que o período de chuvas intensas é plenamente sobreposto pelo período vegetativo da cultura de cobertura."
        ),
        # 3. Literatura Técnica de Referência
        "technical_literature": (
            "Pesquisas do IAC (Ambrosano et al.) e da Embrapa destacam a crotalária pelo rápido fechamento de dossel, excelente "
            "proteção mecânica contra o impacto das gotas de chuva, aporte expressivo de nitrogênio biológico na biomassa e ação de "
            "planta-armadilha para nematoides fitoparasitas (Pratylenchus zeae e Meloidogyne javanica). Como contraponto, não gera "
            "venda comercial direta de grãos e requer manejo correto de dessecação no início do florescimento."
        ),
        # 4. Avaliação Heurística Ilustrativa
        "heuristic_scoring_explanation": (
            "Alcança a liderança do ranking quando o produtor atribui alta prioridade à saúde do solo, proteção contra erosão e supressão "
            "de nematoides. Trata-se de uma ordenação heurística multicritério, e não de um ensaio agronômico local."
        ),
        "unknowns": "Análise nematológica laboratorial para escolher entre C. spectabilis (nematoides) ou C. juncea (máxima biomassa).",
        "confidence": "Qualitativa / Heurística de Referência (embasada em extensas pesquisas de adubação verde do IAC/Embrapa)",
        "specialist_review": "Definir com o agrônomo o momento exato de manejo da biomassa para evitar a lignificação excessiva da palhada."
    },
    "amendoim": {
        "id": "amendoim",
        "name": "Cana + Amendoim (Arachis hypogaea)",
        "crop_type": "Oleaginosa / Cultura Comercial",
        "cycle_days": "120 a 130 dias (cultivares rasteiras)",
        "reference_scores": {
            "protecao_solo": 0.60,
            "fixacao_nitrogenio": 0.65,
            "quebra_pragas": 0.70,
            "resiliencia_hidrica": 0.50,
            "renda_adicional": 0.95,
            "simplicidade_operacional": 0.45,
        },
        # 1. Dados Observacionais / Estimados NASA
        "nasa_observational_data": (
            "A climatologia da NASA POWER descreve a sazonalidade térmica da região de Sertãozinho e Jaboticabal, historicamente "
            "compatível com o cultivo de verão da oleaginosa."
        ),
        # 2. Indicadores Derivados SatAgro
        "derived_indicators": (
            "O SatAgro identifica a coincidência entre a estação chuvosa e as exigências térmicas de maturação da cultura."
        ),
        # 3. Literatura Técnica de Referência
        "technical_literature": (
            "O cultivo de amendoim em áreas de reforma é uma vocação tradicional do polo de Sertãozinho e Jaboticabal (IAC Centro de Grãos). "
            "Oferece elevada liquidez financeira e quebra eficaz de hospedeiros da cana. Todavia, a operação de colheita requer arranquio "
            "e revolvimento mecânico da camada superficial; a literatura enfatiza a vulnerabilidade a chuvas intensas no intervalo entre arranquio e recolhimento."
        ),
        # 4. Avaliação Heurística Ilustrativa
        "heuristic_scoring_explanation": (
            "Obtém pontuação máxima no critério de renda direta na entressafra, sendo penalizada no critério operacional devido à exigência "
            "de maquinário específico de colheita. É uma avaliação heurística orientada pelas prioridades do usuário."
        ),
        "unknowns": "Textura do solo (solos excessivamente argilosos dificultam o arranquio das vagens) e previsão do tempo no arranquio.",
        "confidence": "Qualitativa / Heurística de Referência (prática tradicional regional documentada pelo IAC)",
        "specialist_review": "Confirmar se o solo possui textura arenosa/média adequada e se há equipe operacional e maquinário disponíveis."
    }
}
