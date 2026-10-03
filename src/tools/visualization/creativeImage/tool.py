from pathlib import Path

from google import genai
from google.genai import types

from common.core.env import env


class CreativeImageTool:

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=env.GEMINI_API_KEY
        )

        self.model = env.GEMINI_IMAGE_MODEL

    def run(
        self,
        prompt: str,
        output_path: str | Path,
    ) -> Path:

        if not prompt.strip():
            raise ValueError(
                "Image prompt cannot be empty."
            )

        output_path = Path(output_path)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=[
                    "TEXT",
                    "IMAGE",
                ],
            ),
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        for candidate in response.candidates or []:

            content = candidate.content

            if not content:
                continue

            for part in content.parts or []:

                if part.inline_data is None:
                    continue

                image_data = part.inline_data.data

                if not image_data:
                    continue

                output_path.write_bytes(
                    image_data
                )

                return output_path

        raise RuntimeError(
            "Gemini did not return image data."
        )