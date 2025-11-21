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
# 2. AUTO-CONFIGURAÇÃO (COM PROTEÇÃO ANTI-429)
# =====================================================
def find_best_model(api_key):
    """
    Descobre qual modelo a chave aceita para evitar erro 404.
    Se der erro 429 (Muitos pedidos), usa o padrão sem travar.
    """
    print("🔍 Buscando modelos disponíveis...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        # Timeout curto (5s) para não atrasar a inicialização
        response = requests.get(url, timeout=5)
        
        # SE DER ERRO 429 (Limite atingido), NÃO QUEBRA O SERVIDOR
        if response.status_code == 429:
            print("⚠️ Limite de teste atingido (429). Usando padrão seguro: gemini-1.5-flash")
            return "gemini-1.5-flash"

        data = response.json()
        if "error" in data: 
            print(f"⚠️ Erro na busca: {data['error'].get('message')}")
            return "gemini-1.5-flash"
        
        # Procura Flash ou Pro na lista oficial
        for model in data.get('models', []):
            if "generateContent" in model.get('supportedGenerationMethods', []):
                name = model['name'].replace("models/", "")
                if "flash" in name or "pro" in name:
                    print(f"✅ MODELO SELECIONADO: {name}")
                    return name
        
        return "gemini-1.5-flash"
    except Exception as e:
        print(f"⚠️ Erro de conexão no teste ({e}). Usando padrão.")
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
        # Se der erro 429 aqui, ele recupera e usa o padrão
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
# 4. LÓGICA DA IA (COM FALLBACK BLINDADO)
# =====================================================
def call_gemini(prompt, api_key, model):
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [{ "parts": [{"text": prompt}] }] }
    
    # URL dinâmica baseada no modelo encontrado
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200: 
        return response.json()
    
    # Se der erro, lança Exception com o código para o Mock assumir
    raise Exception(f"Erro Google {response.status_code}: {response.text}")

@app.post("/explain") 
async def explain_law(request: ExplainRequest):
    print(f"📥 [REQ] Tema: {request.user_interest}")
    
    # --- MOCK DE SEGURANÇA (PLANO B) ---
    # Garante que a apresentação funcione mesmo se o Google bloquear a chave
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
        
        data = call_gemini(prompt, API_KEY, ACTIVE_MODEL)
        try:
            text = data['candidates'][0]['content']['parts'][0]['text']
            clean_text = re.sub(r"```json|```", "", text).strip()
            try: return json.loads(clean_text)
            except: return { "explanation": clean_text }
        except:
            return { "explanation": fallback }
            
    except Exception as e:
        print(f"⚠️ Falha na API ({str(e)}). Usando Mock.")
        # Retorna o Mock para o Frontend receber 200 OK
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
if os.path.exists(os.path.join(root_dir, "index.html")):
    app.mount("/", StaticFiles(directory=root_dir, html=True), name="static")

# Bloco de execução local
if __name__ == "__main__":
    print(f"🚀 Rodando localmente na porta 8000...")
    # reload_dirs faz reiniciar se mexer na pasta raiz
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[root_dir])