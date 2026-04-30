import os
import json
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from openai import OpenAI
from locadora_decision_skill import LocadoraDecisionSkill, PerfilLocadora

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração do Banco de Dados SQLite
if os.getenv('VERCEL') == '1':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/leads_v3.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///leads_v3.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de Dados para Leads e Diagnósticos
class DiagnosticoLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_responsavel = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco_completo = db.Column(db.String(500))
    # Dados da empresa (DRE)
    faturamento_anual = db.Column(db.Float)
    custo_manutencao_pecas = db.Column(db.Float)
    folha_pagamento_direta = db.Column(db.Float)
    aluguel_despesas_fixas = db.Column(db.Float)
    depreciacao_ativos = db.Column(db.Float)
    investimento_ativos = db.Column(db.Float)
    
    b2b_percent = db.Column(db.Integer)
    credito_aproveitamento = db.Column(db.Integer)
    is_lucro_presumido = db.Column(db.Boolean)
    
    # Resultado
    recomendacao_final = db.Column(db.String(100))
    analise_detalhada = db.Column(db.Text)
    simulacao_json = db.Column(db.Text) # Guardamos o ranking e DREs aqui
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    consentimento_dados = db.Column(db.Boolean, default=True)

# Criar o banco de dados (Força recriação se houver erro de schema)
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Erro ao inicializar DB: {e}. Tentando reset...")
        # Se houver erro de schema, este bloco poderia ser expandido para resetar
        # Por enquanto, apenas tenta garantir que as tabelas existam.

# Configuração da OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Movido para dentro da função para não travar o início do app

skill = LocadoraDecisionSkill()

@app.route("/")
def index():
    # Serve a landing page premium (templates/index.html)
    return render_template("index.html")

@app.route("/diagnostico")
def diagnostico():
    # Serve o simulador/aplicativo (templates/simulator.html)
    return render_template("simulator.html")

@app.route("/logo.png")
def logo():
    # Tenta servir da static primeiro, depois da landing_page
    return send_from_directory('static', 'logo.png')

@app.route("/favicon.ico")
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Dados não fornecidos"}), 400
        
        # Converte dados para PerfilLocadora
        def safe_float(val):
            try: return float(val) if val else 0.0
            except: return 0.0

        def safe_int(val):
            try: return int(val) if val else 1
            except: return 1

        perfil = PerfilLocadora(
            nome_empresa=data.get("nome_empresa", "N/A"),
            faturamento_anual=safe_float(data.get("faturamento_anual")),
            custo_manutencao_pecas=safe_float(data.get("custo_manutencao_pecas")),
            folha_pagamento_direta=safe_float(data.get("folha_pagamento_direta")),
            aluguel_despesas_fixas=safe_float(data.get("aluguel_despesas_fixas")),
            depreciacao_ativos=safe_float(data.get("depreciacao_ativos")),
            investimento_anual_em_ativos=safe_float(data.get("investimento_anual_em_ativos")),
            percentual_clientes_b2b=safe_float(data.get("percentual_clientes_b2b")),
            percentual_clientes_b2c=safe_float(data.get("percentual_clientes_b2c", 100 - safe_float(data.get("percentual_clientes_b2b", 0)))),
            percentual_clientes_que_aproveitam_credito=safe_float(data.get("percentual_clientes_que_aproveitam_credito")),
            maturidade_sistema_gestao=safe_int(data.get("maturidade_sistema_gestao")),
            maturidade_contabil_fiscal=safe_int(data.get("maturidade_contabil_fiscal")),
            intensidade_contratos_complexos=safe_int(data.get("intensidade_contratos_complexos")),
            sensibilidade_preco_clientes=safe_int(data.get("sensibilidade_preco_clientes")),
            capacidade_suportar_compliance=safe_int(data.get("capacidade_suportar_compliance")),
            necessidade_caixa_curto_prazo=safe_int(data.get("necessidade_caixa_curto_prazo")),
            cobertura_geografica=data.get("cobertura_geografica", "municipal"),
            observacoes=data.get("observacoes", "")
        )
        
        ano = int(data.get("ano", 2027))
        
        # Executa a skill local
        resultado_json = skill.comparar_regimes(perfil, ano)
        
        # Análise via OpenAI
        analise_ia = gerar_analise_ia(resultado_json, perfil)
        
        # Preparar objeto para salvar
        novo_diagnostico = DiagnosticoLead(
            razao_social=data.get("nome_empresa", "N/A"),
            nome_responsavel=data.get("nome_responsavel", "N/A"),
            email=data.get("email", "N/A"),
            telefone=data.get("telefone", "N/A"),
            endereco_completo=data.get("endereco_completo", "N/A"),
            faturamento_anual=perfil.faturamento_anual,
            custo_manutencao_pecas=perfil.custo_manutencao_pecas,
            folha_pagamento_direta=perfil.folha_pagamento_direta,
            aluguel_despesas_fixas=perfil.aluguel_despesas_fixas,
            depreciacao_ativos=perfil.depreciacao_ativos,
            investimento_ativos=perfil.investimento_anual_em_ativos,
            b2b_percent=perfil.percentual_clientes_b2b,
            credito_aproveitamento=perfil.percentual_clientes_que_aproveitam_credito,
            is_lucro_presumido=bool(data.get("is_lucro_presumido")),
            recomendacao_final=resultado_json['recomendacao_principal_label'],
            analise_detalhada=analise_ia,
            simulacao_json=json.dumps(resultado_json),
            consentimento_dados=bool(data.get("consentimento"))
        )
        
        # Tenta salvar no banco, mas não trava se falhar
        try:
            db.session.add(novo_diagnostico)
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            print(f"Aviso: Erro ao salvar lead no banco: {str(db_err)}")

        return jsonify({
            "status": "success", 
            "resultado": resultado_json,
            "analise_ia": analise_ia
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

def gerar_analise_ia(relatorio_dict, perfil):
    """Gera uma análise estratégica usando a OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Chave OpenAI não configurada. Por favor, adicione sua chave ao arquivo .env para receber a análise estratégica da IA."

    # Inicializa o cliente aqui dentro
    sub_client = OpenAI(api_key=api_key)

    prompt = f"""
    Você é um Consultor Tributário Sênior especializado em Locadoras e na Reforma Tributária Brasileira.
    Com base nos dados estruturados abaixo, gerados por um motor de decisão heurístico, forneça uma análise estratégica narrativa e acionável.

    DADOS DA EMPRESA:
    - Nome: {perfil.nome_empresa}
    - Faturamento: R$ {perfil.faturamento_anual:,.2f}
    - Perfil Clientes: {perfil.percentual_clientes_b2b}% B2B, {perfil.percentual_clientes_b2c}% B2C
    - Ano de Análise: {relatorio_dict['ano']}

    RESULTADO DO MOTOR DE DECISÃO:
    - Recomendação Principal: {relatorio_dict['recomendacao_principal_label']}
    - Recomendação Secundária: {relatorio_dict['recomendacao_secundaria_label']}
    - Ranking Completo: {json.dumps(relatorio_dict['ranking'], ensure_ascii=False)}

    SUA TAREFA:
    1. Valide ou refine a recomendação principal, explicando o porquê econômico (ex: CBS/IBS, Split Payment).
    2. Identifique o maior risco estratégico para esta locadora na transição 2026/2027.
    3. Sugira uma "Jogada de Mestre" (estratégia diferenciada) para este perfil específico.
    4. Mantenha um tom profissional, consultivo e focado em preservação de margem.

    Responda em formato Markdown elegante.
    """

    try:
        response = sub_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Você é uma consultora estratégica tributária sênior da Alves Advocacia. Sua missão é analisar simulações de DRE para locadoras de EQUIPAMENTOS DE CONSTRUÇÃO CIVIL E CANTEIRO DE OBRAS (não veículos). REGRAS CRÍTICAS: 1. O limite do Simples Nacional é R$ 4,8 milhões/ano. 2. Foque em estratégias de depreciação de máquinas pesadas e créditos de manutenção de equipamentos industriais. 3. Sugira uma 'Jogada de Mestre' específica para o setor de construção."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao chamar OpenAI: {str(e)}"

# Rota Administrativa para Exportar Dados (CSV)
@app.route("/admin/export")
def export_leads():
    try:
        leads = DiagnosticoLead.query.all()
        si = io.StringIO()
        cw = csv.writer(si)
        # Cabeçalho
        cw.writerow(['ID', 'Razao Social', 'Responsavel', 'Email', 'Telefone', 'Endereco', 'Faturamento', 'Investimento', 'Recomendacao', 'Data'])
        for lead in leads:
            cw.writerow([
                lead.id, lead.razao_social, lead.nome_responsavel, lead.email, 
                lead.telefone, lead.endereco_completo, lead.faturamento_anual, 
                lead.investimento_ativos, lead.recomendacao_final, lead.timestamp
            ])
        
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=leads_rental_smart.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return f"Erro ao exportar: {str(e)}"

# Exportação em JSON (Completa)
@app.route("/admin/export/json")
def export_leads_json():
    try:
        leads = DiagnosticoLead.query.order_by(DiagnosticoLead.timestamp.desc()).all()
        leads_list = []
        for lead in leads:
            leads_list.append({
                "id": lead.id,
                "timestamp": lead.timestamp.isoformat(),
                "razao_social": lead.razao_social,
                "nome_responsavel": lead.nome_responsavel,
                "email": lead.email,
                "telefone": lead.telefone,
                "endereco_completo": lead.endereco_completo,
                "faturamento_anual": lead.faturamento_anual,
                "investimento_ativos": lead.investimento_ativos,
                "b2b_percent": lead.b2b_percent,
                "credito_aproveitamento": lead.credito_aproveitamento,
                "is_lucro_presumido": lead.is_lucro_presumido,
                "recomendacao_final": lead.recomendacao_final,
                "analise_detalhada": lead.analise_detalhada
            })
        
        # Cria uma resposta JSON com indentação para facilitar a leitura
        json_data = json.dumps(leads_list, indent=4, ensure_ascii=False)
        response = make_response(json_data)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename=leads_rental_smart_{datetime.now().strftime("%Y%m%d_%H%M")}.json'
        return response
    except Exception as e:
        return f"Erro ao exportar JSON: {str(e)}"

# Painel Visual de Leads (Administrativo)
@app.route("/admin")
def admin_dashboard():
    # Segurança simples por token na URL: /admin?token=alves2026
    token = request.args.get('token')
    if token != os.getenv("ADMIN_TOKEN", "alves2026"):
        return "Acesso Negado. Credenciais inválidas.", 403
    
    try:
        leads = DiagnosticoLead.query.order_by(DiagnosticoLead.timestamp.desc()).all()
        return render_template("admin.html", leads=leads)
    except Exception as e:
        return f"Erro ao carregar painel: {str(e)}"

if __name__ == "__main__":
    # Garante que as pastas templates e static existam
    if not os.path.exists('templates'): os.makedirs('templates')
    if not os.path.exists('static'): os.makedirs('static')
    
    # Rodar o app de forma estável
    app.run(host='0.0.0.0', port=5000, debug=False)
