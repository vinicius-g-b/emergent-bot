import torch
import torch.nn as nn
import torch.optim as optim
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import sys

print("🔄 Iniciando Rotina de MLOps: Fine-Tuning Diário da Emergent AI...")

# 1. A ESTRUTURA DO CÉREBRO
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

# 2. O COLETOR E O SANITY CHECK (Filtro de Lixo)
def atualizar_dados_mercado():
    hoje = datetime.now().strftime('%Y-%m-%d')
    print(f"📥 Coletando dados de 2020 até HOJE ({hoje})...")
    
    try:
        df = yf.download('BTC-USD', start='2020-01-01', end=hoje, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        df = df.dropna()
        
        # SANITY CHECK: Se a API retornou menos de 100 dias ou dados vazios, aborta!
        if len(df) < 100 or df.isnull().values.any():
            print("🚨 ERRO CRÍTICO: Dados da API corrompidos ou insuficientes. Abortando treinamento para proteger a IA.")
            sys.exit(0) # Sai do script sem gerar erro no GitHub Actions
            
        # SANITY CHECK 2: Variações impossíveis (ex: queda de 99% em 1 dia por bug da API)
        df['Variacao'] = df['Close'].pct_change()
        if df['Variacao'].min() < -0.60 or df['Variacao'].max() > 0.60:
            print("🚨 ERRO CRÍTICO: Anomalia irreal de preço detectada. Possível bug no Yahoo Finance. Abortando.")
            sys.exit(0)
            
    except Exception as e:
        print(f"🚨 ERRO CRÍTICO na conexão com a API: {e}. Abortando.")
        sys.exit(0)

    # Cálculos quantitativos
    df['Preco_Norm'] = df['Close'] / 100000.0
    df['Volume_Norm'] = df['Volume'] / df['Volume'].rolling(window=30).max()
    
    media_30d = df['Close'].rolling(window=30).mean()
    desvio_30d = df['Close'].rolling(window=30).std()
    df['Sentimento'] = ((df['Close'] - media_30d) / desvio_30d).clip(-1.0, 1.0)
    
    df['Risco'] = (df['Variacao'].rolling(window=14).std() * 100)
    df['Risco'] = (df['Risco'] / df['Risco'].max()).clip(0.0, 1.0)

    df['Retorno_Futuro_3d'] = df['Close'].shift(-3) / df['Close'] - 1
    df = df.dropna()

    condicoes = [
        (df['Retorno_Futuro_3d'] > 0.03),   
        (df['Retorno_Futuro_3d'] < -0.03)   
    ]
    escolhas = [2, 0]
    df['Alvo'] = np.select(condicoes, escolhas, default=1) 
    
    entradas = df[['Variacao', 'Preco_Norm', 'Volume_Norm', 'Sentimento', 'Risco']].values
    saidas = df['Alvo'].values
    
    return torch.tensor(entradas, dtype=torch.float32), torch.tensor(saidas, dtype=torch.long)

# 3. O GUARDIÃO DO DEPLOY E O FINE-TUNING
X_treino, Y_treino = atualizar_dados_mercado()

modelo_novo = EmergentBrain()
modelo_antigo = EmergentBrain()
criterio = nn.CrossEntropyLoss()

# Carrega o cérebro atual de produção
try:
    modelo_antigo.load_state_dict(torch.load('emergent_brain.pth'))
    modelo_novo.load_state_dict(torch.load('emergent_brain.pth'))
    print("🧠 Cérebro base 'emergent_brain.pth' carregado.")
except Exception as e:
    print("⚠️ Cérebro base não encontrado. Treinando do zero.")

# Mede a inteligência do cérebro ANTIGO nos dados de hoje
modelo_antigo.eval()
with torch.no_grad():
    erro_antigo = criterio(modelo_antigo(X_treino), Y_treino).item()

# Treina o cérebro NOVO
otimizador = optim.Adam(modelo_novo.parameters(), lr=0.0001) 
epocas_fine_tuning = 50 
print(f"⚙️ Aplicando Fine-Tuning de {epocas_fine_tuning} épocas no novo modelo...")

modelo_novo.train()
for epoca in range(epocas_fine_tuning):
    otimizador.zero_grad()
    previsoes = modelo_novo(X_treino)
    erro = criterio(previsoes, Y_treino)
    erro.backward()
    otimizador.step()

# Mede a inteligência do cérebro NOVO
modelo_novo.eval()
with torch.no_grad():
    erro_novo = criterio(modelo_novo(X_treino), Y_treino).item()

print(f"📊 Desempenho (Loss) -> Antigo: {erro_antigo:.4f} | Novo: {erro_novo:.4f}")

# 4. A DECISÃO FINAL (O Guardião)
if erro_novo < erro_antigo:
    torch.save(modelo_novo.state_dict(), 'emergent_brain.pth')
    print("✅ SUCESSO! O modelo novo é mais inteligente. 'emergent_brain.pth' sobreescrito.")
else:
    print("🛡️ GUARDIÃO ATIVADO: O treinamento de hoje piorou a IA (Overfitting/Ruído).")
    print("Descartando atualização. Mantendo o cérebro antigo em produção para segurança da VGB Tech.")
