import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def aux_escrita(file: str, message: str = ""):
    with open(file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def plot_prioridade(file, df):
    # Número de barras únicas que serão exibidas no gráfico
    num_barras = df["priority"].nunique()

    # Define a largura dinâmica (ex: 1.2 polegadas por barra, com um mínimo de 6)
    largura = max(6, num_barras * 1.2)
    altura = 5

    # Define o tamanho da figura dinamicamente (largura, altura)
    plt.figure(figsize=(largura, altura))

    # Plot direto do DataFrame ordenando pelas prioridades mais frequentes
    ax = sns.countplot(
        data=df,
        x="priority",
        hue="priority",
        order=df["priority"].value_counts().index,
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição de Prioridades")
    plt.xlabel("Prioridade")
    plt.ylabel("Quantidade")

    # Adiciona o número em cima de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()


def plot_num_comentarios(file, df):
    # Obtém a contagem de frequências
    contagem = df["comment_count"].value_counts()

    # Se houver mais de 10 categorias, agrupa do 10º em diante na categoria "outros"
    if len(contagem) > 10:
        top9 = contagem.iloc[:9]
        outros_soma = contagem.iloc[9:].sum()

        # Cria uma nova série mantendo as 9 principais e adicionando 'outros'
        contagem_plot = pd.concat(
            [top9, pd.Series({"outros": outros_soma})]
        ).reset_index()
        contagem_plot.columns = ["comment_count", "count"]
    else:
        contagem_plot = contagem.reset_index()
        contagem_plot.columns = ["comment_count", "count"]

    # Converte para string para garantir que 'outros' plote corretamente no eixo X
    contagem_plot["comment_count"] = contagem_plot["comment_count"].astype(str)

    # Define a largura dinâmica com base nas colunas finais (máximo de 10)
    num_barras = len(contagem_plot)
    largura = max(6, num_barras * 1.2)
    altura = 5

    plt.figure(figsize=(largura, altura))

    # Plot usando os dados pré-agrupados
    ax = sns.barplot(
        data=contagem_plot,
        x="comment_count",
        y="count",
        hue="comment_count",
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição do Número de Comentários (Top 9 + Outros)")
    plt.xlabel("Número de Comentários")
    plt.ylabel("Quantidade")

    # Adiciona a contagem exata no topo de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()


def plot_story_points(file, df):
    # Obtém a contagem de frequências e pega apenas os 15 valores mais frequentes
    contagem_plot = df["actual_story_points"].value_counts().head(15).reset_index()
    contagem_plot.columns = ["actual_story_points", "count"]

    # Converte para string para garantir a formatação correta dos rótulos no eixo X
    contagem_plot["actual_story_points"] = contagem_plot[
        "actual_story_points"
    ].astype(str)

    # Define a largura dinâmica com base nas barras exibidas (máximo de 15)
    num_barras = len(contagem_plot)
    largura = max(6, num_barras * 1.2)
    altura = 5

    plt.figure(figsize=(largura, altura))

    # Plot das 15 maiores frequências
    ax = sns.barplot(
        data=contagem_plot,
        x="actual_story_points",
        y="count",
        hue="actual_story_points",
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição de Story Points (Top 15 Frequentes)")
    plt.xlabel("Story Points")
    plt.ylabel("Quantidade")

    # Adiciona o valor exato no topo de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()


import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_erro_absoluto(file, df):
    # Garante que os valores de erro sejam numéricos
    s_erro = pd.to_numeric(df["absolute_error"], errors="coerce").dropna()

    # Define os limites (bins): 0, valor logo acima de 0 (1e-9), 1, 2, ..., 15, inf
    bins = [0, 1e-9] + list(range(1, 16)) + [float("inf")]

    # Rótulos para as colunas
    labels = (
        ["= 0"]
        + [f"{i} a {i+1}" for i in range(0, 15)]
        + ["outros"]
    )

    # Categoriza os dados (right=True garante intervalos do tipo (a, b])
    categorias = pd.cut(
        s_erro, bins=bins, labels=labels, right=True, include_lowest=True
    )

    # Conta a frequência mantendo a ordem das faixas definidas
    contagem_plot = categorias.value_counts()[labels].reset_index()
    contagem_plot.columns = ["absolute_error", "count"]

    # Remove faixas que eventualmente tenham 0 ocorrências
    contagem_plot = contagem_plot[contagem_plot["count"] > 0]

    # Converte os rótulos para string
    contagem_plot["absolute_error"] = contagem_plot["absolute_error"].astype(str)

    # Largura dinâmica com base no total de barras exibidas
    num_barras = len(contagem_plot)
    largura = max(8, num_barras * 0.8)
    altura = 5

    plt.figure(figsize=(largura, altura))

    # Plot de barras com a paleta Blues_r
    ax = sns.barplot(
        data=contagem_plot,
        x="absolute_error",
        y="count",
        hue="absolute_error",
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição do Erro Absoluto")
    plt.xlabel("Faixa de Erro Absoluto")
    plt.ylabel("Quantidade")

    # Inclina os rótulos do eixo X para melhor leitura
    plt.xticks(rotation=45, ha="right")

    # Adiciona a contagem em cima de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()

def plot_confianca(file, df):
    # Converte os valores de confiança para porcentagem (0.0 a 1.0 -> 0 a 100)
    s_conf = pd.to_numeric(df["confidence"], errors="coerce").dropna() * 100

    # Define os limites de 5 em 5 de 0 a 100
    bins = list(range(0, 105, 5))

    # Cria os rótulos das faixas no formato "0-5%", "5-10%", ..., "95-100%"
    labels = [f"{i}-{i+5}%" for i in range(0, 100, 5)]

    # Categoriza os dados (include_lowest=True garante que 0.0 entre na faixa 0-5%)
    categorias = pd.cut(
        s_conf, bins=bins, labels=labels, right=True, include_lowest=True
    )

    # Obteção da contagem mantendo a ordem sequencial das faixas
    contagem_plot = categorias.value_counts()[labels].reset_index()
    contagem_plot.columns = ["confidence_range", "count"]

    # Filtra apenas as faixas que possuem valores (descarta faixas com 0 ocorrências)
    contagem_plot = contagem_plot[contagem_plot["count"] > 0]

    # Converte o rótulo para string
    contagem_plot["confidence_range"] = contagem_plot["confidence_range"].astype(
        str
    )

    # Define a largura dinâmica com base nas faixas efetivamente presentes
    num_barras = len(contagem_plot)
    largura = max(6, num_barras * 0.9)
    altura = 5

    plt.figure(figsize=(largura, altura))

    # Plot de barras
    ax = sns.barplot(
        data=contagem_plot,
        x="confidence_range",
        y="count",
        hue="confidence_range",
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição da Confiança (%)")
    plt.xlabel("Faixa de Confiança (%)")
    plt.ylabel("Quantidade")

    # Inclina os rótulos do eixo X para facilitar a leitura
    plt.xticks(rotation=45, ha="right")

    # Adiciona a contagem exata no topo de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()


def plot_complexidade(file, df):
    # Obtém a contagem ordenando pelas categorias mais frequentes
    contagem_plot = df["complexity"].value_counts().reset_index()
    contagem_plot.columns = ["complexity", "count"]

    # Converte para string para garantir a renderização correta dos rótulos no eixo X
    contagem_plot["complexity"] = contagem_plot["complexity"].astype(str)

    # Define a largura dinâmica com base no número de categorias únicas
    num_barras = len(contagem_plot)
    largura = max(6, num_barras * 1.2)
    altura = 5

    plt.figure(figsize=(largura, altura))

    # Plot de barras
    ax = sns.barplot(
        data=contagem_plot,
        x="complexity",
        y="count",
        hue="complexity",
        palette="Blues_r",
        legend=False,
    )

    plt.title("Distribuição de Complexidade")
    plt.xlabel("Complexidade")
    plt.ylabel("Quantidade")

    # Adiciona a quantidade exata no topo de cada barra
    for container in ax.containers:
        ax.bar_label(container)

    plt.tight_layout()
    plt.savefig(file)
    plt.close()