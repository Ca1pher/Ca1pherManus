from symtable import Class

from langchain_openai import ChatOpenAI


OpenAiLLM = ChatOpenAI(api_key='sk-787d0ab6ec3e413db40a9fd19b6f62d1', base_url='https://api.deepseek.com/v1', model='deepseek-chat')