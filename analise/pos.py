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

path_pos = "analise/results/pos/type/"
path_image_pos = "analise/images/pos/type/"



grupos_por_tipo_few = {issue_type: grupo for issue_type, grupo in df_few_shot.groupby('issue_type')}
grupos_por_tipo_zero = {issue_type: grupo for issue_type, grupo in df_zero_shot.groupby('issue_type')}


types = ["Bug", "Improvement", "Story", "Suggestion", "ALL"]

grupos_por_tipo_few["ALL"] = df_few_shot
grupos_por_tipo_zero["ALL"] = df_zero_shot

for type in types:
    print(f"==================== Resultados Tipo: {type} ====================\n")

    os.makedirs(path_pos + f"{type}/", exist_ok=True)
    os.makedirs(path_image_pos + f"{type}/", exist_ok=True)
    
    file = path_pos + f"{type}/analise.txt"
    image = path_image_pos + f"{type}/"

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

        message = "Distribuicao de erro (Predito - Real)"
        if print_dist:
            print(message)
        aux_escrita(file, message)
        df['diferenca'] = (df['predicted_story_points'] - df['actual_story_points']) 
        contagem = df['diferenca'].value_counts()
        for value, qtde in contagem.items():
            message = f"\t{value:.2f} => {qtde}"
            if print_dist:
                print(message)
            aux_escrita(file, message)
        plot_distribuicao_erro(image + f"distr_erro_{type}_{shot}.png", df)

        # ---------------------------------------------------------------

        if shot == "Few":
            df = grupos_por_tipo_few[type]
        if shot == "Zero":
            df = grupos_por_tipo_zero[type]
        
        message = f"-{shot}-Shot"
        print(message)
        aux_escrita(file, message)


        message = "Distribuicao de erro absoluto"
        if print_dist:
            print(message)
        aux_escrita(file, message)
        contagem = df['absolute_error'].value_counts()
        for value, qtde in contagem.items():
            message = f"\t{value} => {qtde}"
            if print_dist:
                print(message)
            aux_escrita(file, message)
        plot_erro_absoluto(image + f"erro_abs_{type}_{shot}.png", df)


        # ---------------------------------------------------------------

        if shot == "Few":
            df = grupos_por_tipo_few[type]
        if shot == "Zero":
            df = grupos_por_tipo_zero[type]

        message = f"-{shot}-Shot"
        print(message)
        aux_escrita(file, message)


        message = "Distribuicao de confianca (%)"
        if print_dist:
            print(message)
        aux_escrita(file, message)
        contagem = df['confidence'].value_counts()
        for value, qtde in contagem.items():
            message = f"\t{int(float(value)*100)} => {qtde}"
            if print_dist:
                print(message)
            aux_escrita(file, message)
        plot_confianca(image + f"confianca_{type}_{shot}.png", df)

        # ---------------------------------------------------------------

        if shot == "Few":
            df = grupos_por_tipo_few[type]
        if shot == "Zero":
            df = grupos_por_tipo_zero[type]

        message = f"-{shot}-Shot"
        print(message)
        aux_escrita(file, message)


        message = "Distribuicao de complexidade"
        if print_dist:
            print(message)
        aux_escrita(file, message)
        contagem = df['complexity'].value_counts()
        for value, qtde in contagem.items():
            message = f"\t{value} =>  {qtde}"
            if print_dist:
                print(message)
            aux_escrita(file, message)
        plot_complexidade(image + f"complexidade_{type}_{shot}.png", df)

