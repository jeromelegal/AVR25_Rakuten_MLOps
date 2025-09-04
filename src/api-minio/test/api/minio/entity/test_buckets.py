from api.minio.entity.buckets import (
    get_buckets,
    create_bucket,
    delete_bucket,
)
from fastapi import HTTPException


class TestBuckets:

    async def _create_bucket(self, bucket_name: str, settings):
        try:
            await create_bucket(bucket_name=bucket_name, settings=settings)
        except HTTPException:
            pass

    async def _delete_bucket(self, bucket_name: str, settings):
        try:
            await delete_bucket(bucket_name=bucket_name, settings=settings)
        except HTTPException:
            pass

    async def test_create_and_get_bucket(self, mock_settings):
        bucket_name = "my-bucket-test"
        await self._delete_bucket(bucket_name=bucket_name, settings=mock_settings)

        await create_bucket(bucket_name=bucket_name, settings=mock_settings)

        buckets = await get_buckets(settings=mock_settings)
        assert bucket_name in [bucket.name for bucket in buckets.buckets]

        await self._delete_bucket(bucket_name=bucket_name, settings=mock_settings)

    async def test_remove_bucket(self, mock_settings):
        bucket_name = "my-bucket-test"
        await self._create_bucket(bucket_name=bucket_name, settings=mock_settings)

        res = await delete_bucket(bucket_name=bucket_name, settings=mock_settings)

        buckets = await get_buckets(settings=mock_settings)
        bucket_names = [bucket.name for bucket in buckets.buckets]
        assert bucket_name not in bucket_names
        assert res.name == bucket_name
