import pandas as pd
import os

class DataCleaner:
    @staticmethod
    def save_and_clean(data, filename="output/leads_final.csv"):
        df = pd.DataFrame(data)

        # 1. Filtro: Manter apenas quem tem Site E Email
        df = df.dropna(subset=['Site', 'Email'])

        # 2. Remoção de duplicatas
        df = df.drop_duplicates(subset=['Site'])

        # 3. Limpeza de lixo (Blacklist simples)
        blacklist = ['example.com', 'wixpress', 'sentry']
        df = df[~df['Email'].str.contains('|'.join(blacklist), na=False)]

        # Garantir que a pasta de destino exista
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

        # Salvar
        df.to_csv(filename, sep=';', index=False, encoding='utf-8-sig')
        return len(df)