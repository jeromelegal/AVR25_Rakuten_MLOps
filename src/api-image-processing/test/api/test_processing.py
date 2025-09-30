from fastapi import HTTPException
from fastapi.testclient import TestClient
from api.image_processing.processing import get_categories
from unittest.mock import AsyncMock, patch, Mock
import pytest


class TestProcessing:
    @patch(
        "api.image_processing.processing.get_images_predictions", return_value=Mock()
    )
    async def test_get_categories(self, mock_get_images_predictions: Mock):
        mock_result = Mock()
        mock_get_images_predictions.return_value = mock_result
        files = [AsyncMock()]
        model = Mock()

        res = await get_categories(files=files, model=model)

        mock_get_images_predictions.assert_called_once_with(
            files=[await file.read() for file in files], model=model
        )
        assert res == mock_result

    @patch("api.image_processing.processing.get_images_predictions")
    async def test_get_categories_raise_exception(
        self, mock_get_images_predictions: Mock
    ):
        mock_get_images_predictions.side_effect = Exception()

        with pytest.raises(HTTPException) as e:
            await get_categories(files=[AsyncMock()], model=Mock())

            assert e.status_code == 500


# from main import app
# import sys
# import os

# # Configuration propre du PYTHONPATH
# sys.path.insert(
#     0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# )

# DEMO_IMAGE_PATH = os.path.join("test", "demo_image.jpg")
# client = TestClient(app)


# class TestProcessingIntegration:

#     def test_api_image_processing_predict(self):

#         with open(DEMO_IMAGE_PATH, "rb") as f:
#             response = client.post(
#                 "/api/internal/api-processing/predict",
#                 files={"files": ("demo_image.jpg", f, "image/jpeg")},
#             )

#         assert (
#             response.status_code == 200
#         ), f"Unexpected status: {response.status_code} {response.text}"

#         # Parse the response
#         result_data = response.json()
#         assert "category_codes" in result_data
#         assert "results" in result_data
#         assert len(result_data["results"]) > 0

#         # Check fields of the first result
#         first_result = result_data["results"][0]
#         assert "input" in first_result
#         assert "categories_probabilities" in first_result
#         assert "predicted_category" in first_result
