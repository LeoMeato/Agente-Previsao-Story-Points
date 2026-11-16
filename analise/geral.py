import pandas as pd
import os
from aux import *



# df_few_shot = pd.read_csv('results/batch_predictions_few-shot_20261114_154707.csv')
# df_few_shot.columns = df_few_shot.columns.str.strip()

df = pd.read_csv('results/batch_predictions_few-shot_20261114_154707.csv')
df.columns = df.columns.str.strip()

# df_zero_shot = pd.read_csv('results/batch_predictions_zero-shot_20261114_120148.csv')
# df_zero_shot.columns = df_zero_shot.columns.str.strip()

print_dist = False

path_pre = "analise/results/geral_pre/"
path_image_pre = "analise/images/geral_pre/"

path_pos = "analise/results/geral_pos/"
path_image_pos = "analise/images/geral_pos/"


print("==================== Analise Geral ====================\n")

file_analise_pre = path_pre + "analise_pre_geral.txt"

if os.path.exists(file_analise_pre):
    os.remove(file_analise_pre)

# df2_novos = df_zero_shot[~df_zero_shot['issue_key'].isin(df_few_shot['issue_key'])]
# df = pd.concat([df_few_shot, df2_novos], ignore_index=True)

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





# Resultados
print("\n==================== Resultados Gerais ====================\n")

file_analise_pos = path_pos + "analise_pos.txt"



message = "Distribuicao de erro absoluto"
if print_dist:
    print(message)
aux_escrita(file_analise_pos, message)
contagem = df['absolute_error'].value_counts()
for value, qtde in contagem.items():
    message = f"\t{value} => {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pos, message)
plot_erro_absoluto(path_image_pos + "erro_abs.png", df)


message = "Distribuicao de confianca (%)"
if print_dist:
    print_dist(message)
aux_escrita(file_analise_pos, message)
contagem = df['confidence'].value_counts()
for value, qtde in contagem.items():
    message = f"\t{int(float(value)*100)} => {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pos, message)
plot_confianca(path_image_pos + "confianca.png", df)


message = "Distribuicao de complexidade"
if print_dist:
    print(message)
aux_escrita(file_analise_pos, message)
contagem = df['complexity'].value_counts()
for value, qtde in contagem.items():
    message = f"\t{value} =>  {qtde}"
    if print_dist:
        print(message)
    aux_escrita(file_analise_pos, message)
plot_complexidade(path_image_pos + "complexidade.png", df)