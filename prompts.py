from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import AI_CONTEXTUALIZE_PROMPT, AI_SYSTEM_PROMPT

contextualize_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", AI_CONTEXTUALIZE_PROMPT or ""),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# create_stuff_documents_chain exige o placeholder {context} no prompt
_base_system = (AI_SYSTEM_PROMPT or "").strip() or (
    "És um assistente de atendimento. Responde com base no contexto abaixo. "
    "Se não houver informação suficiente, diz que não sabes."
)
if "{context}" not in _base_system:
    _base_system = f"{_base_system}\n\n{{context}}"

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _base_system),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
