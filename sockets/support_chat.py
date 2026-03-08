import ollama
import os
from tqdm import tqdm

REQUIRED_MODELS = [
    "qwen3.5:9b"
]


def ensure_models():
    print("Starting ollama...\n")
    os.system("ollama ps")
    print("Checking Ollama models...\n")

    installed = [m.model for m in ollama.list().models]

    for model in REQUIRED_MODELS:

        if model in installed:
            print(f"{model} already installed")
            continue

        print(f"Downloading {model}...")

        pbar = None

        for chunk in ollama.pull(model, stream=True):

            if "total" in chunk and "completed" in chunk:

                if pbar is None:
                    pbar = tqdm(
                        total=chunk["total"],
                        unit="B",
                        unit_scale=True,
                        desc=model
                    )

                pbar.update(chunk["completed"] - pbar.n)

        if pbar:
            pbar.close()

        print(f"{model} download finished\n")

    print("All required models ready.\n")
    print("Preparing AI models...")
    asd =ollama.generate(
        model="qwen3.5:9b",keep_alive=-1)


class SupportAI:

    def __init__(self, documentation):

        self.documentation = documentation

        self.messages = [
            {
                "role": "system",
                "content": f"""
You are a strict customer support assistant.

Rules:
1. Answer ONLY using the provided documentation.
2. If the answer is not explicitly present in the documentation, respond with exactly:
Sajnos nem tudok segíteni a kérdéseddel kapcsolatban.
3. Do NOT guess.
4. Do NOT provide general advice.
5. Do NOT explain why you don't know.
6. Do NOT use formatting like **bold**, *italic*, `code`.
7. Answer in same language as the question, but do NOT translate the button labels.

Documentation:
{documentation}
"""
            }
        ]

    def ask(self, question):

        self.messages.append({
            "role": "user",
            "content": question
        })

        response_text = ""

        stream = ollama.chat(
            model="qwen3.5:9b",
            messages=self.messages,
            options={
                "temperature": 0
            },
            think=False,
            stream=True
        )

        for chunk in stream:

            if "message" in chunk:
                part = chunk["message"]["content"]
                response_text += part
                if part != "":
                    yield part

        self.messages.append({
            "role": "assistant",
            "content": response_text
        })


