import json
import os
import httpx
import imgmaker
import logging
from math import exp
from rich.console import Console
from rich.text import Text

console = Console(record=True)

logger = logging.getLogger("GPT3Client")
logger.setLevel(logging.INFO)


class GPT3Client:
    def __init__(self, image: bool = True):

        assert os.getenv(
            "OPENAI_API_SECRET_KEY"
        ), "The OPENAI_API_SECRET_KEY Environment variable has not been set."

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_SECRET_KEY')}",
        }

        self.imgmaker = None
        if image:
            try:
                self.imgmaker = imgmaker()
            except ImportError:
                logging.warn(
                    "imgmaker failed to load Chrome: you will not be able to generate images."
                )

    def generate(
        self,
        prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 32,
        model: str = "davinci",
    ):

        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "logprobs": 1,
        }

        gen_text = Text()

        gen_text.append(prompt, style="bold")
        console.print(gen_text)

        with httpx.stream(
            "POST",
            f"https://api.openai.com/v1/engines/{model}/completions",
            headers=self.headers,
            data=json.dumps(data),
            timeout=None,
        ) as r:
            for chunk in r.iter_text():
                text = chunk[6:]  # JSON chunks are prepended with "data: "
                if len(text) < 10 and "[DONE]" in text:
                    break

                # tokens is a list of 1-element dicts
                tokens = json.loads(text)["choices"][0]["logprobs"]["top_logprobs"]
                for token_dict in tokens:
                    token, log_prob = list(token_dict.items())[0]

                    if exp(log_prob) > 0.5:
                        color = "green"
                    else:
                        color = "red"

                    gen_text.append(token, style=f"on {color}")
                    console.print(gen_text)

        print(console.export_html())
