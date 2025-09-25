from datetime import datetime, timedelta
from typing import List
from airflow.sdk import DAG, Asset
from airflow.decorators import task
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.timetables.assets import AssetOrTimeSchedule
from airflow.timetables.trigger import CronTriggerTimetable
import io
import logging

# Constants
INIT_NUMBER_OF_FILES_TO_TRIGGER_PROCESS = 5
CONN_ID = "minio_s3_conn"
RAW_BUCKET = "raw-images"
PROCESSED_BUCKET = "processed-images"
METADATA_BUCKET = "airflow"
METADATA_CONTENT_TYPE_KEY = "ContentType"
METADATA_SIZE_KEY = "Size"
METADATA_KEY_KEY = "Key"
METADATA_KEYS = [METADATA_CONTENT_TYPE_KEY, METADATA_SIZE_KEY, METADATA_KEY_KEY]
ALLOWED_CONTENT_TYPES = ["image/jpeg"]
STATE_FILE_NAME = "processed_images.json"
PROCESSED_TAG = "processed"

raw_images = Asset(f"s3://{RAW_BUCKET}")
processed_images = Asset(f"s3://{PROCESSED_BUCKET}")
state_file = Asset(f"s3://{METADATA_BUCKET}/{STATE_FILE_NAME}")

number_of_files_threshold: int = INIT_NUMBER_OF_FILES_TO_TRIGGER_PROCESS


def check_fn(
    files: List,
    **kwargs,
) -> bool:
    print(f"type: {type(files[0])}")
    candidates = []

    for file in files:
        correct_content_type = (
            file.get(METADATA_CONTENT_TYPE_KEY) in ALLOWED_CONTENT_TYPES
        )
        correct_tag = True

        if correct_content_type and correct_tag:
            candidates.append(file)

    return len(candidates) >= number_of_files_threshold


# Dummy image processing function
def process_image(content: bytes) -> bytes:
    return content[::-1]


# ----- DAG -----
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="s3_image_processing_assets",
    default_args=default_args,
    description="Process new images from raw-images to processed-images",
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["s3", "images", "assets", "preprocessing"],
    schedule=AssetOrTimeSchedule(
        timetable=CronTriggerTimetable(
            "0/5 * * * *", timezone="UTC"
        ),  # TODO: set to every 30 minutes
        assets=(raw_images | state_file),
    ),
) as dag:
    print(f"raw_images.name: {raw_images.name}")
    print(f"RAW_BUCKET: {RAW_BUCKET}")

    @task
    def get_new_files(force_process: bool = False) -> list:
        """Find new files in raw-images bucket compared to state in airflow bucket."""
        hook = S3Hook(aws_conn_id=CONN_ID)
        s3 = hook.get_conn()

        # Use pagination to overcome limit of max returned objects
        paginator = s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=RAW_BUCKET)

        candidates = []
        for page in page_iterator:
            page_elements = page.get("Contents", [])

            if force_process:
                filtered_objects = [obj["Key"] for obj in page_elements]
            else:
                filtered_objects = []
                for key in [obj["Key"] for obj in page_elements]:
                    tags = s3.get_object_tagging(Bucket=RAW_BUCKET, Key=key)
                    if (
                        tags is None
                        or tags == {}
                        or tags.get("TagSet") is None
                        or (
                            PROCESSED_TAG
                            not in [tag.get("Key") for tag in tags["TagSet"]]
                        )
                    ):
                        filtered_objects.append(key)
                        continue

                    for tag in tags.items():
                        if (
                            tag.get("Key") == PROCESSED_TAG
                            and tag.get("Value") == "False"
                        ):
                            filtered_objects.append(key)
                            break

            for key in filtered_objects:
                if (
                    s3.head_object(Bucket=RAW_BUCKET, Key=key).get(
                        METADATA_CONTENT_TYPE_KEY
                    )
                    in ALLOWED_CONTENT_TYPES
                ):
                    candidates += [key]

        # Load processed state
        try:
            obj = s3.get_object(Bucket=METADATA_BUCKET, Key=STATE_FILE_NAME)
            seen_files = set(obj["Body"].read().decode().splitlines())
        except s3.exceptions.NoSuchKey:
            seen_files = set()

        new_files = [f for f in candidates if f not in seen_files]

        print(f"new_files: {new_files}")

        if len(new_files) >= INIT_NUMBER_OF_FILES_TO_TRIGGER_PROCESS:
            return new_files
        return []

    @task(outlets=[state_file])
    def process_and_store(files: list):
        """Process each new file and upload results + update state file."""
        if not files:
            return "No new files to process."
        print(f"files: {files}")

        hook = S3Hook(aws_conn_id=CONN_ID)
        s3 = hook.get_conn()

        processed_files = []

        for key in files:
            obj = s3.get_object(Bucket=RAW_BUCKET, Key=key)
            raw_content = obj["Body"].read()

            processed_content = process_image(raw_content)

            # Upload processed result
            s3.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=key,
                Body=processed_content,
            )
            processed_files.append(key)

        # Update state file in airflow bucket
        # Fetch current state first
        try:
            obj = s3.get_object(Bucket=METADATA_BUCKET, Key=STATE_FILE_NAME)
            seen_files = set(obj["Body"].read().decode().splitlines())
        except s3.exceptions.NoSuchKey:
            seen_files = set()

        seen_files.update(processed_files)

        s3.put_object(
            Bucket=METADATA_BUCKET,
            Key=STATE_FILE_NAME,
            Body="\n".join(sorted(seen_files)),
        )

        return f"Processed {len(files)} files."

    files = get_new_files()
    process_and_store(files=files)
