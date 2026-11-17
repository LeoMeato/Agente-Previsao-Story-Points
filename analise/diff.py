import pandas as pd
import os
from aux import *

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)


df_few_shot = pd.read_csv('results/batch_predictions_few-shot_20261114_154707.csv')
df_few_shot.columns = df_few_shot.columns.str.strip()

df_zero_shot = pd.read_csv('results/batch_predictions_zero-shot_20261114_120148.csv')
df_zero_shot.columns = df_zero_shot.columns.str.strip()

print_dist = False

path_diff = "analise/results/pos/diff/"



grupos_por_tipo_few = {issue_type: grupo for issue_type, grupo in df_few_shot.groupby('issue_type')}
grupos_por_tipo_zero = {issue_type: grupo for issue_type, grupo in df_zero_shot.groupby('issue_type')}


types = ["Bug", "Improvement", "Story", "Suggestion", "ALL"]

grupos_por_tipo_few["ALL"] = df_few_shot
grupos_por_tipo_zero["ALL"] = df_zero_shot

for type in types:
    print(f"==================== Resultados Tipo: {type} ====================\n")

    os.makedirs(path_diff + f"{type}/", exist_ok=True)

    file = path_diff + f"{type}/analise.txt"

    if os.path.exists(file):
        os.remove(file)

    # ---------------------------------------------------------------

    shots = ["Few", "Zero"]

    for shot in shots:

        if shot == "Few":
            df = grupos_por_tipo_few[type]
        if shot == "Zero":
            df = grupos_por_tipo_zero[type]

        message = f"-{shot}-Shot"
        print(message)
        aux_escrita(file, message)


        df['diferenca'] = df['predicted_story_points'] - df['actual_story_points']
        
        if 'absolute_error' not in df.columns:
            df['absolute_error'] = df['diferenca'].abs()

        # Métricas do Erro Absoluto (MAE, Mediana do Erro, etc.)
        mae = df['absolute_error'].mean()
        mediana_mae = df['absolute_error'].median()
        std_mae = df['absolute_error'].std()

        # Métricas do Erro Residual (Predito - Real)
        media_diff = df['diferenca'].mean()
        mediana_diff = df['diferenca'].median()
        std_diff = df['diferenca'].std()
        min_diff = df['diferenca'].min()
        max_diff = df['diferenca'].max()

        stats_message = (
            f"--- Estatísticas ---\n"
            f"MAE (Média Erro Absoluto): {mae:.4f}\n"
            f"Mediana do Erro Absoluto: {mediana_mae:.4f}\n"
            f"Desvio Padrão do Erro Absoluto: {std_mae:.4f}\n"
            f"Média da Diferença (Pred - Real): {media_diff:.4f}\n"
            f"Mediana da Diferença: {mediana_diff:.4f}\n"
            f"Desvio Padrão da Diferença: {std_diff:.4f}\n"
            f"Mínimo / Máximo Diferença: [{min_diff:.2f}, {max_diff:.2f}]\n"
        )
        
        print(stats_message)
        aux_escrita(file, stats_message)



# Best



path_pos = "analise/results/pos/diff/best/"
path_image_pos = "analise/images/diff/best/"

ID_COL = 'issue_key'

# 1. Garantir o cálculo do erro absoluto nos DataFrames originais
for df in [df_few_shot, df_zero_shot]:
    if 'absolute_error' not in df.columns:
        df['absolute_error'] = (df['predicted_story_points'] - df['actual_story_points']).abs()

# 2. Merge dos ficheiros Few-Shot e Zero-Shot pela chave 'issue_key'
df_merged = pd.merge(
    df_few_shot, 
    df_zero_shot, 
    on=ID_COL, 
    suffixes=('_few', '_zero')
)

# Consolidar metadados do merge
df_merged['issue_type'] = df_merged['issue_type_few']
df_merged['actual_story_points'] = df_merged['actual_story_points_few']

# 3. Selecionar o menor erro absoluto para cada issue
df_merged['absolute_error'] = df_merged[['absolute_error_few', 'absolute_error_zero']].min(axis=1)

# Atribuir os story points preditos do modelo que teve o menor erro
df_merged['predicted_story_points'] = df_merged.apply(
    lambda r: r['predicted_story_points_few'] if r['absolute_error_few'] <= r['absolute_error_zero'] 
              else r['predicted_story_points_zero'], 
    axis=1
)

# Diferença com sinal (Predito - Real) do melhor resultado
df_merged['diferenca'] = df_merged['predicted_story_points'] - df_merged['actual_story_points']

# 4. Agrupar por tipo de tarefa
grupos_por_tipo_best = {issue_type: grupo for issue_type, grupo in df_merged.groupby('issue_type')}
grupos_por_tipo_best["ALL"] = df_merged

types = ["Bug", "Improvement", "Story", "Suggestion", "ALL"]

for type_name in types:
    print(f"==================== Resultados (Melhor Erro por Issue) Tipo: {type_name} ====================\n")
    
    os.makedirs(path_pos + f"{type_name}/", exist_ok=True)
    os.makedirs(path_image_pos + f"{type_name}/", exist_ok=True)

    file = path_pos + f"{type_name}/analise.txt"
    image = path_image_pos + f"{type_name}/"

    if os.path.exists(file):
        os.remove(file)

    df = grupos_por_tipo_best[type_name]

    message = "-Best-Shot (Menor Erro por Issue)"
    print(message)
    aux_escrita(file, message)

    # ------------------- CÁLCULO DAS ESTATÍSTICAS -------------------
    mae = df['absolute_error'].mean()
    mediana_mae = df['absolute_error'].median()
    std_mae = df['absolute_error'].std()

    media_diff = df['diferenca'].mean()
    mediana_diff = df['diferenca'].median()
    std_diff = df['diferenca'].std()
    min_diff = df['diferenca'].min()
    max_diff = df['diferenca'].max()

    stats_message = (
        f"--- Estatísticas (Melhor Seleção por Issue) ---\n"
        f"MAE (Média Erro Absoluto): {mae:.4f}\n"
        f"Mediana do Erro Absoluto: {mediana_mae:.4f}\n"
        f"Desvio Padrão do Erro Absoluto: {std_mae:.4f}\n"
        f"Média da Diferença (Pred - Real): {media_diff:.4f}\n"
        f"Mediana da Diferença: {mediana_diff:.4f}\n"
        f"Desvio Padrão da Diferença: {std_diff:.4f}\n"
        f"Mínimo / Máximo Diferença: [{min_diff:.2f}, {max_diff:.2f}]\n"
    )
    
    print(stats_message)
    aux_escrita(file, stats_message)
