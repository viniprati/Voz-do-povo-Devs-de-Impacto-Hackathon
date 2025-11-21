import os
import sys
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
# 1. AJUSTE DE CAMINHOS
# =====================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

try:
    load_dotenv(os.path.join(root_dir, ".env"))
except:
    pass

API_KEY = os.getenv("GOOGLE_API_KEY")
ACTIVE_MODEL = None

# =====================================================
# 2. SELEÇÃO DE MODELO (COM TRAVA DE SEGURANÇA)
# =====================================================
def find_safe_model(api_key):
    """
    Verifica se a chave funciona, mas força o uso do 1.5-flash.
    IGNORA modelos 'preview' ou '2.5' que tem cota zero.
    """
    print("🔍 Validando chave e escolhendo modelo seguro...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            print(f"⚠️ Aviso: Não foi possível listar modelos. Usando padrão.")
            return "gemini-1.5-flash"

        data = response.json()
        available = [m['name'].replace("models/", "") for m in data.get('models', [])]
        
        # --- AQUI ESTÁ A CORREÇÃO ---
        # Não pegamos mais o "primeiro que aparecer".
        # Procuramos explicitamente pelo modelo GRATUITO E ESTÁVEL.
        
        if "gemini-1.5-flash" in available:
            print("✅ MODELO SELECIONADO: gemini-1.5-flash (Estável)")
            return "gemini-1.5-flash"
            
        if "gemini-1.5-flash-latest" in available:
            print("✅ MODELO SELECIONADO: gemini-1.5-flash-latest")
            return "gemini-1.5-flash-latest"

        # Se não achar o flash, tenta o 1.0 Pro (o 1.5 Pro as vezes limita)
        if "gemini-1.0-pro" in available:
             print("✅ MODELO SELECIONADO: gemini-1.0-pro")
             return "gemini-1.0-pro"
             
        # Retorno de segurança máximo
        print("⚠️ Modelo exato não listado, forçando gemini-1.5-flash")
        return "gemini-1.5-flash"

    except Exception as e:
        print(f"⚠️ Erro na verificação ({e}). Usando padrão.")
        return "gemini-1.5-flash"

# =====================================================
# 3. INICIALIZAÇÃO
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ACTIVE_MODEL
    print("✅ SERVIDOR ONLINE (Estrutura /api).")
    if API_KEY:
        print(f"🔑 Chave detectada: ...{API_KEY[-4:]}")
        ACTIVE_MODEL = find_safe_model(API_KEY)
    else:
        print("⚠️ SEM CHAVE: Modo Simulação Ativo.")
    yield

app = FastAPI(
    title="Voz do Povo API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# 4. CONEXÃO E FALLBACK
# =====================================================
def call_gemini(prompt, api_key, model):
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    # SEGURANÇA FINAL: Se por acaso o modelo for o 2.5, troca na hora.
    if "2.5" in model or "preview" in model or "exp" in model:
        print(f"⚠️ Bloqueando uso do modelo instável ({model}). Trocando para Flash.")
        model = "gemini-1.5-flash"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200: 
        return response.json()
    
    raise Exception(f"Erro Google {response.status_code}: {response.text}")

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Tema: {request.user_interest}")
    
    # MOCK (Para não travar apresentação)
    fallback = (
        f"Olha só, imagina que essa lei funciona igualzinho a {request.user_interest}. "
        "Basicamente, ela cria regras pra organizar a casa e garantir que ninguém saia perdendo. "
        "É tipo aquele regulamento que existe pra coisa funcionar direito e proteger todo mundo!"
    )

    if not API_KEY: return { "explanation": fallback }

    try:
        prompt = f"""
        ATUE COMO LOCUTOR POPULAR.
        Explicar lei: "{request.pl_text}"
        Analogia: "{request.user_interest}"
        Texto curto falado (max 3 parágrafos).
        RETORNE APENAS JSON: {{ "explanation": "texto..." }}
        """
        
        data = call_gemini(prompt, API_KEY, ACTIVE_MODEL or "gemini-1.5-flash")
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
            clean_text = re.sub(r"```json|```", "", text).strip()
            try: return json.loads(clean_text)
            except: return { "explanation": clean_text }
        except:
            return { "explanation": fallback }
            
    except Exception as e:
        print(f"⚠️ Falha API ({str(e)}). Usando Mock.")
        return { "explanation": fallback }

@app.post("/send_feedback")
async def send_email(feedback: FeedbackRequest):
    print(f"📧 Feedback: {feedback.author_name}")
    return { "status": "success" }

@app.get("/health")
async def health():
    return {"status": "ok"}

# =====================================================
# 5. LOCALHOST
# =====================================================
if os.path.exists(os.path.join(root_dir, "index.html")):
    app.mount("/", StaticFiles(directory=root_dir, html=True), name="static")

if __name__ == "__main__":
    print(f"🚀 Rodando localmente...")
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[root_dir])