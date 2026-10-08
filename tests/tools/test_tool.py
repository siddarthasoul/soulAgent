from pathlib import Path

from src.tools.visualization.creativeImage.tool import CreativeImageTool


def main() -> None:

    prompt = """
    Create a clean educational scientific illustration of a Transformer
    neural network architecture.

    Show:
    - input tokens
    - token embeddings
    - positional information
    - multi-head self-attention
    - feed-forward network
    - residual connections
    - layer normalization
    - output tokens

    Use a professional educational diagram style.
    Make the architecture easy for a student to understand.
    """

    output_path = Path(
        "outputs/test_creative_image.png"
    )

    tool = CreativeImageTool()

    result = tool.run(
        prompt=prompt,
        output_path=output_path,
    )

    print("Result:", result)
    print("Exists:", output_path.exists())

    if output_path.exists():
        print(
            "Size:",
            output_path.stat().st_size,
            "bytes",
        )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    print("✅ CreativeImageTool test passed!")


if __name__ == "__main__":
    main()