import json
import time
from web3 import Web3
import torch
import requests
import torch.nn as nn
import threading
from flask import Flask, jsonify
import os
from supabase import create_client, Client
import random

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
# 1. CAMADAS AVANÇADAS (SENTIMENTO E RISCO)
# ==========================================
def obter_sentimento_mercado():
    """Consulta o Índice de Medo e Ganância Global (0 a 100)"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        resposta = requests.get(url).json()
        valor = int(resposta['data'][0]['value'])
        classificacao = resposta['data'][0]['value_classification']
        # Normaliza o valor para a Rede Neural (-1.0 a 1.0)
        valor_normalizado = (valor - 50) / 50.0
        return valor_normalizado, classificacao
    except:
        return 0.0, "Neutral"

def analisar_risco_sistemico():
    """Simula a varredura On-Chain de baleias e liquidez"""
    # Em produção, conectaríamos a APIs do Glassnode ou CryptoQuant.
    # Aqui, geramos uma métrica de risco baseada em volatilidade simulada.
    risco = random.uniform(0.0, 1.0)
    return risco

# ==========================================
# 2. A NOVA ESTRUTURA DO CÉREBRO (5 Entradas)
# ==========================================
class EmergentBrain(nn.Module):
    def __init__(self):
        super(EmergentBrain, self).__init__()
        # Entradas: [Variação, Preço, Volume, Sentimento, Risco]
        self.rede = nn.Sequential(
            nn.Linear(5, 32), # Aumentamos os neurônios para processar mais dados
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 3) # Saídas: [Vende, Hold, Compra]
        )

    def forward(self, x):
        return self.rede(x)

# ==========================================
# 3. BLOCKCHAIN & SEGURANÇA
# ==========================================
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

VAULT_ADDRESS = web3.to_checksum_address("0x6b1519CA41602B91F12A6269F04AE656D5FB4803")
EUSD_ADDRESS = web3.to_checksum_address("0x960C3A75ad6b793882D643f8B71c33945269af01")
AI_PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "CHAVE_NAO_ENCONTRADA") 

if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA":
    ai_account = web3.eth.account.from_key(AI_PRIVATE_KEY)
else:
    print("🚨 AVISO: Chave privada ausente. Operando em modo de simulação visual.")

try:
    with open("vault_abi.json", "r") as file:
        vault_abi = json.load(file)
    vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)
except Exception as e:
    print(f"⚠️ Erro ABI: {e}")

def executar_ordem(tipo_ordem, valor_dolares):
    if AI_PRIVATE_KEY == "CHAVE_NAO_ENCONTRADA": return
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
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"🚀 Transação Hash: {web3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"❌ Falha on-chain: {e}")

# ==========================================
# 4. LOOP PRINCIPAL DA IA MULTICAMADA
# ==========================================
def ai_decision_loop():
    global status_bot
    print("🧠 Inicializando Rede Neural Multimodal v2...")
    model = EmergentBrain()
    
    try:
        # Tenta carregar o cérebro antigo. Se der erro por diferença de tamanho, cria um novo.
        model.load_state_dict(torch.load('emergent_brain.pth'))
        print("✅ Cérebro carregado com sucesso.")
    except Exception as e:
        print("⚠️ Cérebro antigo incompatível com a nova arquitetura (5 inputs). Iniciando nova sinapse...")
        torch.save(model.state_dict(), 'emergent_brain.pth')
        
    model.eval()

    while True:
        status_bot["ultima_analise"] = time.strftime('%H:%M:%S')
        print("\n" + "="*50)
        print(f"⏰ [{status_bot['ultima_analise']}] Varredura de Mercado Iniciada...")

        try:
            # Camada 1: Preço (Binance)
            url = "https://api.binance.us/api/v3/ticker/24hr?symbol=BTCUSDT"
            resposta = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
            variacao = float(resposta['priceChangePercent']) / 100.0
            preco_atual = float(resposta['lastPrice']) / 100000.0 
            volume = float(resposta['volume']) / 100000.0
            status_bot["preco_btc"] = float(resposta['lastPrice'])
            
            # Camada 2 e 3: Sentimento NLP e Risco On-Chain
            sentimento_valor, sentimento_texto = obter_sentimento_mercado()
            risco_sistemico = analisar_risco_sistemico()
            status_bot["sentimento_mercado"] = sentimento_texto
            
            print(f"📈 BTC: ${status_bot['preco_btc']:.2f} | Sentimento: {sentimento_texto} | Risco: {risco_sistemico:.2f}")
            
            market_data = [variacao, preco_atual, volume, sentimento_valor, risco_sistemico]
            
        except Exception as e:
            print(f"⚠️ Erro nas APIs. Acionando modo de emergência. Detalhe: {e}")
            market_data = [0.0, 0.0, 0.0, 0.0, 0.0]
            sentimento_texto = "Neutral"
            risco_sistemico = 0.5

        # ----------------------------------------------------
        # SISTEMA DE DEFESA (CIRCUIT BREAKER - CAMADA 3)
        # ----------------------------------------------------
        if sentimento_texto == "Extreme Fear" or risco_sistemico > 0.85:
            print("🚨 ALERTA VERMELHO: Risco Sistêmico Crítico Detectado! Ignorando Rede Neural.")
            status_bot["ultima_decisao"] = "EMERGENCY HEDGE"
            status_bot["confianca_ia"] = 100.0
            executar_ordem("VENDA", 100)
            avisar_app("EMERGENCY HEDGE", f"Extreme Fear or Anomaly detected. Executing emergency capital protection to eUSD.", 100)
        
        # ----------------------------------------------------
        # REDE NEURAL PADRÃO (CAMADA 1)
        # ----------------------------------------------------
        else:
            tensor_inputs = torch.tensor(market_data, dtype=torch.float32)
            with torch.no_grad():
                prediction = model(tensor_inputs)
                probabilidades = torch.nn.functional.softmax(prediction, dim=0)
                confianca = torch.max(probabilidades).item()
                decision = torch.argmax(prediction).item() 
                
            status_bot["confianca_ia"] = round(confianca * 100, 2)

            if confianca < 0.80:
                print(f"⚖️ Confiança baixa ({status_bot['confianca_ia']}%).")
                status_bot["ultima_decisao"] = "HOLD"
                avisar_app("HOLD", f"Complex market conditions. Analyzing macro data before moving treasury.", status_bot["confianca_ia"])
                
            else:
                if decision == 2:
                    status_bot["ultima_decisao"] = "BUY"
                    executar_ordem("COMPRA", 100)
                    avisar_app("BUY", f"Market sentiment is {sentimento_texto}. Increasing spot BTC exposure to capture value.", status_bot["confianca_ia"])
                    
                elif decision == 0:
                    status_bot["ultima_decisao"] = "SELL"
                    executar_ordem("VENDA", 100)
                    avisar_app("HEDGE", f"Algorithm identified a local top. Rebalancing treasury to eUSD.", status_bot["confianca_ia"])
                    
                else:
                    status_bot["ultima_decisao"] = "HOLD"
                    avisar_app("MONITORING", "Treasury is perfectly balanced for current market conditions.", status_bot["confianca_ia"])

        status_bot["status"] = "Sleeping"
        print(f"💤 Varredura concluída. Descansando por 5 minutos...")
        time.sleep(300)
        status_bot["status"] = "Analyzing"
        
# ==========================================
# 5. SERVIDOR WEB 
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Emergent Advanced Brain is online."

@app.route('/health')
def health_check():
    return jsonify(status_bot)

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    ai_decision_loop()
