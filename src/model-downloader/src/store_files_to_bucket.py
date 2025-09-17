import sys
import logging
from config import get_settings
from s3 import get_client


FILES_TO_BE_UPLOADED = [
    "translation_cache_english.pkl",
    "index.json",
    "models/lid.176.bin",
    "models/distilbert/config.json",
    "models/distilbert/model.safetensors",
    "models/distilbert/special_tokens_map.json",
    "models/distilbert/tokenizer_config.json",
    "models/distilbert/tokenizer.json",
    "models/distilbert/training_args.bin",
    "models/distilbert/vocab.txt",
    "models/nllb-200/config.json",
    "models/nllb-200/generation_config.json",
    "models/nllb-200/model.safetensors",
    "models/nllb-200/sentencepiece.bpe.model",
    "models/nllb-200/special_tokens_map.json",
    "models/nllb-200/tokenizer_config.json",
    "models/nllb-200/tokenizer.json",
    "combined_trained_model_no_output.keras",
]


def name_in_bucket(file_path: str, sep: str = "-"):
    return sep.join(file_path.rsplit("/"))


def main(dir_path: str):
    logging.info("Collecting settings")
    settings = get_settings()

    logging.info("Getting Minio client")
    client = get_client(settings=settings)

    logging.info(f"Uploading files from {dir_path}:")
    for file_path in FILES_TO_BE_UPLOADED:
        logging.info(f"\tUploading {file_path}")
        path = f"{dir_path}/{file_path}"
        client.upload_file(
            path,
            settings.MINIO_MODEL_BUCKET_NAME,
            name_in_bucket(file_path=file_path),
        )


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    if len(sys.argv) < 2:
        raise ValueError("Must have at least one argument")

    main(dir_path=sys.argv[1])
