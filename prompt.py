from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import(
    AI_CONTEXTUALIZER_PROMPT,
    AI_SYSTEM_PROMPT,
)

contextualizer_prompt = ChatPromptTemplate.from_messages([
    ('system', AI_CONTEXTUALIZER_PROMPT),
    MessagesPlaceholder('chat_history'),
    ('human', '{input}'),
])

qa=ChatPromptTemplate.from_messages([
    ('system', AI_SYSTEM_PROMPT),
    MessagesPlaceholder('chat_history'),
    ('human', '{input}'),
])

