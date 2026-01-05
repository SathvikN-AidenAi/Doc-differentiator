import json
from typing import AsyncGenerator
from openai import AsyncAzureOpenAI
from app.config import settings

# Initialize Azure OpenAI client
client = AsyncAzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)

async def stream_chat_response(
    question: str,
    diffs: str,
    chat_history: list = None
) -> AsyncGenerator[str, None]:
    """
    Stream conversational responses from Azure OpenAI
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are DocDiff Assistant — a friendly AI that explains document differences conversationally. "
                "Use natural language, respond quickly, and keep it concise."
            )
        }
    ]

    # Add chat history if provided
    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })

    # Add current question with context
    user_message = f"User Question: {question}\n\nDocument Differences:\n{diffs}"
    if not chat_history:
        user_message += "\n\nIf the question is unrelated to the diffs, just chat naturally."

    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            stream=True,
            max_completion_tokens=1000
        )

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

    except Exception as e:
        yield f"Error: {str(e)}"

async def get_chat_completion(
    question: str,
    diffs: str,
    chat_history: list = None
) -> str:
    """
    Get non-streaming response from Azure OpenAI
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are DocDiff Assistant — a friendly AI that explains document differences conversationally. "
                "Use natural language, respond quickly, and keep it concise."
            )
        }
    ]

    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": "user" if msg["role"] == "user" else "assistant",
                "content": msg["content"]
            })

    user_message = f"User Question: {question}\n\nDocument Differences:\n{diffs}"
    messages.append({"role": "user", "content": user_message})

    try:
        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            max_completion_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"
