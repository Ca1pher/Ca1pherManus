# app/langgraph_core/prompts/utils.py
import os
import json
from typing import Optional, List, Dict, Any

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,  # 确保导入 AIMessagePromptTemplate
    MessagesPlaceholder,
    PromptTemplate  # 确保导入 PromptTemplate
)
from langchain_core.example_selectors import LengthBasedExampleSelector  # 确保导入路径正确


def _load_file_content(file_path: str) -> str:
    """Helper to load content from a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def get_prompt_path(agent_name: str, prompt_type: str) -> str:
    """Constructs the full path to a prompt file."""
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, agent_name, f"{prompt_type}.md")


def get_examples_path(agent_name: str, examples_name: str) -> str:
    """Constructs the full path to an examples file."""
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, agent_name, f"{examples_name}.json")


def load_chat_prompt_template(agent_name: str, human_template_name: str, system_template_name: str = "system_prompt",
                              examples_name: Optional[str] = None) -> ChatPromptTemplate:
    """
    Loads and constructs a ChatPromptTemplate for a given agent.
    """
    system_content = _load_file_content(get_prompt_path(agent_name, system_template_name))
    human_content = _load_file_content(get_prompt_path(agent_name, human_template_name))

    # Initial messages for the ChatPromptTemplate
    messages = [
        SystemMessagePromptTemplate.from_template(system_content),
        MessagesPlaceholder(variable_name="messages"),  # For chat history
        HumanMessagePromptTemplate.from_template(human_content)
    ]

    if examples_name:
        examples_data: List[Dict[str, str]] = json.loads(
            _load_file_content(get_examples_path(agent_name, examples_name)))

        # Define a simple PromptTemplate for the example selector to format each example.
        # This is a regular PromptTemplate, not a ChatPromptTemplate.
        example_prompt_for_selector = PromptTemplate.from_template("Human: {input}\nAI: {output}")

        # Use LengthBasedExampleSelector to select examples (returns a list of dictionaries)
        example_selector = LengthBasedExampleSelector(
            examples=examples_data,
            example_prompt=example_prompt_for_selector,  # 这里传入的是 PromptTemplate
            max_length=200  # 根据你的 token 限制调整
        )

        # Select examples. The `input_variables` can be a dummy value if not used for selection logic.
        selected_examples = example_selector.select_examples({"input": ""})

        # Convert selected examples (dictionaries) into HumanMessagePromptTemplate and AIMessagePromptTemplate objects
        example_messages_to_insert = []
        for ex in selected_examples:
            example_messages_to_insert.append(HumanMessagePromptTemplate.from_template(ex["input"]))
            example_messages_to_insert.append(AIMessagePromptTemplate.from_template(ex["output"]))

        # Insert the example messages right after the system message (at index 1)
        messages[1:1] = example_messages_to_insert

    return ChatPromptTemplate.from_messages(messages)

