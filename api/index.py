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
# 2. SELEÇÃO INTELIGENTE (PRIORIDADE: FLASH LATEST)
# =====================================================
def pick_any_working_model(api_key):
    print("🔍 Baixando lista de modelos da sua conta...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "models" not in data:
            return "gemini-1.5-flash"

        # Lista limpa de nomes
        all_models = [m['name'].replace("models/", "") for m in data['models']]
        print(f"📋 SUA LISTA (Resumo): {all_models[:5]}...") # Mostra só os 5 primeiros

        # === AQUI ESTÁ A REGRA DE OURO ===
        # 1. Tenta o alias de produção (Mais estável de todos)
        if "gemini-flash-latest" in all_models:
            print("✅ ESCOLHIDO (GOLD): gemini-flash-latest")
            return "gemini-flash-latest"
            
        # 2. Tenta o 1.5 Flash (O tanque de guerra)
        if "gemini-1.5-flash" in all_models:
            print("✅ ESCOLHIDO (SILVER): gemini-1.5-flash")
            return "gemini-1.5-flash"

        # 3. Tenta o 2.0 Flash (Novo, rápido)
        if "gemini-2.0-flash" in all_models:
             print("✅ ESCOLHIDO (BRONZE): gemini-2.0-flash")
             return "gemini-2.0-flash"

        # 4. Se não tiver nenhum desses, pega o primeiro que não seja 2.5 (Cota Zero)
        for m in all_models:
            if "2.5" not in m and "preview" not in m and "exp" not in m:
                print(f"✅ ESCOLHIDO (FALLBACK): {m}")
                return m

        # Se tudo falhar, tenta o flash latest na sorte
        return "gemini-flash-latest"

    except Exception as e:
        print(f"⚠️ Erro na seleção: {e}")
        return "gemini-1.5-flash"

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
    
    # URL final
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=20)
    
    if response.status_code == 200: 
        return response.json()
    
    raise Exception(f"Erro {response.status_code}: {response.text}")

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Tema: {request.user_interest}")
    
    # MOCK DE APRESENTAÇÃO (Para não travar no palco)
    fallback = (
        f"Olha só, imagina que essa lei funciona igualzinho a {request.user_interest}. "
        "Basicamente, ela cria regras pra organizar a casa e garantir que ninguém saia perdendo. "
        "É tipo aquele regulamento que existe pra coisa funcionar direito e proteger todo mundo!"
    )

    if not API_KEY: return { "explanation": fallback }

    try:
        prompt = f"""
        ATUE COMO LOCUTOR POPULAR BRASILEIRO.
        Explicar lei: "{request.pl_text}"
        Analogia: "{request.user_interest}"
        Texto curto falado (max 3 parágrafos).
        RETORNE APENAS JSON: {{ "explanation": "texto..." }}
        """
        
        model_final = ACTIVE_MODEL if ACTIVE_MODEL else "gemini-flash-latest"
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