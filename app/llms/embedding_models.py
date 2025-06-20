# app/llms/embedding_models.py

from langchain_openai import OpenAIEmbeddings

# 默认的嵌入模型
default_embedding_model = OpenAIEmbeddings(model="text-embedding-ada-002")

# 如果有其他供应商的嵌入模型，也可以放在这里
# cohere_embedding_model = CohereEmbeddings(model="embed-english-v3.0")
