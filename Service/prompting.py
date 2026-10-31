from collections.abc import Iterable
from collections.abc import Mapping


class Prompting:
    SYSTEM_PROMPT = (
        "Priority rule: Never guess the user's first name, specialization, or any "
        "personal information. "
        "If this information does not appear in the active conversation, respond "
        "that you do not have this information. "
        "Never confuse examples or instructions in this prompt with the user's "
        "actual information. "
        "You are a helpful and accurate general-purpose assistant. "
        "Always respond in English, regardless of the language used by the user. "
        "Answer the question directly without making up information. "
        "If you do not know something or the context does not allow you to answer, "
        "state it clearly. "
        "Never guess the user's personal information. "
        "If personal information does not appear in the current conversation, "
        "clearly state that you do not know it. "
        "Use only the history provided in this prompt and never claim to remember "
        "information that is absent from that history. "
        "Avoid repetition, incoherent sentences, and descriptions unrelated "
        "to the question."
    )

    @staticmethod
    def get_system_message():
        return {"role": "system", "content": Prompting.SYSTEM_PROMPT}

    @staticmethod
    def build_messages(messages: Iterable, current_text: str | None = None) -> list[dict[str, str]]:
        result = [Prompting.get_system_message()]

        for message in messages:
            if isinstance(message, Mapping):
                role = message.get("role")
                content = message.get("content")
            else:
                role = message.role
                content = message.content
            if role in {"user", "assistant"} and isinstance(content, str):
                result.append({"role": role, "content": content})

        if current_text is not None:
            result.append({"role": "user", "content": current_text})

        return result

    @staticmethod
    def build_prompt(messages: Iterable, current_text: str | None = None) -> str:
        lines = [
            Prompting.SYSTEM_PROMPT,
            "",
            "Conversation history:",
        ]

        for message in messages:
            if isinstance(message, Mapping):
                role = message.get("role")
                content = message.get("content")
            else:
                role = message.role
                content = message.content
            label = {
                "user": "User",
                "assistant": "Assistant",
                "system": "System",
            }.get(role, role)
            lines.append(f"{label} : {content}")

        if current_text is not None:
            lines.extend(["", f"User : {current_text}"])

        lines.extend(["", "Assistant :"])
        return "\n".join(lines)