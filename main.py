import uvicorn
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import re

# =====================================================
# 1. CONFIGURAÇÃO
# =====================================================
# COLE SUA CHAVE ABAIXO (DENTRO DAS ASPAS):
API_KEY = "AIzaSyDxT9wy69iYt8msIO3375wgSV8KikAvUiw" 

if API_KEY == "COLE_SUA_CHAVE_AQUI":
    print("⚠️ ATENÇÃO: Você esqueceu de colocar a API Key na linha 13 do main.py!")

genai.configure(api_key=API_KEY)

# =====================================================
# 2. SERVIDOR & UTILITÁRIOS
# =====================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seleção automática do melhor modelo disponível
def get_best_model():
    priority_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"]
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for model_name in priority_models:
            for available in available_models:
                if model_name in available:
                    print(f"✅ Modelo Selecionado: {available}")
                    return available
    except:
        pass
    return "models/gemini-pro" # Fallback

active_model = get_best_model()
model = genai.GenerativeModel(active_model)

class ExplainRequest(BaseModel):
    pl_text: str
    user_interest: str

# =====================================================
# 3. ROTA DE GERAÇÃO (MODO LOCUTOR / ÁUDIO)
# =====================================================
@app.post("/explain")
async def explain_law(request: ExplainRequest):
    print(f"📥 Gerando explicação em áudio sobre: {request.user_interest}...")
    
    try:
        # PROMPT FOCADO EM ORATÓRIA (TEXT-TO-SPEECH)
        # Removemos a parte de imagem para focar na qualidade do texto falado.
        prompt = f"""
        ATUE COMO UM LOCUTOR DE RÁDIO POPULAR E CARISMÁTICO.
        
        CONTEXTO:
        Você precisa explicar a lei técnica: "{request.pl_text}"
        Para um cidadão comum, usando uma analogia com: "{request.user_interest}".

        TAREFA:
        Escreva um roteiro curto (máximo 3 parágrafos) que será LIDO EM VOZ ALTA por um sintetizador de voz.
        
        REGRAS DE ESTILO (CRUCIAL):
        1. Use linguagem falada e direta (Ex: "Olha só...", "Imagina que...", "Sabe quando...").
        2. Mantenha a analogia do tema "{request.user_interest}" durante toda a explicação.
        3. NÃO use listas, tópicos ou caracteres especiais (*, -). Escreva como uma conversa fluida.
        4. Termine com uma frase de impacto sobre como isso muda a vida da pessoa.

        RETORNE APENAS ESTE JSON (SEM MARKDOWN):
        {{
            "explanation": "O texto da explicação aqui..."
        }}
        """

        response = model.generate_content(prompt)
        texto_bruto = response.text

        # Limpeza de JSON
        texto_limpo = re.sub(r"```json|```", "", texto_bruto).strip()
        
        try:
            return json.loads(texto_limpo)
        except json.JSONDecodeError:
            # Se der erro no JSON, retorna o texto puro no campo correto
            return {
                "explanation": texto_limpo
            }

    except Exception as e:
        print(f"❌ Erro Crítico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)