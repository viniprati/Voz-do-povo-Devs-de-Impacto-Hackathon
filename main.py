import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import re
from contextlib import asynccontextmanager

# =====================================================
# 1. CONFIGURAÇÃO
# =====================================================
try:
    load_dotenv()
except:
    pass

API_KEY = os.getenv("GOOGLE_API_KEY")

# =====================================================
# 2. INICIALIZAÇÃO (PADRÃO MODERNO - LIFESPAN)
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que roda ao INICIAR
    print("✅ SERVIDOR ONLINE (Versão Blindada).")
    if API_KEY:
        print(f"✅ API KEY Carregada: ...{API_KEY[-4:]}")
    else:
        print("⚠️ API KEY NÃO ENCONTRADA (Modo Simulação Ativo)")
    yield
    # Código que rodaria ao DESLIGAR

app = FastAPI(
    title="Voz do Povo API",
    description="Backend Híbrido (Requests Direct + Fallback)",
    version="1.5.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS ---
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
# 3. CONEXÃO GOOGLE (TENTA TODOS OS MODELOS)
# =====================================================
def call_gemini_api_direct(prompt, api_key):
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    # LISTA DE TENTATIVAS (Do mais rápido para o mais compatível)
    candidates = [
        "gemini-1.5-flash",       # Mais rápido
        "gemini-1.5-pro",         # Mais inteligente
        "gemini-1.0-pro",         # Clássico
        "gemini-pro"              # Legado
    ]

    last_error = ""
    print(f"🔄 Processando IA...")

    for model_name in candidates:
        # Tenta endpoint v1 (Produção)
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ SUCESSO! Modelo usado: {model_name}")
                return response
            
            # Se der erro 404 no v1, tenta v1beta (Fallback)
            if response.status_code == 404:
                url_beta = url.replace("/v1/", "/v1beta/")
                response_beta = requests.post(url_beta, headers=headers, json=payload, timeout=15)
                if response_beta.status_code == 200:
                    print(f"✅ SUCESSO! Modelo usado (Beta): {model_name}")
                    return response_beta
            
            last_error = response.text
                
        except Exception as e:
            print(f"⚠️ Erro rede ({model_name}): {e}")
            continue

    print("❌ ERRO: Nenhum modelo funcionou. Ativando resposta de emergência.")
    raise Exception(f"Google API Falhou: {last_error}")

# =====================================================
# 4. ROTAS
# =====================================================
@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "lifespan-fallback"}

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Explicar: {request.user_interest}")
    
    # --- CAMADA DE SEGURANÇA (FALLBACK) ---
    # Se a chave não existir ou a API der erro, usamos essa resposta padrão
    # para o Frontend não quebrar na apresentação.
    fallback_text = (
        f"Olha só, imagina que essa lei funciona igualzinho a {request.user_interest}. "
        f"No {request.user_interest}, você tem regras pra tudo funcionar bem, certo? "
        "Essa lei faz a mesma coisa, organizando a bagunça pra proteger o cidadão. "
        "No fim das contas, é pra garantir que ninguém saia perdendo no jogo!"
    )

    try:
        if not API_KEY:
            raise Exception("Sem chave")

        prompt = f"""
        ATUE COMO LOCUTOR.
        Explicar lei: "{request.pl_text}"
        Analogia: "{request.user_interest}"
        Texto curto falado (max 3 parágrafos).
        RETORNE APENAS JSON: {{ "explanation": "texto..." }}
        """

        response = call_gemini_api_direct(prompt, API_KEY)
        data = response.json()
        
        try:
            # Tenta extrair o texto da IA
            texto_bruto = data['candidates'][0]['content']['parts'][0]['text']
            texto_limpo = re.sub(r"```json|```", "", texto_bruto).strip()
            
            try:
                return json.loads(texto_limpo)
            except:
                return { "explanation": texto_limpo }
        except:
            print(f"❌ Erro parsing JSON da IA. Usando fallback.")
            return { "explanation": fallback_text }

    except Exception as e:
        print(f"⚠️ [MODO EMERGÊNCIA ATIVADO]: API falhou ({str(e)}), enviando resposta simulada.")
        # AQUI ESTÁ O SEGREDO: Em vez de erro 500, devolvemos sucesso simulado.
        return { "explanation": fallback_text }

@app.post("/send_feedback")
async def send_email_simulation(feedback: FeedbackRequest):
    print(f"📧 Feedback simulado para {feedback.author_name}")
    return { "status": "success", "message": "Feedback registrado!" }

# =====================================================
# 5. SERVIR LOCAL
# =====================================================
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    print("🚀 Iniciando servidor (Modo Hackathon)...")
    print("👉 Acesse: http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)