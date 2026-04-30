document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyzeForm');
    const b2bSlider = document.getElementById('b2b_slider');
    const b2bVal = document.getElementById('b2b_val');
    const b2cVal = document.getElementById('b2c_val');
    const collapseBtn = document.querySelector('.collapse-btn');
    const collapseContent = document.querySelector('.collapse-content');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.querySelector('.spinner');
    const btnText = document.querySelector('.btn-text');
    const resultsArea = document.getElementById('resultsArea');
    
    let rankingChart = null;

    // Helper function to safely get values
    const getVal = (id, def = '') => {
        const el = document.getElementById(id);
        return el ? el.value : def;
    };

    const getCheck = (id, def = true) => {
        const el = document.getElementById(id);
        return el ? el.checked : def;
    };

    // Dual Slider Logic
    b2bSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        b2bVal.textContent = val;
        b2cVal.textContent = 100 - val;
    });

    // Collapse Logic
    if (collapseBtn) {
        collapseBtn.addEventListener('click', () => {
            if (collapseContent) collapseContent.classList.toggle('open');
        });
    }

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show Loading
        submitBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');
        const originalText = btnText ? btnText.textContent : submitBtn.textContent;
        if (btnText) btnText.textContent = 'PROCESSANDO...';
        else submitBtn.textContent = 'PROCESSANDO...';
        
        const b2b = parseFloat(b2bSlider.value);
        const b2c = 100 - b2b;

        const formData = {
            nome_empresa: getVal('razao_social'),
            nome_responsavel: getVal('nome_responsavel'),
            email: getVal('email'),
            telefone: getVal('telefone'),
            endereco_completo: getVal('endereco_completo'),
            consentimento: getCheck('consentimento'),
            faturamento_anual: getVal('faturamento_anual', 0),
            custo_manutencao_pecas: getVal('custo_manutencao_pecas', 0),
            folha_pagamento_direta: getVal('folha_pagamento_direta', 0),
            aluguel_despesas_fixas: getVal('aluguel_despesas_fixas', 0),
            depreciacao_ativos: getVal('depreciacao_ativos', 0),
            investimento_anual_em_ativos: getVal('investimento_anual_em_ativos', 0),
            percentual_clientes_b2b: b2b,
            percentual_clientes_b2c: b2c,
            percentual_clientes_que_aproveitam_credito: getVal('percentual_clientes_que_aproveitam_credito', 0),
            ano: getVal('ano', 2027),
            cobertura_geografica: getVal('cobertura_geografica', 'municipal'),
            maturidade_sistema_gestao: getVal('maturidade_sistema_gestao', 3),
            maturidade_contabil_fiscal: getVal('maturidade_contabil_fiscal', 3),
            intensidade_contratos_complexos: getVal('intensidade_contratos_complexos', 3),
            necessidade_caixa_curto_prazo: getVal('necessidade_caixa_curto_prazo', 3),
        };

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.status === 'success') {
                updateUI(data.resultado, data.analise_ia);
                resultsArea.classList.remove('hidden');
                resultsArea.scrollIntoView({ behavior: 'smooth' });
            } else {
                alert('Erro: ' + data.message);
            }
        } catch (error) {
            console.error('Erro:', error);
            alert('Erro no Servidor: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            if (spinner) spinner.classList.add('hidden');
            if (btnText) btnText.textContent = originalText;
            else submitBtn.textContent = originalText;
        }
    });

    function updateUI(skill, ia) {
        // Main Recommendation
        document.getElementById('mainRecommendation').textContent = skill.recomendacao_principal_label;
        document.getElementById('executiveSummary').textContent = `Com base no perfil da ${skill.empresa} para o ano ${skill.ano}, o regime ${skill.recomendacao_principal_label} apresenta melhor equilíbrio entre competitividade e risco.`;

        // Chart
        const labels = skill.ranking.map(item => item.label);
        const scores = skill.ranking.map(item => item.score);

        if (rankingChart) rankingChart.destroy();
        
        const ctx = document.getElementById('rankingChart').getContext('2d');
        rankingChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Score de Eficiência',
                    data: scores,
                    backgroundColor: [
                        'rgba(0, 242, 255, 0.6)',
                        'rgba(0, 242, 255, 0.3)',
                        'rgba(255, 255, 255, 0.1)',
                        'rgba(255, 255, 255, 0.05)'
                    ],
                    borderColor: 'rgba(0, 242, 255, 1)',
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                scales: {
                    x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, border: { display: false } },
                    y: { grid: { display: false }, border: { display: false } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // IA Analysis (Markdown)
        document.getElementById('iaContent').innerHTML = marked.parse(ia);

        // Action Plan
        const list = document.getElementById('actionPlanList');
        if (list) {
            list.innerHTML = '';
            skill.plano_acao.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                list.appendChild(li);
            });
        }

        // DRE Comparison Table
        renderDRETable(skill.ranking);
    }

    function formatCurrency(v) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
    }

    function renderDRETable(ranking) {
        const container = document.getElementById('dreTableContainer');
        if (!container) return;

        let html = `
            <div class="dre-table-wrapper">
                <h3><i class="fas fa-file-invoice-dollar"></i> Simulador de DRE Comparativo</h3>
                <table class="dre-table">
                    <thead>
                        <tr>
                            <th>Conta DRE</th>
                            ${ranking.map(r => `<th>${r.label}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Receita Bruta</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.receita_bruta)}</td>`).join('')} </tr>
                        <tr><td>(-) Impostos Faturam.</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.impostos_faturamento)}</td>`).join('')} </tr>
                        <tr class="highlight-row"><td>Receita Líquida</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.receita_liquida)}</td>`).join('')} </tr>
                        <tr><td>(-) Custos Operac.</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.custos_variaveis)}</td>`).join('')} </tr>
                        <tr><td>(-) Despesas Fixas</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.despesas_fixas)}</td>`).join('')} </tr>
                        <tr><td>(+) Créditos Aplicados</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.creditos_aproveitados || 0)}</td>`).join('')} </tr>
                        <tr class="profit-row"><td>LUCRO LÍQUIDO FINAL</td> ${ranking.map(r => `<td>${formatCurrency(r.dre.lucro_liquido)}</td>`).join('')} </tr>
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = html;
    }

    // DISCOVERY HELPER LOGIC
    window.openHelper = (type) => {
        const modal = document.getElementById('helperModal');
        const title = document.getElementById('helperTitle');
        const body = document.getElementById('helperBody');
        
        modal.style.display = 'block';

        if (type === 'revenue') {
            title.innerHTML = '<h3>Mecanismo: Faturamento Anual</h3>';
            body.innerHTML = `
                <p style="font-size: 0.9rem; margin-bottom: 1rem; color: var(--text-dim);">
                    <strong>Como obter os dados:</strong> Consulte sua <strong>DRE (Demonstração do Resultado do Exercício)</strong> no campo "Receita Operacional Bruta" ou peça ao seu contador o total de notas de serviço/locação emitidas nos últimos 12 meses.
                </p>
                <div class="helper-calc">
                    <p style="color: var(--primary);">Dica Estratégica:</p>
                    <p style="font-size: 0.85rem; color: var(--text-dim);">Para previsões de 2026/2027, utilize a projeção de crescimento baseada no histórico atual.</p>
                </div>
            `;
        } else if (type === 'assets') {
            title.innerHTML = '<h3>Mecanismo: Investimento em Ativos</h3>';
            body.innerHTML = `
                <p style="font-size: 0.9rem; margin-bottom: 1rem; color: var(--text-dim);">
                    <strong>Como obter os dados:</strong> Verifique seu <strong>Relatório de Compras/Entradas</strong> para equipamentos de locação ou o Balanço Patrimonial na conta de "Imobilizado".
                </p>
                <div class="helper-calc">
                    <p style="color: var(--primary);">Por que isso importa?</p>
                    <p style="font-size: 0.85rem; color: var(--text-dim);">Na Reforma Tributária, o crédito imediato sobre a compra de ativos (Bens de Capital) é um dos maiores benefícios para quem opta pelo Lucro Real.</p>
                </div>
            `;
        } else if (type === 'b2b') {
            title.innerHTML = '<h3>Mecanismo: B2B vs B2C</h3>';
            body.innerHTML = `
                <p style="font-size: 0.9rem; margin-bottom: 1rem; color: var(--text-dim);">
                    <strong>Como obter os dados:</strong> Acesse seu relatório de faturamento do último ano e filtre por tipo de documento (CNPJ vs CPF).
                </p>
                <div class="helper-calc">
                    <p style="margin-bottom: 1rem; color: var(--primary);">Calculadora de Proporção:</p>
                    <div class="helper-input-group">
                        <label>Faturamento Anual com Empresas (CNPJ)</label>
                        <input type="number" id="calc_cnpj" class="helper-input" placeholder="Ex: 850000">
                    </div>
                    <div class="helper-input-group">
                        <label>Faturamento Anual com Pessoas Físicas (CPF)</label>
                        <input type="number" id="calc_cpf" class="helper-input" placeholder="Ex: 150000">
                    </div>
                    <button class="btn-primary" style="padding: 0.8rem;" onclick="applyCalc('b2b')">Calcular e Aplicar</button>
                </div>
            `;
        } else if (type === 'credit') {
            title.innerHTML = '<h3>Mecanismo: Aproveitamento de Crédito</h3>';
            body.innerHTML = `
                <p style="font-size: 0.9rem; margin-bottom: 1rem; color: var(--text-dim);">
                    <strong>Como obter os dados:</strong> Identifique clientes B2B que estão nos regimes de <strong>Lucro Real ou Lucro Presumido</strong>. Estes são os que mais valorizam o crédito para abater CBS/IBS.
                </p>
                <div class="helper-calc" style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 1rem;">
                    <p style="margin-bottom: 1rem; color: var(--primary);">Calculadora de Relevância:</p>
                    <div class="helper-input-group">
                        <label>Faturamento com Clientes "Lucro Real / Presumido"</label>
                        <input type="number" id="calc_large" class="helper-input" placeholder="R$">
                    </div>
                    <div class="helper-input-group">
                        <label>Faturamento com Clientes "Simples Nacional / CPF"</label>
                        <input type="number" id="calc_small" class="helper-input" placeholder="R$">
                    </div>
                    <button class="btn-primary" style="padding: 0.8rem;" onclick="applyCalc('credit')">Calcular e Aplicar</button>
                </div>
            `;
        }
    };

    window.closeHelper = () => {
        document.getElementById('helperModal').style.display = 'none';
    };

    window.applyCalc = (type) => {
        if (type === 'b2b') {
            const cnpj = parseFloat(document.getElementById('calc_cnpj').value) || 0;
            const cpf = parseFloat(document.getElementById('calc_cpf').value) || 0;
            const total = cnpj + cpf;
            if (total > 0) {
                const perc = Math.round((cnpj / total) * 100);
                document.getElementById('b2b_slider').value = perc;
                document.getElementById('b2b_val').textContent = perc;
                document.getElementById('b2c_val').textContent = 100 - perc;
            }
        } else if (type === 'credit') {
            const large = parseFloat(document.getElementById('calc_large').value) || 0;
            const small = parseFloat(document.getElementById('calc_small').value) || 0;
            const total = large + small;
            if (total > 0) {
                const perc = Math.round((large / total) * 100);
                document.getElementById('percentual_clientes_que_aproveitam_credito').value = perc;
            }
        }
        closeHelper();
    };

    // Close modal on click outside
    window.onclick = (event) => {
        const modal = document.getElementById('helperModal');
        if (event.target == modal) {
            closeHelper();
        }
    };
});
