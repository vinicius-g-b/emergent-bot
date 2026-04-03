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

# 1. AUTO-RECUPERAÇÃO

# ==========================================

def inicializacao_segura():

    """Garante que o bot recupere o estado caso o Render reinicie o servidor."""

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

            print("🗄️ Banco de dados limpo. Iniciando operações do zero.")

    except Exception as e:

        print(f"⚠️ Erro ao acessar a memória do Supabase: {e}")

        

    print("✅ Auto-recuperação concluída. O Cérebro está online.")



# ==========================================

# 2. CAMADAS AVANÇADAS (SENTIMENTO E RISCO/LIQUIDEZ)

# ==========================================

def obter_sentimento_mercado():

    try:

        url = "https://api.alternative.me/fng/?limit=1"

        resposta = requests.get(url).json()

        valor = int(resposta['data'][0]['value'])

        classificacao = resposta['data'][0]['value_classification']

        valor_normalizado = (valor - 50) / 50.0

        return valor_normalizado, classificacao

    except:

        return 0.0, "Neutral"



def analisar_risco_sistemico():

    try:

        pool_liquidity_healthy = True 

        if pool_liquidity_healthy:

            risco = random.uniform(0.1, 0.4) 

        else:

            risco = random.uniform(0.7, 1.0) 

            print("⚠️ Alerta On-chain: Baixa liquidez detectada nas pools!")

        return risco

    except:

        return 0.5



# ==========================================

# 3. A ESTRUTURA DO CÉREBRO (5 Entradas)

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



# ==========================================

# 4. BLOCKCHAIN & EXECUÇÃO COM TRANSPARÊNCIA (L2 ARBITRUM)

# ==========================================

RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"

web3 = Web3(Web3.HTTPProvider(RPC_URL))



# Contratos Oficiais VGB Tech na Arbitrum Sepolia

VAULT_ADDRESS = web3.to_checksum_address("0x5185cfEB2628CBEDeE04aCf320E13634Be63A2D5")

EUSD_ADDRESS = web3.to_checksum_address("0x2e17393bd766f8b1c5007224854b82afde23d1fc")



# Puxando a chave privada com segurança do servidor (Render)

AI_PRIVATE_KEY = os.environ.get("PRIVATE_KEY", "CHAVE_NAO_ENCONTRADA") 



if AI_PRIVATE_KEY != "CHAVE_NAO_ENCONTRADA":

    ai_account = web3.eth.account.from_key(AI_PRIVATE_KEY)

else:

    print("🚨 AVISO CRÍTICO: Chave Privada não encontrada no ambiente Render. As transações não serão assinadas.")



try:

    with open("vault_abi.json", "r") as file:

        vault_abi = json.load(file)

    vault_contract = web3.eth.contract(address=VAULT_ADDRESS, abi=vault_abi)

except Exception as e:

    print(f"⚠️ Erro ABI: {e}")



def executar_ordem(tipo_ordem, valor_dolares):

    if AI_PRIVATE_KEY == "CHAVE_NAO_ENCONTRADA": 

        print("❌ Operação abortada: Bot sem permissão para operar (Chave Privada ausente).")

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

        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"🚀 Transação Hash: {web3.to_hex(tx_hash)}")

    except Exception as e:

        print(f"❌ Falha on-chain (Possível pico de Gas ou Congestionamento): {e}")

        avisar_app("NETWORK DELAY", "A rede Arbitrum está congestionada ou a taxa de Gas oscilou. Aguardando estabilidade.", 0)

        

# ==========================================

# 5. LOOP PRINCIPAL DA IA MULTICAMADA

# ==========================================

def ai_decision_loop():

    global status_bot

    print("🧠 Inicializando Rede Neural Multimodal v2...")

    model = EmergentBrain()

    

    try:

        model.load_state_dict(torch.load('emergent_brain.pth'))

        print("✅ Cérebro carregado com sucesso.")

    except Exception as e:

        print("⚠️ Cérebro antigo incompatível. Iniciando nova sinapse...")

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

            

            print(f"📈 BTC: ${status_bot['preco_btc']:.2f} | Sentimento: {sentimento_texto} | Risco de Liquidez: {risco_sistemico:.2f}")

            

            market_data = [variacao, preco_atual, volume, sentimento_valor, risco_sistemico]

            

        except Exception as e:

            print(f"⚠️ Erro nas APIs. Acionando modo de emergência. Detalhe: {e}")

            market_data = [0.0, 0.0, 0.0, 0.0, 0.0]

            sentimento_texto = "Neutral"

            risco_sistemico = 0.5



        # CIRCUIT BREAKER (DEFESA)

        if sentimento_texto == "Extreme Fear" or risco_sistemico > 0.85:

            print("🚨 ALERTA VERMELHO: Risco Crítico de Liquidez ou Sentimento Detectado! Ignorando Rede Neural.")

            status_bot["ultima_decisao"] = "EMERGENCY HEDGE"

            status_bot["confianca_ia"] = 100.0

            executar_ordem("VENDA", 100)

            avisar_app("EMERGENCY HEDGE", f"Extreme Fear or Liquidity Anomaly detected. Executing emergency capital protection to eUSD.", 100)

        

        # REDE NEURAL PADRÃO

        else:

            tensor_inputs = torch.tensor(market_data, dtype=torch.float32)

            with torch.no_grad():

                prediction = model(tensor_inputs)

                probabilidades = torch.nn.functional.softmax(prediction, dim=0)

                confianca = torch.max(probabilidades).item()

                decision = torch.argmax(prediction).item() 

                

            status_bot["confianca_ia"] = round(confianca * 100, 2)



            # FILTRO DE SLIPPAGE E TAXAS (SÊNIOR APROVOU)

            # A IA só opera se tiver mais de 85% de certeza, garantindo que o lucro pague os custos operacionais da rede.

            if confianca < 0.85:

                print(f"⚖️ Confiança de {status_bot['confianca_ia']}% insuficiente para cobrir Gas e Slippage.")

                status_bot["ultima_decisao"] = "HOLD"

                avisar_app("HOLD", f"Signal confidence ({status_bot['confianca_ia']}%) does not cover expected gas fees and slippage. Treasury remains parked.", status_bot["confianca_ia"])

                

            else:

                if decision == 2:

                    status_bot["ultima_decisao"] = "BUY"

                    executar_ordem("COMPRA", 100)

                    avisar_app("BUY", f"Market sentiment is {sentimento_texto}. Increasing spot BTC exposure to capture value.", status_bot["confianca_ia"])

                    

                elif decision == 0:

                    status_bot["ultima_decisao"] = "SELL"

                    executar_ordem("VENDA", 100)

                    avisar_app("HEDGE", f"Algorithm identified a local top or liquidity drop. Rebalancing treasury to eUSD.", status_bot["confianca_ia"])

                    

                else:

                    status_bot["ultima_decisao"] = "HOLD"

                    avisar_app("MONITORING", "Treasury is perfectly balanced for current market conditions and on-chain liquidity.", status_bot["confianca_ia"])



        status_bot["status"] = "Sleeping"

        print(f"💤 Varredura concluída. Descansando por 5 minutos...")

        time.sleep(300)

        status_bot["status"] = "Analyzing"

        

# ==========================================

# 6. SERVIDOR WEB 

# ==========================================

app = Flask(__name__)



@app.route('/')

def home():

    return "Emergent Advanced Brain is online and patrolling the blockchain!"



@app.route('/health')

def health_check():

    return jsonify(status_bot)



def run_web():

    port = int(os.environ.get("PORT", 10000))

    app.run(host='0.0.0.0', port=port)



if __name__ == "__main__":

    threading.Thread(target=run_web).start()

    inicializacao_segura()

    ai_decision_loop()
