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
# 1. AJUSTE DE CAMINHOS (CRUCIAL PARA NOVA ESTRUTURA)
# =====================================================
# Descobre onde está a raiz do projeto (uma pasta acima da 'api')
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# Tenta carregar .env da raiz
try:
    load_dotenv(os.path.join(root_dir, ".env"))
except:
    pass

API_KEY = os.getenv("GOOGLE_API_KEY")
ACTIVE_MODEL = None

# =====================================================
# 2. AUTO-CONFIGURAÇÃO
# =====================================================
def find_best_model(api_key):
    """Descobre qual modelo a chave aceita para evitar erro 404"""
    print("🔍 Buscando modelos disponíveis...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if "error" in data: return None
        
        # Procura Flash ou Pro
        for model in data.get('models', []):
            if "generateContent" in model.get('supportedGenerationMethods', []):
                name = model['name'].replace("models/", "")
                if "flash" in name or "pro" in name:
                    print(f"✅ MODELO SELECIONADO: {name}")
                    return name
        return "gemini-1.5-flash"
    except:
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
        ACTIVE_MODEL = find_best_model(API_KEY)
        if not ACTIVE_MODEL: ACTIVE_MODEL = "gemini-1.5-flash"
    else:
        print("⚠️ SEM CHAVE: Modo Simulação Ativo.")
    yield

app = FastAPI(
    title="Voz do Povo API",
    docs_url="/api/docs", # Ajuste para documentação funcionar na subpasta
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
# 4. LÓGICA DA IA (COM FALLBACK)
# =====================================================
def call_gemini(prompt, api_key, model):
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    if response.status_code == 200: return response.json()
    raise Exception(f"Erro {response.status_code}")

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Tema: {request.user_interest}")
    
    # Texto de emergência (Mock)
    fallback = (
        f"Olha só, imagina que essa lei funciona igualzinho a {request.user_interest}. "
        "Tem regras pra tudo funcionar bem e proteger quem participa. "
        "No final, é pra garantir que o jogo seja justo pra todo mundo!"
    )

    if not API_KEY: return { "explanation": fallback }

    try:
        prompt = f"""
        ATUE COMO LOCUTOR POPULAR.
        Explicar lei: "{request.pl_text}"
        Analogia: "{request.user_interest}"
        Texto curto (max 3 parágrafos).
        RETORNE APENAS JSON: {{ "explanation": "texto..." }}
        """
        
        data = call_gemini(prompt, API_KEY, ACTIVE_MODEL)
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
            clean_text = re.sub(r"```json|```", "", text).strip()
            try: return json.loads(clean_text)
            except: return { "explanation": clean_text }
        except:
            return { "explanation": fallback }
            
    except Exception as e:
        print(f"⚠️ Falha na API: {e}")
        return { "explanation": fallback }

@app.post("/send_feedback")
async def send_email(feedback: FeedbackRequest):
    print(f"📧 Feedback: {feedback.author_name}")
    return { "status": "success" }

@app.get("/health")
async def health():
    return {"status": "ok", "structure": "api_folder"}

# =====================================================
# 5. SERVIR ARQUIVOS ESTÁTICOS (LOCALHOST APENAS)
# =====================================================
# O Vercel serve os estáticos sozinho. Isso aqui é só para quando você roda no PC.
if os.path.exists(os.path.join(root_dir, "index.html")):
    app.mount("/", StaticFiles(directory=root_dir, html=True), name="static")

# Bloco de execução local
if __name__ == "__main__":
    print(f"🚀 Rodando localmente na porta 8000...")
    # Importante: recarrega apenas se mudar arquivos na api ou raiz
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[root_dir])