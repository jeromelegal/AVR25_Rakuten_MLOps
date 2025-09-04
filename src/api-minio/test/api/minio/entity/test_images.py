import os

from api.minio.entity.images import (
    store_image,
    list_files,
    get_image,
    update_image,
    delete_image,
    ImageRaw,
    ImageUpdateRaw,
)

DEFAULT_BUCKET = "raw-images"


class TestImages:
    async def _add_new_file(self, settings):
        with open(
            os.path.join("test", "api", "minio", "entity", "demo_image.jpg"),
            "rb",
        ) as f:
            raw = ImageRaw(username="test", content=f.read())
            res = await store_image(
                image=raw, tmp_folder=".", settings=settings, bucket=DEFAULT_BUCKET
            )
        return res

    async def _delete_file(self, settings, image_id: str):
        await delete_image(
            bucket=DEFAULT_BUCKET,
            image_id=image_id,
            settings=settings,
        )

    async def test_store_image(self, mock_settings):
        res = await self._add_new_file(settings=mock_settings)

        assert DEFAULT_BUCKET in res.bucket_path
        assert "demo_image.jpg" != res.image_id

        await self._delete_file(settings=mock_settings, image_id=res.image_id)

    async def test_list_files_in_bucket(self, mock_settings):
        res = await self._add_new_file(settings=mock_settings)
        image_id = res.image_id

        res = await list_files(bucket=DEFAULT_BUCKET, settings=mock_settings)

        assert len(res.names) >= 1

        await self._delete_file(settings=mock_settings, image_id=image_id)

    async def test_get_a_single_files_from_bucket(self, mock_settings):
        res = await self._add_new_file(settings=mock_settings)

        res = await get_image(
            bucket=DEFAULT_BUCKET,
            image_id=res.image_id,
            settings=mock_settings,
            tmp_folder=".",
        )

        assert res is not None

        await self._delete_file(settings=mock_settings, image_id=res.image_id)

    async def test_delete_a_file_from_bucket(self, mock_settings):
        res = await self._add_new_file(settings=mock_settings)
        image_id = res.image_id

        res = await delete_image(
            bucket=DEFAULT_BUCKET,
            image_id=res.image_id,
            settings=mock_settings,
        )

        assert res.deleted_image == image_id

    async def test_update_a_file_from_bucket(self, mock_settings):
        with open(
            os.path.join("test", "api", "minio", "entity", "demo_image.jpg"),
            "rb",
        ) as f:
            content = f.read()
            raw = ImageRaw(username="test", content=content)
            res = await store_image(
                image=raw, tmp_folder=".", settings=mock_settings, bucket=DEFAULT_BUCKET
            )
            update = ImageUpdateRaw(
                username="test", content=content, image_id=res.image_id
            )

            res = await update_image(
                bucket=DEFAULT_BUCKET,
                update=update,
                settings=mock_settings,
                tmp_folder=".",
            )

            assert DEFAULT_BUCKET in res.bucket_path
            assert "demo_image.jpg" != res.image_id

            await self._delete_file(settings=mock_settings, image_id=res.image_id)
