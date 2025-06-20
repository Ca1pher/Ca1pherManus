# app/llms/reasoning_models.py

from langchain_openai import ChatOpenAI

# 总裁办代理使用的 LLM (可能需要最强的推理能力)
supervisor_llm = ChatOpenAI(model="deepseek-chat", temperature=0.6, base_url="http://langchain4j.dev/demo/openai/v1", api_key="demo")

# 总监代理使用的 LLM (这里沿用之前的 director_llm，但现在它可能被 supervisor_llm 替代)
# director_llm = ChatOpenAI(model="gpt-4o", temperature=0.5) # 暂时保留，但可能不再直接使用

# 策划代理使用的 LLM
planner_llm = ChatOpenAI(model="deepseek-chat", temperature=0.3, base_url="http://langchain4j.dev/demo/openai/v1", api_key="demo")

# 其他工人代理使用的 LLM (稍后会用到)
other_worker_llm = ChatOpenAI(model="deepseek-chat", temperature=0.7, base_url="http://langchain4j.dev/demo/openai/v1", api_key="demo")
