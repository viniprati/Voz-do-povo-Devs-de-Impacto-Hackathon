import os
import uvicorn
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import re

# =====================================================
# 1. CONFIGURAÇÃO E SEGURANÇA
# =====================================================

# Carrega variáveis do arquivo .env (apenas para rodar localmente)
# No Vercel, ele ignora isso e pega das "Environment Variables" do painel.
load_dotenv()

# Tenta pegar a chave do ambiente
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("⚠️ AVISO: API Key não encontrada nas variáveis de ambiente!")
    print("Para rodar local, crie um arquivo .env com GOOGLE_API_KEY=sua_chave")
    # Se quiser testar rápido sem .env, descomente a linha abaixo (NÃO SUBA PRO GITHUB):
    # API_KEY = "SUA_CHAVE_AQUI"

if API_KEY:
    genai.configure(api_key=API_KEY)

# =====================================================
# 2. INICIALIZAÇÃO DO SERVIDOR
# =====================================================
app = FastAPI()

# Configuração de CORS (Permite que o Frontend acesse o Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção real, troque "*" pelo domínio do seu site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Função para selecionar o melhor modelo disponível na conta
def get_best_model():
    priority_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
    try:
        # Lista modelos disponíveis
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Tenta encontrar o melhor modelo da lista de prioridade
        for model_name in priority_models:
            for available in available_models:
                if model_name in available:
                    print(f"✅ Modelo Selecionado: {available}")
                    return available
    except Exception as e:
        print(f"⚠️ Erro ao listar modelos: {e}")
    
    return "models/gemini-pro" # Fallback padrão

# Inicializa o modelo
active_model_name = get_best_model() if API_KEY else "models/gemini-pro"
model = genai.GenerativeModel(active_model_name)

# --- MODELOS DE DADOS (O que o Frontend envia) ---
class ExplainRequest(BaseModel):
    pl_text: str
    user_interest: str

class FeedbackRequest(BaseModel):
    pl_title: str
    author_name: str
    author_email: str
    vote_type: str
    reason: str

# =====================================================
# 3. ROTA DE EXPLICAÇÃO (IA - MODO LOCUTOR)
# =====================================================
@app.post("/explain")
async def explain_law(request: ExplainRequest):
    print(f"📥 Processando explicação sobre: {request.user_interest}...")
    
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key não configurada no servidor.")

    try:
        prompt = f"""
        ATUE COMO UM LOCUTOR DE RÁDIO POPULAR E CARISMÁTICO.
        
        CONTEXTO:
        Você precisa explicar a seguinte lei técnica: "{request.pl_text}"
        Para um cidadão comum, usando uma analogia baseada em: "{request.user_interest}".

        TAREFA:
        Escreva um roteiro curto (máximo 3 parágrafos) que será LIDO EM VOZ ALTA pelo celular.
        
        REGRAS DE ESTILO (CRUCIAL):
        1. Use linguagem falada, simples e direta (Ex: "Olha só...", "Imagina que...", "Sabe quando...").
        2. Mantenha a analogia do tema "{request.user_interest}" durante toda a explicação para facilitar o entendimento.
        3. NÃO use listas, tópicos, hashtags ou caracteres especiais (*, -). O texto deve ser corrido e fluido para leitura.
        4. Termine com uma frase de impacto sobre como isso afeta o dia a dia da pessoa.

        RETORNE APENAS ESTE JSON (SEM MARKDOWN):
        {{
            "explanation": "O texto da explicação aqui..."
        }}
        """

        response = model.generate_content(prompt)
        texto_bruto = response.text

        # Limpeza de JSON (Remove ```json e espaços extras)
        texto_limpo = re.sub(r"```json|```", "", texto_bruto).strip()
        
        try:
            return json.loads(texto_limpo)
        except json.JSONDecodeError:
            # Se a IA falhar em retornar JSON, retorna o texto puro encapsulado
            return { "explanation": texto_limpo }

    except Exception as e:
        print(f"❌ Erro na geração: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# 4. ROTA DE FEEDBACK (SIMULAÇÃO DE E-MAIL)
# =====================================================
@app.post("/send_feedback")
async def send_email_simulation(feedback: FeedbackRequest):
    # Isso simula o envio e imprime no log do servidor (Terminal)
    print("\n" + "="*50)
    print(f"📧 [SIMULAÇÃO] DISPARANDO E-MAIL PARA DEPUTADO")
    print("="*50)
    print(f"DE: Cidadão Brasileiro (via Voz do Povo)")
    print(f"PARA: {feedback.author_name} <{feedback.author_email}>")
    print(f"ASSUNTO: Feedback sobre o projeto {feedback.pl_title}")
    print("-" * 30)
    print(f"Mensagem:")
    print(f"Excelentíssimo(a),")
    print(f"Um eleitor registrou o seguinte voto na plataforma:")
    print(f"VOTO: {feedback.vote_type.upper()}")
    print(f"MOTIVO: {feedback.reason}")
    print("="*50 + "\n")
    
    return {
        "status": "success", 
        "message": f"Feedback enviado com sucesso para o gabinete de {feedback.author_name}!"
    }

# Bloco para rodar localmente com 'python main.py'
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)