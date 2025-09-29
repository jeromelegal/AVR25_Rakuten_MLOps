import json
import os
from typing import Dict
import boto3
from botocore.exceptions import ClientError
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


class S3Client:
    def __init__(self, connection_id: str):
        self._s3 = self.get_s3_client(connection_id=connection_id)

    @property
    def exceptions(self):
        return self._s3.exceptions

    def get_s3_client(self, connection_id: str):
        hook = S3Hook(aws_conn_id=connection_id)
        return hook.get_conn()

    def _folder_key(self, folder_name: str):
        # S3 "folders" are just prefixes ending with '/'
        return f"{folder_name.strip('/')}/"

    def create_folder_in_bucket(self, bucket: str, folder_name: str):
        folder_key = self._folder_key(folder_name=folder_name)
        try:
            # Check if folder marker object exists
            self._s3.head_object(Bucket=bucket, Key=folder_key)
            print(f"Folder '{folder_key}' already exists in bucket '{bucket}'.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # Create empty "folder" marker
                self._s3.put_object(Bucket=bucket, Key=folder_key)
                print(f"Created folder '{folder_key}' in bucket '{bucket}'.")
            else:
                raise

    def move_object_to_folder(
        self,
        bucket,
        folder_name,
        old_bucket,
        object_name,
        check_folder_exist: bool = False,
    ):
        folder_key = self._folder_key(folder_name=folder_name)

        if check_folder_exist:
            self.create_folder_in_bucket(bucket=bucket, folder_name=folder_name)

        # Copy object to new bucket/folder
        copy_source = {"Bucket": old_bucket, "Key": object_name}
        destination_key = f"{folder_key}{object_name.split('/')[-1]}"
        try:
            self._s3.copy_object(
                CopySource=copy_source, Bucket=bucket, Key=destination_key
            )
            print(
                f"Copied '{object_name}' from '{old_bucket}' to '{bucket}/{destination_key}'"
            )

            # Delete from old bucket
            self._s3.delete_object(Bucket=old_bucket, Key=object_name)
            print(f"Deleted '{object_name}' from '{old_bucket}'")
        except ClientError as e:
            print(f"Error moving object: {e}")
            raise

    def get_object(self, bucket: str, filename: str):
        obj = self._s3.get_object(Bucket=bucket, Key=filename)
        return obj["Body"].read().decode()

    def list_files_from_bucket(self, bucket: str):
        # Use pagination to overcome limit of max returned objects
        paginator = self._s3.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket)

        images = []
        for page in page_iterator:
            page_elements = page.get("Contents", [])
            print(f"page_elements: {page_elements}")
            images += [obj["Key"] for obj in page_elements]
        return images

    def upload_dict_as_json(self, bucket: str, key: str, data: Dict):

        json_data = json.dumps(data, indent=2)

        self._s3.put_object(
            Bucket=bucket, Key=key, Body=json_data, ContentType="application/json"
        )

    def download_bucket(self, bucket, local_dir):
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]

                # Skip "folders" (S3 keys ending with '/')
                if key.endswith("/"):
                    continue

                # Build local path
                local_path = os.path.join(local_dir, key)
                local_folder = os.path.dirname(local_path)

                # Create local directories if they don’t exist
                os.makedirs(local_folder, exist_ok=True)

                # Download file
                self._s3.download_file(bucket, key, local_path)
                print(f"Downloaded: s3://{bucket}/{key} -> {local_path}")
