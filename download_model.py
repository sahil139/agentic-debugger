import argparse
import os
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser(description="Download GPT-Oasis model weights via Hugging Face Hub")
    parser.add_argument("--repo-id", default=os.getenv("GPOASIS_REPO_ID", "openai/gpt-oss-20b"), help="Hugging Face repo id")
    parser.add_argument("--revision", default=os.getenv("GPOASIS_REVISION", None), help="Optional revision/commit/tag")
    parser.add_argument("--models-dir", default="./models", help="Target models directory")
    parser.add_argument("--model-name", default="gpt-oasis", help="Folder name under models/")
    args = parser.parse_args()

    models_dir = Path(args.models_dir).resolve()
    target_dir = models_dir / args.model_name

    # 1) Check if model exists
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"Model already present at: {target_dir}")
        return

    models_dir.mkdir(parents=True, exist_ok=True)

    # 2) Download snapshot
    print(f"Downloading '{args.repo_id}' to {target_dir} ...")
    snapshot_download(
        repo_id=args.repo_id,
        revision=args.revision,
        local_dir=str(target_dir),
        local_dir_use_symlinks=False,
        ignore_patterns=["*.md", "*.txt", "*.json"],
    )

    print(f"Download complete. Files saved to: {target_dir}")


if __name__ == "__main__":
    main()


