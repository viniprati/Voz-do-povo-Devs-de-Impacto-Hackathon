import os
import sys
import uvicorn
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import re
from contextlib import asynccontextmanager

# =====================================================
# 1. SETUP
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
# 2. SELEÇÃO INTELIGENTE (PEGA O QUE TIVER)
# =====================================================
def pick_any_working_model(api_key):
    print("🔍 Baixando lista de modelos da sua conta...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "models" not in data:
            print("⚠️ Lista vazia. Usando fallback seguro.")
            return "gemini-1.5-flash-8b"

        # Lista todos os modelos encontrados no console para a gente ver
        all_models = [m['name'].replace("models/", "") for m in data['models']]
        print(f"📋 MODELOS DISPONÍVEIS NA SUA CONTA: {all_models}")

        # FILTRO: Pega o primeiro que gere texto e não seja o 2.5 (que tem cota zero)
        for m in data['models']:
            name = m['name'].replace("models/", "")
            methods = m.get('supportedGenerationMethods', [])
            
            if "generateContent" in methods:
                # Pula modelos experimentais que travam conta grátis
                if "2.5" in name or "preview" in name or "exp" in name:
                    continue
                
                # ACHOU UM BOM!
                print(f"✅ ESCOLHIDO AUTOMATICAMENTE: {name}")
                return name

        # Se não sobrou nada, tenta o 8b que é o mais leve de todos
        return "gemini-1.5-flash-8b"

    except Exception as e:
        print(f"⚠️ Erro na seleção: {e}")
        return "gemini-1.5-flash-8b"

# =====================================================
# 3. INICIALIZAÇÃO
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global ACTIVE_MODEL
    print("✅ SERVIDOR ONLINE.")
    if API_KEY:
        print(f"🔑 Chave: ...{API_KEY[-4:]}")
        ACTIVE_MODEL = pick_any_working_model(API_KEY)
    else:
        print("⚠️ SEM CHAVE.")
    yield

app = FastAPI(title="Voz do Povo API", docs_url="/api/docs", openapi_url="/api/openapi.json", lifespan=lifespan)

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
# 4. CHAMADA API
# =====================================================
def call_gemini(prompt, api_key, model):
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    # Usa o modelo que escolhemos dinamicamente
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200: 
        return response.json()
    
    raise Exception(f"Erro {response.status_code}: {response.text}")

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Tema: {request.user_interest}")
    
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
        
        # Usa o modelo descoberto ou o 8b como fallback
        model_final = ACTIVE_MODEL if ACTIVE_MODEL else "gemini-1.5-flash-8b"
        data = call_gemini(prompt, API_KEY, model_final)
        
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
            clean_text = re.sub(r"```json|```", "", text).strip()
            try: return json.loads(clean_text)
            except: return { "explanation": clean_text }
        except:
            return { "explanation": fallback }
            
    except Exception as e:
        print(f"⚠️ Erro API ({e}). Usando Mock.")
        return { "explanation": fallback }

@app.post("/send_feedback")
async def send_email(feedback: FeedbackRequest):
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