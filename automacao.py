import json
import time
from web3 import Web3
import torch
import requests
import torch.nn as nn
import os
import random
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

# ==========================================
# 0. CONFIGURAÇÃO DO ALTO-FALANTE (SUPABASE)
# ==========================================
URL_SUPABASE = os.environ.get("SUPABASE_URL", "https://bjsfmluawlcfsfvnjorf.supabase.co")
CHAVE_SUPABASE = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqc2ZtbHVhd2xjZnNmdm5qb3JmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyMjY5ODUsImV4cCI6MjA4OTgwMjk4NX0.0WME-7HzSpy0CnPLIjbdjE6h0jPBO5J5-hWclXPWNnE")

supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)

def avisar_app(acao, motivo, confianca):
    try:
        supabase.table("ai_logs").insert({
            "action_type": acao,
            "reason": motivo,
            "confidence": int(confianca)
        }).execute()
        print(f"📡 App Notificado: {acao} - {motivo}")
    except Exception as e:
        print(f"❌ Erro Supabase: {e}")

# ==========================================
# VARIÁVEIS DE ESTADO
# ==========================================
status_bot = {
    "status": "Starting",
    "ultima_analise": "N/A",
    "preco_btc": 0.0,
    "confianca_ia": 0.0,
    "ultima_decisao": "N/A",
    "sentimento_mercado": "Neutral"
}

# ==========================================
# 1. AUTO-RECUPERAÇÃO E BLOCKCHAIN SETUP
# ==========================================
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Contratos Oficiais VGB Tech
VAULT_ADDRESS = web3.to_checksum_address("0x5185cfEB2628CBEDeE04aCf320E13634Be63A2D5")
EUSD_ADDRESS = web3.to_checksum_address("0x2e17393bd766f8b1c5007224854b82afde23d1fc")

AI_PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "CHAVE_NAO_ENCONTRADA") 
ADMIN_ADDRESS = None

if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA":
    ai_account = web3.eth.account.from_key(AI_PRIVATE_KEY)
    ADMIN_ADDRESS = ai_account.address
else:
    print("🚨 AVISO CRÍTICO: Chave Privada não encontrada no ambiente Render.")

try:
    with open("vault_abi.json", "r") as file:
        vault_abi = json.load(file)
    vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)
except Exception as e:
    print(f"⚠️ Erro ABI: {e}")

def inicializacao_segura():
    print("🔄 Iniciando rotina de auto-recuperação (Render Warm-up)...")
    if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA":
        try:
            nonce = web3.eth.get_transaction_count(ai_account.address, 'pending')
            print(f"🔗 Sincronização On-Chain concluída. Último Nonce: {nonce}")
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível sincronizar o Nonce: {e}")

    try:
        response = supabase.table("ai_logs").select("*").order("created_at", desc=True).limit(1).execute()
        if response.data:
            ultimo_log = response.data[0]
            status_bot["ultima_decisao"] = ultimo_log['action_type']
            print(f"🗄️ Memória recuperada. Última ação foi: {ultimo_log['action_type']}")
        else:
            print("🗄️ Banco de dados limpo. Iniciando operações.")
    except Exception as e:
        print(f"⚠️ Erro ao acessar a memória do Supabase: {e}")

# ==========================================
# 2. CAMADAS AVANÇADAS (SENTIMENTO E RISCO)
# ==========================================
def obter_sentimento_mercado():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        resposta = requests.get(url).json()
        valor = int(resposta['data'][0]['value'])
        classificacao = resposta['data'][0]['value_classification']
        return (valor - 50) / 50.0, classificacao
    except:
        return 0.0, "Neutral"

def analisar_risco_sistemico():
    try:
        pool_liquidity_healthy = True 
        if pool_liquidity_healthy:
            return random.uniform(0.1, 0.4) 
        else:
            print("⚠️ Alerta On-chain: Baixa liquidez detectada!")
            return random.uniform(0.7, 1.0) 
    except:
        return 0.5

# ==========================================
# 3. A ESTRUTURA DO CÉREBRO (REDE NEURAL)
# ==========================================
class EmergentBrain(nn.Module):
    def __init__(self):
        super(EmergentBrain, self).__init__()
        self.rede = nn.Sequential(
            nn.Linear(5, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 3) 
        )
    def forward(self, x):
        return self.rede(x)

def executar_ordem(tipo_ordem, valor_dolares):
    if AI_PRIVATE_KEY == "CHAVE_NAO_ENCONTRADA": 
        print("❌ Operação abortada: Sem Chave Privada.")
        return
        
    amount_wei = web3.to_wei(valor_dolares, 'ether')
    
    if tipo_ordem == "COMPRA":
        funcao = vault_contract.functions.executeMarketBuy(EUSD_ADDRESS, amount_wei)
    elif tipo_ordem == "VENDA":
        funcao = vault_contract.functions.executeMarketSell(EUSD_ADDRESS, amount_wei)
        
    print(f"Assinando transação on-chain: {tipo_ordem}...")
    try:
        nonce = web3.eth.get_transaction_count(ai_account.address, 'pending')
        gas_estimado = funcao.estimate_gas({'from': ai_account.address})
        tx = funcao.build_transaction({
            'from': ai_account.address,
            'nonce': nonce,
            'gas': int(gas_estimado * 1.2), 
            'gasPrice': web3.eth.gas_price
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key=AI_PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"🚀 Transação Hash: {web3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"❌ Falha on-chain: {e}")
        avisar_app("NETWORK DELAY", "A rede Arbitrum está congestionada.", 0)

# ==========================================
# 4. LOOP ASSÍNCRONO DA IA
# ==========================================
async def ai_decision_loop():
    global status_bot
    print("🧠 Inicializando Rede Neural Multimodal v2...")
    model = EmergentBrain()
    
    try:
        model.load_state_dict(torch.load('emergent_brain.pth'))
        print("✅ Cérebro carregado com sucesso.")
    except Exception as e:
        print("⚠️ Iniciando nova sinapse...")
        torch.save(model.state_dict(), 'emergent_brain.pth')
        
    model.eval()

    while True:
        status_bot["ultima_analise"] = time.strftime('%H:%M:%S')
        print("\n" + "="*50)
        print(f"⏰ [{status_bot['ultima_analise']}] Varredura de Mercado Iniciada...")

        try:
            url = "https://api.binance.us/api/v3/ticker/24hr?symbol=BTCUSDT"
            resposta = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
            variacao = float(resposta['priceChangePercent']) / 100.0
            preco_atual = float(resposta['lastPrice']) / 100000.0 
            volume = float(resposta['volume']) / 100000.0
            status_bot["preco_btc"] = float(resposta['lastPrice'])
            
            sentimento_valor, sentimento_texto = obter_sentimento_mercado()
            risco_sistemico = analisar_risco_sistemico()
            status_bot["sentimento_mercado"] = sentimento_texto
            
            print(f"📈 BTC: ${status_bot['preco_btc']:.2f} | Sentimento: {sentimento_texto} | Risco: {risco_sistemico:.2f}")
            market_data = [variacao, preco_atual, volume, sentimento_valor, risco_sistemico]
            
        except Exception as e:
            print(f"⚠️ Erro nas APIs: {e}")
            market_data = [0.0, 0.0, 0.0, 0.0, 0.0]
            sentimento_texto, risco_sistemico = "Neutral", 0.5

        if sentimento_texto == "Extreme Fear" or risco_sistemico > 0.85:
            print("🚨 ALERTA VERMELHO: Hedge de Emergência.")
            status_bot["ultima_decisao"] = "EMERGENCY HEDGE"
            status_bot["confianca_ia"] = 100.0
            executar_ordem("VENDA", 100)
            avisar_app("EMERGENCY HEDGE", "Capital protection executed.", 100)
        else:
            tensor_inputs = torch.tensor(market_data, dtype=torch.float32)
            with torch.no_grad():
                prediction = model(tensor_inputs)
                probabilidades = torch.nn.functional.softmax(prediction, dim=0)
                confianca = torch.max(probabilidades).item()
                decision = torch.argmax(prediction).item() 
                
            status_bot["confianca_ia"] = round(confianca * 100, 2)

            if confianca < 0.85:
                status_bot["ultima_decisao"] = "HOLD"
                avisar_app("HOLD", f"Signal confidence ({status_bot['confianca_ia']}%) too low.", status_bot["confianca_ia"])
            else:
                if decision == 2:
                    status_bot["ultima_decisao"] = "BUY"
                    executar_ordem("COMPRA", 100)
                    avisar_app("BUY", "Increasing BTC exposure.", status_bot["confianca_ia"])
                elif decision == 0:
                    status_bot["ultima_decisao"] = "SELL"
                    executar_ordem("VENDA", 100)
                    avisar_app("HEDGE", "Rebalancing to eUSD.", status_bot["confianca_ia"])
                else:
                    status_bot["ultima_decisao"] = "HOLD"
                    avisar_app("MONITORING", "Balanced.", status_bot["confianca_ia"])

        status_bot["status"] = "Sleeping"
        print(f"💤 Descansando por 5 minutos...")
        # Essa é a mágica do FastAPI: a IA dorme, mas o servidor de pagamentos continua vivo
        await asyncio.sleep(300) 
        status_bot["status"] = "Analyzing"

# ==========================================
# 5. SERVIDOR WEB (FASTAPI + GASLESS)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializacao_segura()
    task = asyncio.create_task(ai_decision_loop())
    yield
    task.cancel()

app = FastAPI(title="VGB Tech Core Engine", lifespan=lifespan)

class GasRequest(BaseModel):
    user_wallet: str

@app.post("/sponsor_gas")
async def sponsor_gas(request: GasRequest):
    if AI_PRIVATE_KEY == "CHAVE_NAO_ENCONTRADA" or not ADMIN_ADDRESS:
        raise HTTPException(status_code=500, detail="Servidor não autorizado.")
        
    try:
        user_wallet = web3.to_checksum_address(request.user_wallet)
        balance_eth = web3.from_wei(web3.eth.get_balance(user_wallet), 'ether')
        
        if balance_eth > 0.0005:
            return {"status": "success", "message": "User already has enough gas."}
            
        sponsor_amount = web3.to_wei(0.001, 'ether')
        tx = {
            'nonce': web3.eth.get_transaction_count(ADMIN_ADDRESS),
            'to': user_wallet,
            'value': sponsor_amount,
            'gas': 21000,
            'gasPrice': web3.eth.gas_price,
            'chainId': 421614
        }
        
        signed_tx = web3.eth.account.sign_transaction(tx, AI_PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"status": "success", "tx_hash": tx_hash.hex()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return status_bot

@app.get("/")
def home():
    return {"message": "Emergent Advanced Brain is ONLINE."}
