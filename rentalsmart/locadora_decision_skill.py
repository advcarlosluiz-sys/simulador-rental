"""
Skill de apoio à gestão tributária e tomada de decisão para locadoras - Versão RENTAL SMART com DRE.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Literal

AnoAnalise = Literal[2026, 2027]
Regime = Literal["simples_puro", "simples_hibrido", "lucro_presumido", "lucro_real"]

REGIME_LABELS: Dict[Regime, str] = {
    "simples_puro": "Simples Nacional Puro",
    "simples_hibrido": "Simples Nacional Híbrido",
    "lucro_presumido": "Lucro Presumido",
    "lucro_real": "Lucro Real",
}

@dataclass
class PerfilLocadora:
    """Perfil operacional e financeiro para Simulação de DRE."""
    nome_empresa: str
    faturamento_anual: float
    
    # Detalhamento de Custos e Despesas para DRE
    custo_manutencao_pecas: float
    folha_pagamento_direta: float
    aluguel_despesas_fixas: float
    depreciacao_ativos: float
    investimento_anual_em_ativos: float
    
    # Perfil Qualitativo
    percentual_clientes_b2b: float
    percentual_clientes_b2c: float
    percentual_clientes_que_aproveitam_credito: float
    maturidade_sistema_gestao: int
    maturidade_contabil_fiscal: int
    intensidade_contratos_complexos: int
    sensibilidade_preco_clientes: int
    capacidade_suportar_compliance: int
    necessidade_caixa_curto_prazo: int
    cobertura_geografica: Literal["municipal", "estadual", "interestadual"]
    observacoes: Optional[str] = None

@dataclass
class DRE:
    """Estrutura de Demonstrativo de Resultados."""
    receita_bruta: float
    impostos_faturamento: float
    receita_liquida: float
    custos_variaveis: float
    margem_contribuicao: float
    despesas_fixas: float
    depreciacao: float
    ebit: float
    imp_lucro: float # IRPJ/CSLL
    lucro_liquido: float
    creditos_aproveitados: float = 0.0

class LocadoraDecisionSkill:
    """Skill com Motor de Simulação de DRE e Score."""

    def comparar_regimes(self, perfil: PerfilLocadora, ano: AnoAnalise) -> Dict:
        # Gera DRE para cada regime
        dres = {
            "simples_puro": self._calcular_dre_simples(perfil, hibrido=False),
            "simples_hibrido": self._calcular_dre_simples(perfil, hibrido=True),
            "lucro_presumido": self._calcular_dre_presumido(perfil),
            "lucro_real": self._calcular_dre_real(perfil)
        }
        
        # Gera Rankings (Heurística baseada no Lucro Líquido e Maturidade)
        ranking = []
        for regime, dre in dres.items():
            score = self._calcular_score(regime, dre, perfil, ano)
            ranking.append({
                "regime": regime,
                "label": REGIME_LABELS[regime],
                "lucro_liquido": dre.lucro_liquido,
                "score": score,
                "dre": dre.__dict__
            })
        
        ranking = sorted(ranking, key=lambda x: x['score'], reverse=True)
        
        # Gera Plano de Ação dinâmico
        plano_acao = [
            f"Migrar para o regime {ranking[0]['label']} conforme simulação de DRE.",
            "Revisar contratos B2B para destacar a transferência de créditos de IBS/CBS.",
            "Auditar balanço para garantir máxima apropriação de créditos sobre ativos."
        ]
        
        return {
            "empresa": perfil.nome_empresa,
            "ano": ano,
            "ranking": ranking,
            "recomendacao_principal_label": ranking[0]['label'],
            "recomendacao_secundaria_label": ranking[1]['label'],
            "plano_acao": plano_acao
        }

    def _calcular_dre_simples(self, perfil: PerfilLocadora, hibrido: bool) -> DRE:
        # Alíquota média estimada do Simples (Anexo III)
        aliq_simples = 0.12 if perfil.faturamento_anual < 1800000 else 0.15
        
        if hibrido:
            # No híbrido, recolhe IBS/CBS cheio (est. 26.5%) mas gera créditos.
            # O IBS/CBS substitui parte da guia do Simples.
            aliq_ajustada_simples = aliq_simples * 0.7 
            aliq_ibs_cbs = 0.265
            impostos = perfil.faturamento_anual * (aliq_ajustada_simples + aliq_ibs_cbs)
            creditos = perfil.custo_manutencao_pecas * 0.15 # Créditos parciais de entrada
        else:
            impostos = perfil.faturamento_anual * aliq_simples
            creditos = 0
            
        receita_liq = perfil.faturamento_anual - impostos
        custos = perfil.custo_manutencao_pecas + perfil.folha_pagamento_direta
        ebit = receita_liq - custos - perfil.aluguel_despesas_fixas - perfil.depreciacao_ativos
        
        return DRE(
            receita_bruta=perfil.faturamento_anual,
            impostos_faturamento=impostos,
            receita_liquida=receita_liq,
            custos_variaveis=custos,
            margem_contribuicao=receita_liq - custos,
            despesas_fixas=perfil.aluguel_despesas_fixas,
            depreciacao=perfil.depreciacao_ativos,
            ebit=ebit,
            imp_lucro=0, # Já incluso no Simples
            lucro_liquido=ebit + creditos,
            creditos_aproveitados=creditos
        )

    def _calcular_dre_presumido(self, perfil: PerfilLocadora) -> DRE:
        # PIS/COFINS (3.65%) + ISS (est. 5%)
        aliq_faturamento = 0.0865
        impostos_f = perfil.faturamento_anual * aliq_faturamento
        
        # IRPJ/CSLL sobre presunção de 32% do faturamento
        presuncao = perfil.faturamento_anual * 0.32
        imp_lucro = presuncao * 0.24 # 15% IRPJ + 9% CSLL
        
        receita_liq = perfil.faturamento_anual - impostos_f
        custos = perfil.custo_manutencao_pecas + perfil.folha_pagamento_direta
        ebit = receita_liq - custos - perfil.aluguel_despesas_fixas - perfil.depreciacao_ativos
        
        return DRE(
            receita_bruta=perfil.faturamento_anual,
            impostos_faturamento=impostos_f,
            receita_liquida=receita_liq,
            custos_variaveis=custos,
            margem_contribuicao=receita_liq - custos,
            despesas_fixas=perfil.aluguel_despesas_fixas,
            depreciacao=perfil.depreciacao_ativos,
            ebit=ebit,
            imp_lucro=imp_lucro,
            lucro_liquido=ebit - imp_lucro
        )

    def _calcular_dre_real(self, perfil: PerfilLocadora) -> DRE:
        # PIS/COFINS Não Cumulativo (9.25%)
        aliq_faturamento = 0.0925
        impostos_f = perfil.faturamento_anual * aliq_faturamento
        
        # Créditos sobre custos e depreciação no Real
        creditos = (perfil.custo_manutencao_pecas + perfil.depreciacao_ativos) * 0.0925
        
        receita_liq = perfil.faturamento_anual - impostos_f + creditos
        custos = perfil.custo_manutencao_pecas + perfil.folha_pagamento_direta
        ebit = receita_liq - custos - perfil.aluguel_despesas_fixas - perfil.depreciacao_ativos
        
        # IRPJ/CSLL sobre lucro real (ajustado por depreciação etc)
        lucro_tributavel = max(ebit, 0)
        imp_lucro = lucro_tributavel * 0.34 # 25% IRPJ (c/ adicional) + 9% CSLL
        
        return DRE(
            receita_bruta=perfil.faturamento_anual,
            impostos_faturamento=impostos_f,
            receita_liquida=receita_liq,
            custos_variaveis=custos,
            margem_contribuicao=receita_liq - custos,
            despesas_fixas=perfil.aluguel_despesas_fixas,
            depreciacao=perfil.depreciacao_ativos,
            ebit=ebit,
            imp_lucro=imp_lucro,
            lucro_liquido=ebit - imp_lucro,
            creditos_aproveitados=creditos
        )

    def _calcular_score(self, regime: Regime, dre: DRE, perfil: PerfilLocadora, ano: int) -> float:
        # Trava Legal: Simples Nacional (Limite de R$ 4.8M)
        if regime in ["simples_puro", "simples_hibrido"] and perfil.faturamento_anual > 4800000:
            return -500.0 # Desqualificado legalmente

        # Score base é o Lucro Líquido normalizado p/ escala 0-100
        score = (dre.lucro_liquido / (perfil.faturamento_anual or 1)) * 100
        
        # Penalidades por falta de maturidade em regimes complexos
        if regime in ["lucro_real", "simples_hibrido"] and perfil.maturidade_contabil_fiscal < 3:
            score -= 15
            
        # Bônus por competitividade B2B no Real/Híbrido
        if regime in ["lucro_real", "simples_hibrido"] and perfil.percentual_clientes_b2b > 50:
            score += 10
            
        return max(score, 5.0)
