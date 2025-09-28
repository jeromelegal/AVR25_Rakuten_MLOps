from datetime import datetime, timedelta
import json
import logging
import os
import random
from typing import Dict, List, Optional
from airflow.sdk import DAG, Asset
from airflow.decorators import task

# TODO: Uncommment when API gateway will be ready to return image category
# In the meantime, we use a mock
# from utils.api_gateway_client import APIGatewayClient
from utils.mock.api_gateway_client import MockAPIGatewayClient as APIGatewayClient
from utils.s3_client import S3Client


# Constants
CONN_ID = "minio_s3_conn"
PROCESSED_BUCKET = "processed-images"
TRAIN_BUCKET = "train-images"
TEST_BUCKET = "test-images"
METADATA_BUCKET = "airflow"
TRAIN_STATE_FILE_NAME = "splitted_train_images_distribution.json"
TEST_STATE_FILE_NAME = "splitted_test_images_distribution.json"

API_GATEWAY_SERVICE_NAME = os.getenv("API_GATEWAY_SERVICE_NAME")
API_GATEWAY_USER_NAME = os.getenv("API_GATEWAY_USER_NAME")
API_GATEWAY_USER_PASSWORD = os.getenv("API_GATEWAY_USER_PASSWORD")
API_GATEWAY_USER_EMAIL = os.getenv("API_GATEWAY_USER_EMAIL")
TRAIN_TEST_SPLIT_TARGETED = float(os.getenv("TRAIN_TEST_SPLIT_TARGETED", "0.8"))

processed_images_asset = Asset(f"s3://{PROCESSED_BUCKET}")
train_images_asset = Asset(f"s3://{TRAIN_BUCKET}")
test_images_asset = Asset(f"s3://{TEST_BUCKET}")
train_state_file_asset = Asset(f"s3://{METADATA_BUCKET}/{TRAIN_STATE_FILE_NAME}")
test_state_file_asset = Asset(f"s3://{METADATA_BUCKET}/{TEST_STATE_FILE_NAME}")


# ----- DAG -----
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime.now(),
}


s3_client = S3Client(connection_id=CONN_ID)


def get_image_distribution(s3_client: S3Client, bucket: str, filename: str):
    try:
        images_distribution = json.loads(
            s3_client.get_object(bucket=bucket, filename=filename)
        )
        print(f"images_distribution for {filename}: {images_distribution}")
    except s3_client.exceptions.NoSuchKey:
        images_distribution = {}
        print(f"No previous image distribution found for {filename}.")
    return images_distribution


def get_images_category(api_gateway_client: APIGatewayClient, images: List[str]):
    images_by_category = {}
    for image_id in images:
        image_category = api_gateway_client.get_category_from_image_id(
            image_id=image_id
        )
        if image_category is None:
            continue
        images_by_category[image_category] = images_by_category.get(
            image_category, []
        ) + [image_id]
    return images_by_category


def shuffle_and_split(values, n):
    if n > len(values) or n < 0:
        raise ValueError("n must be between 0 and the length of the list")

    shuffled = values[:]
    random.shuffle(shuffled)
    return shuffled[:n], shuffled[n:]


def split_to_distribution(
    images_by_category: Dict[str, str],
    train_images_distribution: Dict[str, int],
    test_images_distribution: Dict[str, int],
    split: float = TRAIN_TEST_SPLIT_TARGETED,
):
    """
    This function is used to try to reach the desired the stratified split percentage
    denoted 'split' between train and test sets by category.
    To do so, for a given category, let's say we have x elements in the train set and
    y elements in the test set and we want to add n new elements. The problem is to find
    the number of elements to add to x and the number of elements to add to y. Let's
    named them respectively nx and ny. We therefore have this set of equations:
        x + nx = split * (x + y + n)
        n = nx + ny
    The solutions are therefore:
        nx = split * (x + y + n) - x
    nx and ny needs to be integer therefore we decide to take the round value for nx and
    calculate ny as n - nx
    """
    if split > 1 or split < 0:
        raise ValueError(f"'split' argument must be in [0, 1]. Got {split}")
    new_train_images_by_category = {}
    new_test_images_by_category = {}

    for category, images in images_by_category.items():
        x = train_images_distribution.get(category, 0)
        y = test_images_distribution.get(category, 0)
        n = len(images)

        if n == 0:
            continue

        # Split the data
        nx = round(split * (x + y + n) - x)
        train_images, test_images = shuffle_and_split(values=images, n=nx)

        # Store splitted data by category:
        new_train_images_by_category[category] = train_images
        new_test_images_by_category[category] = test_images

    return new_train_images_by_category, new_test_images_by_category


with DAG(
    dag_id="images_train_test_split",
    default_args=default_args,
    description="Split the processed images between train and test sets",
    catchup=False,
    tags=["s3", "images", "assets", "split"],
    schedule=processed_images_asset,
    is_paused_upon_creation=False,
) as dag:

    @task(
        multiple_outputs=True,
        task_display_name="Retrieve images distribution",
    )
    def get_images_distribution_file() -> Dict[str, str]:
        train_images_distribution = get_image_distribution(
            s3_client=s3_client,
            bucket=METADATA_BUCKET,
            filename=TRAIN_STATE_FILE_NAME,
        )
        test_images_distribution = get_image_distribution(
            s3_client=s3_client,
            bucket=METADATA_BUCKET,
            filename=TEST_STATE_FILE_NAME,
        )
        return {
            "train_images_distribution": train_images_distribution,
            "test_images_distribution": test_images_distribution,
        }

    @task(
        task_display_name="Get processed images to split",
    )
    def get_new_files() -> List:
        new_images = s3_client.list_files_from_bucket(bucket=PROCESSED_BUCKET)
        return new_images

    @task.branch(
        task_id="branch_split",
        task_display_name="Check if we need to split new processed images",
    )
    def branch_split(new_images: List, images_distribution: Dict):
        next_steps = []
        if len(new_images) > 0:
            next_steps += ["train_test_split_images"]
        return next_steps

    @task(
        multiple_outputs=True,
        task_display_name="Split images based on the desired distribution",
    )
    def train_test_split_images(ti=None):
        images = ti.xcom_pull(task_ids="get_new_files")
        images_distribution = ti.xcom_pull(task_ids="get_images_distribution_file")
        api_gateway_client = APIGatewayClient(
            username=API_GATEWAY_USER_PASSWORD,
            password=API_GATEWAY_USER_PASSWORD,
            email=API_GATEWAY_USER_EMAIL,
            base_url="https://{API_GATEWAY_SERVICE_NAME}",
        )

        print("Getting images categories...")
        images_by_category = get_images_category(
            api_gateway_client=api_gateway_client, images=images
        )
        print(f"images_by_category = {images_by_category}")

        print("Splitting images by category...")
        new_train_images_by_category, new_test_images_by_category = (
            split_to_distribution(
                images_by_category=images_by_category,
                train_images_distribution=images_distribution[
                    "train_images_distribution"
                ],
                test_images_distribution=images_distribution[
                    "test_images_distribution"
                ],
            )
        )
        print(f"new_train_images_by_category = {new_train_images_by_category}")
        print(f"new_test_images_by_category = {new_test_images_by_category}")

        return {
            "new_train_images_by_category": new_train_images_by_category,
            "new_test_images_by_category": new_test_images_by_category,
        }

    @task.branch(
        task_id="branch_store",
        task_display_name="Check if we need to store new processed images",
    )
    def branch_store(ti=None):
        new_train_images_by_category = ti.xcom_pull(
            task_ids="train_test_split_images", key="new_train_images_by_category"
        )
        new_test_images_by_category = ti.xcom_pull(
            task_ids="train_test_split_images", key="new_test_images_by_category"
        )
        next_steps = []
        if len(new_train_images_by_category) > 0:
            next_steps += ["store_train_images"]
        if len(new_test_images_by_category) > 0:
            next_steps += ["store_test_images"]
        return next_steps

    @task(
        outlets=[train_images_asset, train_state_file_asset],
        task_display_name="Store train images",
    )
    def store_train_images(ti=None):
        images_by_category = ti.xcom_pull(
            task_ids="train_test_split_images", key="new_train_images_by_category"
        )
        images_distribution = ti.xcom_pull(
            task_ids="get_images_distribution_file", key="train_images_distribution"
        )

        print(f"train images: {images_by_category}")
        print(f"train images distribution: {images_distribution}")

        for category, images in images_by_category.items():
            uploaded_images_for_current_category = 0
            # Check if bucket exists otherwise create it
            s3_client.create_folder_in_bucket(bucket=TRAIN_BUCKET, folder_name=category)

            # Move each image from processed folder to train folder
            for image_id in images:
                try:
                    s3_client.move_object_to_folder(
                        old_bucket=PROCESSED_BUCKET,
                        bucket=TRAIN_BUCKET,
                        folder_name=category,
                        object_name=image_id,
                        check_folder_exist=False,
                    )
                    uploaded_images_for_current_category += 1
                except Exception as e:
                    logging.error(f"Impossible to move file {image_id}: {e}")
                    continue

            # Update image distribution
            images_distribution[category] = (
                images_distribution.get(category, 0)
                + uploaded_images_for_current_category
            )

        print(f"new train distribution: {images_distribution}")

        # Upload images distribution
        s3_client.upload_dict_as_json(
            bucket=METADATA_BUCKET, key=TRAIN_STATE_FILE_NAME, data=images_distribution
        )

    @task(
        outlets=[test_images_asset, test_state_file_asset],
        task_display_name="Store test images",
    )
    def store_test_images(ti=None):
        images_by_category = ti.xcom_pull(
            task_ids="train_test_split_images", key="new_test_images_by_category"
        )
        images_distribution = ti.xcom_pull(
            task_ids="get_images_distribution_file", key="test_images_distribution"
        )

        print(f"test images: {images_by_category}")
        print(f"test images distribution: {images_distribution}")

        for category, images in images_by_category.items():
            uploaded_images_for_current_category = 0
            # Check if bucket exists otherwise create it
            s3_client.create_folder_in_bucket(bucket=TEST_BUCKET, folder_name=category)

            # Move each image from processed folder to train folder
            for image_id in images:
                try:
                    s3_client.move_object_to_folder(
                        old_bucket=PROCESSED_BUCKET,
                        bucket=TEST_BUCKET,
                        folder_name=category,
                        object_name=image_id,
                        check_folder_exist=False,
                    )
                    uploaded_images_for_current_category += 1
                except Exception as e:
                    logging.error(f"Impossible to move file {image_id}: {e}")
                    continue

            # Update image distribution
            images_distribution[category] = (
                images_distribution.get(category, 0)
                + uploaded_images_for_current_category
            )

        print(f"new test distribution: {images_distribution}")

        # Upload images distribution
        s3_client.upload_dict_as_json(
            bucket=METADATA_BUCKET, key=TEST_STATE_FILE_NAME, data=images_distribution
        )

    images_distribution = get_images_distribution_file()
    new_images = get_new_files()
    (
        branch_split(new_images=new_images, images_distribution=images_distribution)
        >> [train_test_split_images()]
        >> branch_store()
        >> [store_train_images(), store_test_images()]
    )
