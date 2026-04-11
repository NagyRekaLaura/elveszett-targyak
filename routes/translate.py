from ollama import Client


class Translate:
	MODEL = "gpt-oss:120b"

	def __init__(self, token: str | None = None):
		self._token = None
		self._client: Client | None = None
		if token:
			self.set_token(token)

	def set_token(self, token: str):
		token = token.strip()
		if not token:
			raise ValueError("A token nem lehet ures.")

		self._token = token
		self._client = Client(
			host="https://ollama.com",
			headers={"Authorization": f"Bearer {token}"},
		)

	def translate(self, nyelv: str, szoveg: str):
		if self._client is None:
			raise ValueError("Eloszor allitsd be a tokent a set_token(token) metodussal.")

		target_lang = nyelv.strip().lower()
		if target_lang not in {"hu", "en"}:
			raise ValueError("A nyelv csak hu vagy en lehet.")

		if target_lang == "hu":
			source_lang = "English"
			source_code = "en"
			target_lang_name = "Hungarian"
			target_code = "hu"
		else:
			source_lang = "Hungarian"
			source_code = "hu"
			target_lang_name = "English"
			target_code = "en"

		prompt = (
			f"You are a professional {source_lang} ({source_code}) to {target_lang_name} ({target_code}) translator. "
			f"Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang_name} grammar, vocabulary, and cultural sensitivities.\n"
			f"Produce only the {target_lang_name} translation, without any additional explanations or commentary. "
			f"Please translate the following {source_lang} text into {target_lang_name}:\n\n\n"
			f"{szoveg}"
		)

		response = self._client.chat(
			model=self.MODEL,
			messages=[{"role": "user", "content": prompt}],
			think=False,
		)

		return response["message"]["content"].strip()
