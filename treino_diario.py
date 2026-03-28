import torch
import torch.nn as nn
import torch.optim as optim
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

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

# 2. O COLETOR E O BUFFER DE MEMÓRIA (Até o dia de HOJE)
def atualizar_dados_mercado():
    hoje = datetime.now().strftime('%Y-%m-%d')
    print(f"📥 Coletando dados de 2020 até HOJE ({hoje})...")
    
    # Baixa a história toda. Isso garante a proporção 90% passado (Crashes/Bulls) e 10% presente.
    df = yf.download('BTC-USD', start='2020-01-01', end=hoje, progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    df = df.dropna()

    # Cálculos quantitativos
    df['Variacao'] = df['Close'].pct_change()
    df['Preco_Norm'] = df['Close'] / 100000.0
    df['Volume_Norm'] = df['Volume'] / df['Volume'].rolling(window=30).max()
    
    media_30d = df['Close'].rolling(window=30).mean()
    desvio_30d = df['Close'].rolling(window=30).std()
    df['Sentimento'] = ((df['Close'] - media_30d) / desvio_30d).clip(-1.0, 1.0)
    
    df['Risco'] = (df['Variacao'].rolling(window=14).std() * 100)
    df['Risco'] = (df['Risco'] / df['Risco'].max()).clip(0.0, 1.0)

    # Gabarito (Target)
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

# 3. O AJUSTE FINO (Fine-Tuning Seguro)
X_treino, Y_treino = atualizar_dados_mercado()

modelo = EmergentBrain()

# TENTA CARREGAR O CÉREBRO EXISTENTE PARA NÃO PERDER A MEMÓRIA
try:
    modelo.load_state_dict(torch.load('emergent_brain.pth'))
    print("🧠 Cérebro base 'emergent_brain.pth' carregado com sucesso. Iniciando expansão neural...")
except Exception as e:
    print("⚠️ Cérebro base não encontrado. Treinando um novo do zero...")

criterio = nn.CrossEntropyLoss()
# O SEGREDO DO SÊNIOR: Taxa de aprendizado MICRO (0.0001) para não dar "Esquecimento Catastrófico"
otimizador = optim.Adam(modelo.parameters(), lr=0.0001) 

# Poucas épocas (apenas 50), porque é só uma revisão diária, não um doutorado novo.
epocas_fine_tuning = 50 
print(f"⚙️ Aplicando Fine-Tuning de {epocas_fine_tuning} épocas...")

for epoca in range(epocas_fine_tuning):
    otimizador.zero_grad()
    previsoes = modelo(X_treino)
    erro = criterio(previsoes, Y_treino)
    erro.backward()
    otimizador.step()

acertos = (torch.argmax(previsoes, dim=1) == Y_treino).float().mean()
print(f"🎯 Atualização Concluída! Precisão atualizada: {acertos.item()*100:.2f}%")

# 4. SALVANDO O CÉREBRO ATUALIZADO
torch.save(modelo.state_dict(), 'emergent_brain.pth')
print("💾 'emergent_brain.pth' sobreescrito com os dados de hoje. Pronto para o deploy!")