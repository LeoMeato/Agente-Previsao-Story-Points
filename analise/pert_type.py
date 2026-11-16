import pandas as pd
import os
from aux import *


df_few_shot = pd.read_csv('results/batch_predictions_few-shot_20261114_154707.csv')
df_few_shot.columns = df_few_shot.columns.str.strip()

df_zero_shot = pd.read_csv('results/batch_predictions_zero-shot_20261114_120148.csv')
df_zero_shot.columns = df_zero_shot.columns.str.strip()

print_dist = False

path_pre = "analise/results/geral_pre/"
path_image_pre = "analise/images/geral_pre/"

path_pos = "analise/results/geral_pos/"
path_image_pos = "analise/images/geral_pos/"


print("==================== Analise Geral ====================\n")

grupos_por_tipo = {issue_type: grupo for issue_type, grupo in df.groupby('issue_type')}


# Resultados
print("==================== Resultados Tipo: Bug ====================")
print("Few-Shot\n")

grupo = grupos_por_tipo["Bug"]

print("Distribuicao de erro (Predito-Real): ")
df_few_shot['diferenca'] = (df_few_shot['predicted_story_points'] - df_few_shot['actual_story_points']) 
contagem = df_few_shot['diferenca'].value_counts()
for value, qtde in contagem.items():
    print(f"\t{value:.2f}\tQtde: {qtde}")