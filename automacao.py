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

# ==========================================
# 0. CONFIGURAÇÃO DO ALTO-FALANTE (SUPABASE)
# ==========================================
URL_SUPABASE = os.environ.get("SUPABASE_URL", "https://bjsfmluawlcfsfvnjorf.supabase.co")
CHAVE_SUPABASE = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqc2ZtbHVhd2xjZnNmdm5qb3JmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQyMjY5ODUsImV4cCI6MjA4OTgwMjk4NX0.0WME-7HzSpy0CnPLIjbdjE6h0jPBO5J5-hWclXPWNnE")

supabase: Client = create_client(URL_SUPABASE, CHAVE_SUPABASE)

def avisar_app(acao, motivo, confianca):
    """Função que envia a decisão da IA direto para a tela do celular do usuário"""
    try:
        supabase.table("ai_logs").insert({
            "action_type": acao,
            "reason": motivo,
            "confidence": int(confianca)
        }).execute()
        print(f"📡 App notificado via Supabase: {acao} - {motivo}")
    except Exception as e:
        print(f"❌ Erro ao notificar o App: {e}")

# ==========================================
# VARIÁVEIS DE ESTADO (Para o painel /health do Flask)
# ==========================================
status_bot = {
    "status": "Starting",
    "ultima_analise": "N/A",
    "preco_btc": 0.0,
    "confianca_ia": 0.0,
    "ultima_decisao": "N/A"
}

# ==========================================
# 1. A ESTRUTURA DO CÉREBRO (PYTORCH)
# ==========================================
class EmergentBrain(nn.Module):
    def __init__(self):
        super(EmergentBrain, self).__init__()
        self.rede = nn.Sequential(
            nn.Linear(3, 24),
            nn.ReLU(),
            nn.Linear(24, 24),
            nn.ReLU(),
            nn.Linear(24, 3)
        )

    def forward(self, x):
        return self.rede(x)

# ==========================================
# 2. CONFIGURAÇÕES DA BLOCKCHAIN & SEGURANÇA
# ==========================================
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

VAULT_ADDRESS = web3.to_checksum_address("0x6b1519CA41602B91F12A6269F04AE656D5FB4803")
EUSD_ADDRESS = web3.to_checksum_address("0x960C3A75ad6b793882D643f8B71c33945269af01")

AI_PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "CHAVE_NAO_ENCONTRADA") 

if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA":
    ai_account = web3.eth.account.from_key(AI_PRIVATE_KEY)
else:
    print("🚨 ERRO CRÍTICO: Chave privada não encontrada nas Variáveis de Ambiente!")

try:
    with open("vault_abi.json", "r") as file:
        vault_abi = json.load(file)
    vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)
except Exception as e:
    print(f"⚠️ Erro ao carregar vault_abi.json: {e}")

# ==========================================
# 3. FUNÇÕES DE EXECUÇÃO ON-CHAIN
# ==========================================
def executar_ordem(tipo_ordem, valor_dolares):
    amount_wei = web3.to_wei(valor_dolares, 'ether')
    
    if tipo_ordem == "COMPRA":
        funcao = vault_contract.functions.executeMarketBuy(EUSD_ADDRESS, amount_wei)
    elif tipo_ordem == "VENDA":
        funcao = vault_contract.functions.executeMarketSell(EUSD_ADDRESS, amount_wei)
        
    print(f"Assinando transação de {tipo_ordem} de ${valor_dolares}...")
    
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
        
        print(f"🚀 Enviado! Hash: {web3.to_hex(tx_hash)}")
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print("✅ Transação confirmada na blockchain!")
        
    except Exception as e:
        print(f"❌ Falha na transação Web3: {e}")

# ==========================================
# 4. O LOOP PRINCIPAL DA IA
# ==========================================
def ai_decision_loop():
    global status_bot
    print("🧠 Inicializando Rede Neural...")
    model = EmergentBrain()
    
    try:
        model.load_state_dict(torch.load('emergent_brain.pth'))
        print("✅ Cérebro carregado. Iniciando patrulha de mercado.")
    except:
        print("⚠️ Arquivo .pth não encontrado. Usando pesos aleatórios para teste.")
        
    model.eval()

    while True:
        status_bot["ultima_analise"] = time.strftime('%H:%M:%S')
        print("\n" + "="*40)
        print(f"⏰ [{status_bot['ultima_analise']}] Iniciando ciclo de análise...")

        try:
            url = "https://api.binance.us/api/v3/ticker/24hr?symbol=BTCUSDT"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resposta = requests.get(url, headers=headers).json()
            
            variacao = float(resposta['priceChangePercent']) / 100.0
            preco_atual = float(resposta['lastPrice']) / 100000.0 
            volume = float(resposta['volume']) / 100000.0
            
            market_data = [variacao, preco_atual, volume]
            status_bot["preco_btc"] = float(resposta['lastPrice'])
            print(f"📈 Preço BTC: ${status_bot['preco_btc']:.2f} | Variação: {resposta['priceChangePercent']}%")
            
        except Exception as e:
            print(f"⚠️ Erro ao ler a Binance US ({e}). Usando dados de emergência.")
            market_data = [0.0, 0.0, 0.0]

        tensor_inputs = torch.tensor(market_data, dtype=torch.float32)

        with torch.no_grad():
            prediction = model(tensor_inputs)
            probabilidades = torch.nn.functional.softmax(prediction, dim=0)
            confianca = torch.max(probabilidades).item()
            decision = torch.argmax(prediction).item() 
            
        status_bot["confianca_ia"] = round(confianca * 100, 2)

        # TRAVA DE CONFIANÇA (Threshold de 85%)
        if confianca < 0.85:
            print(f"⚖️ Confiança muito baixa ({status_bot['confianca_ia']}%). A IA prefere MANTER (Hold) por segurança.")
            status_bot["ultima_decisao"] = "HOLD"
            
            # IA AVISA O APP EM INGLÊS:
            avisar_app("HOLD", f"Low market confidence ({status_bot['confianca_ia']}%). Waiting for clearer signals to operate.", status_bot["confianca_ia"])
            
        else:
            if decision == 2:
                print(f"📈 Decisão da IA: COMPRAR (Confiança: {status_bot['confianca_ia']}%)")
                status_bot["ultima_decisao"] = "BUY"
                
                if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA": executar_ordem("COMPRA", 100)
                
                # IA AVISA O APP EM INGLÊS:
                avisar_app("BUY", f"Strong bullish signal on BTC at ${status_bot['preco_btc']:.2f}. Increasing spot market exposure.", status_bot["confianca_ia"])
                
            elif decision == 0:
                print(f"📉 Decisão da IA: VENDER (Confiança: {status_bot['confianca_ia']}%)")
                status_bot["ultima_decisao"] = "SELL"
                
                if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA": executar_ordem("VENDA", 100)
                
                # IA AVISA O APP EM INGLÊS:
                avisar_app("HEDGE", f"Downside risk detected on BTC. Converting funds to eUSD for capital protection.", status_bot["confianca_ia"])
                
            else:
                print(f"⚖️ Decisão da IA: MANTER (Hold) - Mercado lateral (Confiança: {status_bot['confianca_ia']}%)")
                status_bot["ultima_decisao"] = "HOLD"
                
                # IA AVISA O APP EM INGLÊS:
                avisar_app("MONITORING", "Market is moving sideways. Keeping current vault positions intact.", status_bot["confianca_ia"])

        status_bot["status"] = "Sleeping"
        minutos = 5
        print(f"💤 Ciclo encerrado. O cérebro vai descansar por {minutos} minutos...")
        time.sleep(minutos * 60)
        status_bot["status"] = "Analyzing"
        
# ==========================================
# 5. SERVIDOR WEB E PAINEL DE STATUS
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Emergent Brain is online and patrolling the blockchain!"

@app.route('/health')
def health_check():
    return jsonify(status_bot)

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    ai_decision_loop()
