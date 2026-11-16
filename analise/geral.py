import pandas as pd
import os
from aux import *

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)


df = pd.read_csv('results/batch_predictions_few-shot_20261114_154707.csv')
df.columns = df.columns.str.strip()

print_dist = False

path_pre = "analise/results/pre/"
path_image_pre = "analise/images/pre/"


print("==================== Analise Geral ====================\n")

file_analise_pre = path_pre + "analise_pre_geral.txt"

if os.path.exists(file_analise_pre):
    os.remove(file_analise_pre)

# ---------------------------------------------------------------

cont_issue = df['issue_key'].nunique()
message = "Qtde issues => " + str(cont_issue)
print(message)
aux_escrita(file_analise_pre, message)

# ---------------------------------------------------------------

contagem = df['project_key'].nunique()
message = "Qtde de projetos => " + str(contagem)
print(message)
aux_escrita(file_analise_pre, message)

# ---------------------------------------------------------------

contagem = df['issue_type'].nunique()
message = "Qtde de tipos de 'tipo de issue' => " + str(contagem)
print(message)
aux_escrita(file_analise_pre, message)

# ---------------------------------------------------------------

contagem = df['has_empty_description'].value_counts().items()
desc = 0
for value, qtde in contagem:
    if not value:
        desc = qtde
message = "Issues com descricao => " + str(desc)
print(message)
aux_escrita(file_analise_pre, message)

# ---------------------------------------------------------------

message = "Distribuicao Priority"
if print_dist:
    print(message)
aux_escrita(file_analise_pre, message)
contagem = df['priority'].value_counts()
for value, qtde in contagem.items():
    message = f"\t {value} => {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pre, message)
plot_prioridade(path_image_pre + "prioridade.png", df)

# ---------------------------------------------------------------

message = "Distribuicao SP"
if print_dist:
    print(message)
aux_escrita(file_analise_pre, message)
contagem = df['actual_story_points'].value_counts()
for value, qtde in contagem.items():
    message = f"\t{value} => {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pre, message)
plot_story_points(path_image_pre + "story_point.png", df)

# ---------------------------------------------------------------

message = "Distribuicao Numero Comentarios"
if print_dist:
    print(message)
aux_escrita(file_analise_pre, message)
contagem = df['comment_count'].value_counts()
for value, qtde in contagem.items():
    message = f"\t{value} => {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pre, message)
plot_num_comentarios(path_image_pre + "num_com.png", df)
