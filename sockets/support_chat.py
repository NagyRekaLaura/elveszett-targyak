from ollama import Client


class SupportAI:
    MODEL = "gpt-oss:120b"

    def __init__(self, documentation: str = ""):
        self._token = None
        self.documentation = documentation
        self.sessions = {}  # {session_id: messages_list}

    def _get_system_message(self) -> dict:
        return {
    "role": "system",
    "content": f"""
You are a strict customer support assistant.

You MUST follow these rules without exception:

CORE RULES:
1. Answer ONLY with information that is explicitly and clearly stated in the provided documentation.
2. If the exact answer is not found in the documentation, respond with EXACTLY this sentence and nothing else:
Sajnos nem tudok segíteni a kérdéseddel kapcsolatban.
3. Do NOT infer, assume, guess, or combine multiple pieces of information unless the documentation explicitly connects them.
4. Do NOT use prior knowledge.
5. Do NOT add explanations, suggestions, or extra context.

STRICT BEHAVIOR:
6. If the question is ambiguous or partially answerable, treat it as NOT answerable.
7. If multiple interpretations exist and the documentation does not clearly resolve them, refuse.
8. Only answer what is directly asked. Do not expand the scope.
9. Do NOT rephrase or summarize beyond what is necessary.

LANGUAGE RULES:
10. ALWAYS answer in the same language as the user's question.
11. The user's language has priority over the documentation language.
12. If the documentation is in a different language, translate the meaning internally but respond in the user's language.

OUTPUT FORMAT:
13. Output plain text only.
14. No formatting (no markdown, no bold, no code blocks, no lists).
15. No quotes, no prefixes, no suffixes.

DOCUMENTATION USAGE:
16. Every statement in your answer must be directly traceable to the documentation.
17. If any part of your answer is not explicitly supported, do NOT answer.

Documentation:
{self.documentation}
"""
}

    def _get_session_messages(self, session_id: str) -> list:
        """Get or create messages list for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = [self._get_system_message()]
        return self.sessions[session_id]

    def _build_client(self) -> Client:
        if not self._token:
            raise ValueError("Support AI token not set. Use set_token() first.")
        return Client(
            host="https://ollama.com",
            headers={"Authorization": f"Bearer {self._token}"},
        )

    def set_token(self, token: str):
        """Set the API token"""
        token = token.strip()
        if not token:
            raise ValueError("Token cannot be empty.")
        self._token = token

    def ask(self, question: str, session_id: str):
        """Ask a question in a specific session"""
        if not self._token:
            yield "A szolgáltatás jelenleg nem elérhető."
            return

        try:
            messages = self._get_session_messages(session_id)
            messages.append({
                "role": "user",
                "content": question
            })

            response_text = ""
            client = self._build_client()

            for chunk in client.chat(
                model=self.MODEL,
                messages=messages,
                think=False,
                stream=True
            ):
                if "message" in chunk:
                    part = chunk["message"]["content"]
                    response_text += part
                    if part != "":
                        yield part

            messages.append({
                "role": "assistant",
                "content": response_text
            })
        except Exception as e:
            # On any error, return the service unavailable message
            yield "A szolgáltatás jelenleg nem elérhető."

    def clear_session(self, session_id: str):
        """Clear a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


