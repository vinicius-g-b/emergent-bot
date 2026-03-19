import json
import time
import random
from web3 import Web3
import torch
import requests
import torch.nn as nn
import threading
from flask import Flask
import os

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
# 2. CONFIGURAÇÕES DA BLOCKCHAIN
# ==========================================
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

VAULT_ADDRESS = web3.to_checksum_address("COLE_AQUI_O_SEU_ENDERECO_COMPLETO_DO_APP")
EUSD_ADDRESS = web3.to_checksum_address("0x960C3A75ad6b793882D643f8B71c33945269af01")

AI_PRIVATE_KEY = "584c7bdfcc43bd124c6e1cec9300d0aebbaedced9be4c0ef874f04bd5dc482c3" 
ai_account = web3.eth.account.from_key(AI_PRIVATE_KEY)

with open("vault_abi.json", "r") as file:
    vault_abi = json.load(file)

vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)

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
    
    tx = funcao.build_transaction({
        'from': ai_account.address,
        'nonce': web3.eth.get_transaction_count(ai_account.address),
        'gas': 500000,
        'gasPrice': web3.eth.gas_price
    })
    
    signed_tx = web3.eth.account.sign_transaction(tx, private_key=AI_PRIVATE_KEY)
    
    # Usando o padrão novo da biblioteca web3 (com underline)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"🚀 Enviado! Hash: {web3.to_hex(tx_hash)}")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print("✅ Transação confirmada na blockchain!")
    else:
        print("❌ Falha na execução do Smart Contract.")

# ==========================================
# 4. O LOOP PRINCIPAL DA IA (PILOTO AUTOMÁTICO)
# ==========================================
def ai_decision_loop():
    print("🧠 Inicializando Rede Neural...")
    model = EmergentBrain()
    
    try:
        model.load_state_dict(torch.load('emergent_brain.pth'))
        print("✅ Cérebro carregado. Iniciando patrulha de mercado.")
    except:
        print("⚠️ Arquivo .pth não encontrado. Usando pesos aleatórios para teste.")
        
    model.eval()

    while True:
        print("\n" + "="*40)
        print(f"⏰ [{time.strftime('%H:%M:%S')}] Iniciando ciclo de análise...")

        # 1. LEITURA DE MERCADO REAL (COINGECKO API - Imune ao bloqueio dos EUA)
        print("📊 Buscando dados ao vivo do Bitcoin no CoinGecko...")
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"
            headers = {'User-Agent': 'Mozilla/5.0'} # Truque para o CoinGecko não nos bloquear
            resposta = requests.get(url, headers=headers).json()
            
            dados_btc = resposta['bitcoin']
            preco_real = float(dados_btc['usd'])
            mudanca_24h = float(dados_btc['usd_24h_change'])
            volume_24h = float(dados_btc['usd_24h_vol'])

            # Normalizando para a IA
            variacao = mudanca_24h / 100.0
            preco_atual = preco_real / 100000.0 
            volume = volume_24h / 100000000000.0 # Ajustado para a escala do CoinGecko
            
            market_data = [variacao, preco_atual, volume]
            print(f"📈 Preço BTC: ${preco_real:.2f} | Variação: {mudanca_24h:.2f}%")
            
        except Exception as e:
            print(f"⚠️ Erro ao ler o CoinGecko ({e}). Usando dados de emergência.")
            market_data = [0.0, 0.0, 0.0]

        tensor_inputs = torch.tensor(market_data, dtype=torch.float32)

        # 2. O CÉREBRO PENSA
        with torch.no_grad():
            prediction = model(tensor_inputs)
            decision = torch.argmax(prediction).item() 

        # 3. TRADUZINDO A DECISÃO PARA A BLOCKCHAIN
        if decision == 2:
            print("📈 Decisão da IA: COMPRAR")
            try:
                executar_ordem("COMPRA", 100)
            except Exception as e:
                print(f"❌ Erro ao executar compra na blockchain: {e}")
            
        elif decision == 0:
            print("📉 Decisão da IA: VENDER")
            try:
                executar_ordem("VENDA", 100)
            except Exception as e:
                print(f"❌ Erro ao executar venda na blockchain: {e}")
            
        else:
            print("⚖️ Decisão da IA: MANTER (Hold) - O mercado está lateral.")

        # 4. HORA DE DORMIR
        minutos = 5
        print(f"💤 Ciclo encerrado. O cérebro vai descansar por {minutos} minutos...")
        time.sleep(minutos * 60)
        
app = Flask(__name__)

@app.route('/')
def home():
    return "O Cérebro da Emergent está online e patrulhando a blockchain!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    ai_decision_loop()
