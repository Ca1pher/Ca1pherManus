# app/llms/chat_models.py

from langchain_openai import ChatOpenAI

# 默认的聊天模型
default_chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# 也可以有其他聊天模型，例如用于客服的
customer_service_chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)
