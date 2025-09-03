import os

from api.minio.entity.images import store_image, get_buckets, list_files, ImageRaw


class TestImages:
    async def test_store_image(self, mock_settings):
        with open(
            os.path.join("test", "api", "minio", "entity", "demo_image.jpg"),
            "rb",
        ) as f:
            raw = ImageRaw(username="test", content=f.read())
            res = await store_image(raw, tmp_folder=".", settings=mock_settings)

            assert mock_settings.MINIO_BUCKET_NAME in res.bucket_path
            assert "demo_image.jpg" != res.image_id

    async def test_get_all_buckets(self, mock_settings):
        res = await get_buckets(settings=mock_settings)

        assert len(res.buckets) == 1
        assert res.buckets[0].name == mock_settings.MINIO_BUCKET_NAME

    async def test_list_files_in_bucket(self, mock_settings):
        res = await list_files(settings=mock_settings)

        assert hasattr(res, "names")

    async def test_get_all_file_names_in_bucket_with_limit(self, mock_settings):
        pass

    async def test_get_a_single_files_from_bucket(self, mock_settings):
        pass

    async def test_get_a_multiple_files_from_bucket(self, mock_settings):
        pass

    async def test_delete_a_file_from_bucket(self, mock_settings):
        pass

    async def test_delete_mutliple_files_from_bucket(self, mock_settings):
        pass

    async def test_update_a_file_from_bucket(self, mock_settings):
        pass
