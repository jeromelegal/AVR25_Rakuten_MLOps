import os

from api.minio.entity.images import store_image, ImageRaw


class TestImages:
    async def test_store_image(self, mock_settings):
        with open(
            os.path.join("test", "api", "minio", "entity", "demo_image.jpg"),
            "rb",
        ) as f:
            raw = ImageRaw(username="test", content=f.read())
            res = await store_image(raw, tmp_folder=".", settings=mock_settings)
            print(res)
