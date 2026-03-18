import pandas as pd
import json

try:
    df_dm = pd.read_excel('DM.xlsx')
    df_th = pd.read_excel('Bang TH.xlsx')

    info = {
        'DM': {
            'columns': list(df_dm.columns),
            'sample': df_dm.head(2).fillna('').to_dict('records')
        },
        'TH': {
            'columns': list(df_th.columns),
            'sample': df_th.head(2).fillna('').to_dict('records')
        }
    }

    with open('explore.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
except Exception as e:
    with open('explore.json', 'w', encoding='utf-8') as f:
        f.write(str(e))
