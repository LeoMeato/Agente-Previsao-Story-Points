# Contexto do Projeto: Agente de IA para Estimativa de Story Points (TAWOS)

## 1. Visão Geral do Trabalho
- **Objetivo Acadêmico:** Desenvolver um agente de IA para automatizar a estimativa de esforço (*story points*) a partir de issues do Jira.
- **Base de Dados:** TAWOS Dataset (*The Agile Work Organizational System*).
- **Metodologia:** Estudo de caso empírico com abordagem mista (quantitativa e qualitativa).
- **Escopo do Sistema:** **Um único agente de IA** (simplificado para viabilidade e robustez no trabalho).

---

## 2. Perguntas de Pesquisa (Research Questions)

### **RQ1 (Quantitativa) - Precisão Geral**
- **Pergunta:** Qual é a precisão das estimativas de story points geradas pelo agente em comparação com as estimativas reais das equipes de desenvolvimento no TAWOS?
- **Métricas:** Erro Absoluto ($|y_{pred} - y_{real}|$), Média do Erro Absoluto (MAE) e Desvio Padrão.

### **RQ2 (Qualitativa) - Cenários de Discrepância / Falta de Informação**
- **Pergunta:** Em quais contextos específicos (ex.: falta de descrição, ausência de comentários, alterações pós-estimativa) o agente apresenta as maiores discrepâncias?
- **Métricas:** Frequência e magnitude dos erros categorizados por:
  - Descrição ausente (`description_text IS NULL` ou vazio);
  - Issues sem comentários (`comment_count = 0`);
  - Alterações após estimativa (`title_changed_after_estimation`, `story_point_changed_after_estimation`).

### **RQ3 (Quantitativa) - Impacto do Tipo da Tarefa**
- **Pergunta:** Como o tipo de tarefa (`Bug`, `Story`, `Task`, `Improvement`, `New Feature`) afeta estatisticamente a precisão da estimativa do agente?
- **Métricas:** Média do Erro Absoluto (MAE) e desvio padrão agrupados pela coluna `type`.

---

## 3. Estado da Base de Dados (`tawos.db`)
O dump original `TAWOS.sql` (4.3 GB) foi filtrado e convertido em um banco local SQLite leve e indexado:
- **Arquivo:** `tawos.db` (~310 MB).
- **Tabelas disponíveis:**
  1. `project` (39 projetos reais, ex.: Apache Mesos, Spring XD, MongoDB, MuleSoft).
  2. `sprint` (4.594 sprints com datas de início e fim).
  3. `issue` (**63.011 issues** que possuem `story_point > 0`, contendo título, descrição limpa `description_text`, tipo, prioridade, flags de mudança e a coluna pré-calculada `comment_count`).
  4. `comment` (**197.927 comentários** vinculados exclusivamente às issues estimadas).

### Destaque dos Projetos para Testes
- **Apache Mesos (`MESOS` - ID 4):** 3.268 issues estimadas (média 3.23 pts).
- **Spring XD (`XD` - ID 1):** 3.542 issues estimadas (95.5% de cobertura, média 4.53 pts).
- **MongoDB Evergreen (`EVG` - ID 43):** 5.069 issues estimadas com escala padronizada (0.5 a 8 pts).

---

## 4. Scripts Utilitários Criados (`scripts/`)
- [`build_tawos_sqlite.py`](scripts/build_tawos_sqlite.py): Parser de streaming que extraiu o dump de 4.3 GB para o SQLite em ~4 minutos.
- [`verify_database.py`](scripts/verify_database.py): Consulta de integridade, contagem de linhas e verificação das variáveis das RQs.
- [`count_story_points.py`](scripts/count_story_points.py): Relatório de issues e story points por projeto.

---

## 5. Arquitetura do Agente de IA (`agent/` e `run_agent.py`)
- **Provedor e Modelo:** OpenAI (`gpt-4o-mini` / `gpt-4o`) com saídas estritas via Pydantic (`client.beta.chat.completions.parse` / `response_format=EstimationResult`).
- **Estratégias Implementadas:**
  1. **Zero-Shot:** Análise contextual com base nas diretrizes ágeis (Fibonacci) e estatísticas globais do projeto.
  2. **Few-Shot Dinâmico (Calibração Histórica):** Recupera no SQLite (`tawos.db`) âncoras históricas de esforço (baixo: 1-2 pts, médio: 3-5 pts, alto: 8+ pts) concluídas pela **mesma equipe** antes da data da issue avaliada (**zero vazamento temporal**).
- **Módulos Criados:**
  - [`agent/schemas.py`](agent/schemas.py): Definição de `EstimationResult` (story points, complexidade, confiança, rationale, fatores) e `EvaluationRecord`.
  - [`agent/retriever.py`](agent/retriever.py): Extrator de âncoras históricas e amostras estratificadas do SQLite.
  - [`agent/prompts.py`](agent/prompts.py): Engenharia de prompts para Scrum/Agile Story Points.
  - [`agent/estimator.py`](agent/estimator.py): Agente com cliente OpenAI, tratamento de erros e modo Mock.
  - [`agent/evaluator.py`](agent/evaluator.py): Pipeline de avaliação que exporta relatórios automatizados para responder às **RQ1, RQ2 e RQ3**.
  - [`run_agent.py`](run_agent.py): CLI para estimativa de issue única ou execução de benchmark comparativo.

---

## 6. Próximos Passos
1. Inserir a chave `OPENAI_API_KEY` no arquivo `.env` para execução real na API da OpenAI.
2. Executar o benchmark com uma amostra maior (ex.: 50 a 100 issues do projeto `MESOS`) em modo `both` (Zero-Shot vs Few-Shot).
3. Gerar gráficos e tabelas comparativas a partir dos relatórios em `results/` para inclusão no trabalho acadêmico.
