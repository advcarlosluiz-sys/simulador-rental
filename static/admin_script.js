document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('adminSearch');
    const tableRows = document.querySelectorAll('tbody tr');
    const modal = document.getElementById('detailsModal');
    const closeModal = document.querySelector('.close-details');
    const detailsContent = document.getElementById('detailsBody');

    // Filter Logic
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            tableRows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }

    // Modal Logic
    window.openDetails = (leadId) => {
        const leadData = JSON.parse(document.getElementById(`data-${leadId}`).textContent);
        
        modal.style.display = 'block';
        const qual = calcularQualificacao(leadData);
        
        detailsContent.innerHTML = `
            <div class="modal-detail-header">
                <div style="float: right; text-align: right;">
                    <label style="font-size: 0.65rem; display: block; margin-bottom: 4px; color: var(--text-dim);">QUALIFICAÇÃO DO LEAD</label>
                    <span class="badge" style="background: ${qual.cor}; color: #000; border: none; padding: 6px 12px; font-size: 0.8rem;">${qual.status}</span>
                </div>
                <h2>${leadData.razao_social}</h2>
                <p>Responsável: <strong>${leadData.nome_responsavel}</strong></p>
                <div class="detail-badges">
                    <span class="badge ${leadData.recomendacao_final.includes('Lucro Real') ? 'badge-lr' : 'badge-lp'}">
                        ${leadData.recomendacao_final}
                    </span>
                    <span class="badge badge-date">${formatDate(leadData.timestamp)}</span>
                </div>
            </div>
            
            <div class="detail-grid">
                <div class="detail-item">
                    <label>E-mail</label>
                    <p>${leadData.email}</p>
                </div>
                <div class="detail-item">
                    <label>Telefone</label>
                    <p>${leadData.telefone}</p>
                </div>
                <div class="detail-item">
                    <label>Faturamento Anual</label>
                    <p>R$ ${parseFloat(leadData.faturamento_anual).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                    <small style="color: var(--primary);">${qual.resumo}</small>
                </div>
                <div class="detail-item">
                    <label>Investimento Ativos</label>
                    <p>R$ ${parseFloat(leadData.investimento_ativos).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                </div>
            </div>

            <!-- Dados Operacionais Detalhados -->
            <div class="detail-grid mt-1" style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px;">
                <div class="detail-item">
                    <label>Manutenção/Peças</label>
                    <p>R$ ${parseFloat(leadData.custo_manutencao_pecas || 0).toLocaleString('pt-BR')}</p>
                </div>
                <div class="detail-item">
                    <label>Folha Direta</label>
                    <p>R$ ${parseFloat(leadData.folha_pagamento_direta || 0).toLocaleString('pt-BR')}</p>
                </div>
                <div class="detail-item">
                    <label>Despesas Fixas</label>
                    <p>R$ ${parseFloat(leadData.aluguel_despesas_fixas || 0).toLocaleString('pt-BR')}</p>
                </div>
                <div class="detail-item">
                    <label>Depreciação</label>
                    <p>R$ ${parseFloat(leadData.depreciacao_ativos || 0).toLocaleString('pt-BR')}</p>
                </div>
            </div>

            <div class="detail-section">
                <label>Endereço</label>
                <p>${leadData.endereco_completo}</p>
            </div>

            <!-- TABELA DE DRE SIMULADA -->
            ${renderAdminDRE(leadData.simulacao_json)}

            <div class="detail-section ai-analysis-section">
                <h3><img src="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg" alt="OpenAI" width="20"> Análise Estratégica da IA</h3>
                <div class="markdown-body">
                    ${window.marked ? marked.parse(leadData.analise_detalhada) : leadData.analise_detalhada}
                </div>
            </div>
        `;
    };

    function renderAdminDRE(simulacaoJson) {
        if (!simulacaoJson) return '';
        try {
            const skill = JSON.parse(simulacaoJson);
            const ranking = skill.ranking;
            const format = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);

            return `
                <div class="detail-section">
                    <h3><i class="fas fa-file-invoice-dollar"></i> Simulador DRE Comparativo</h3>
                    <div class="dre-table-wrapper">
                        <table class="dre-table">
                            <thead>
                                <tr>
                                    <th>CONTA DRE</th>
                                    ${ranking.map(r => `<th>${r.label}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td>Receita Bruta</td> ${ranking.map(r => `<td>${format(r.dre.receita_bruta)}</td>`).join('')} </tr>
                                <tr><td>(-) Impostos</td> ${ranking.map(r => `<td>${format(r.dre.impostos_faturamento)}</td>`).join('')} </tr>
                                <tr class="highlight-row"><td>Receita Líquida</td> ${ranking.map(r => `<td>${format(r.dre.receita_liquida)}</td>`).join('')} </tr>
                                <tr><td>(-) Custos Oper.</td> ${ranking.map(r => `<td>${format(r.dre.custos_variaveis)}</td>`).join('')} </tr>
                                <tr><td>(-) Despesas Fixas</td> ${ranking.map(r => `<td>${format(r.dre.despesas_fixas)}</td>`).join('')} </tr>
                                <tr class="profit-row"><td>LUCRO LÍQUIDO</td> ${ranking.map(r => `<td>${format(r.dre.lucro_liquido)}</td>`).join('')} </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } catch(e) {
            console.error("Erro ao renderizar DRE Admin:", e);
            return '<p style="color:red">Erro ao processar dados da simulação.</p>';
        }
    }

    if (closeModal) {
        closeModal.onclick = () => {
            modal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
    }

    function calcularQualificacao(data) {
        const fat = parseFloat(data.faturamento_anual);
        const ativos = parseFloat(data.investimento_ativos);
        
        if (fat >= 3200000 || ativos >= 1000000) {
            return { status: 'POTENCIAL ELEVADO (OURO)', cor: 'var(--primary)', resumo: '✓ Lead Altamente Qualificado' };
        } else if (fat >= 1200000) {
            return { status: 'POTENCIAL MÉDIO (PRATA)', cor: '#e2e8f0', resumo: '⚠ Lead com Potencial de Escala' };
        } else {
            return { status: 'BAIXO POTENCIAL', cor: '#94a3b8', resumo: '○ Empresa de Pequeno Porte' };
        }
    }
});
