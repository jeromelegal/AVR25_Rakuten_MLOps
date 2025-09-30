from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from api.processing.processing import get_categories
from unittest.mock import AsyncMock, patch, Mock
import pytest
import logging
from api.processing.classifier import Prediction


class TestProcessing:
    async def test_get_categories(self):
        file = AsyncMock(UploadFile)
        file.filename = "test.jpg"
        file.content_type = "image/jpeg"
        mock_model = Mock()
        expected_result = Prediction(
            category="my-category",
            probability=0.79,
            overall_probabilities={"cat1": 0.79, "cat2": 0.21},
            image_probabilities={"cat1": 0.79, "cat2": 0.21},
            text_probabilities={"cat1": 0.79, "cat2": 0.21},
        )
        mock_model.predict.return_value = expected_result

        res = await get_categories(
            description="my-description",
            designation="my-designation",
            files=[],
            model=mock_model,
        )

        mock_model.predict.assert_called_once_with(
            description="my-description",
            designation="my-designation",
            files=[],
        )
        assert res.model_dump() == expected_result.to_dict()

    async def test_get_categories_raise_exception(self):
        description = "my-description"
        designation = "my-designation"
        files = [AsyncMock(UploadFile)]
        mock_model = Mock()
        mock_model.predict.side_effect = ValueError

        with pytest.raises(HTTPException) as e:
            await get_categories(
                description=description,
                designation=designation,
                files=files,
                model=mock_model,
            )

        assert e.value.status_code == 500


from main import app
import sys
import os

# Configuration propre du PYTHONPATH
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

client = TestClient(app)


DEMO_IMAGE_PATH = os.path.join("test", "demo_image.jpg")


class TestProcessingIntegration:
    def test_predict_integration(self):
        with open(DEMO_IMAGE_PATH, "rb") as f:
            response = client.post(
                "/api/internal/api-processing/predict",
                files={"files": ("demo_image.jpg", f, "image/jpeg")},
            )

        assert (
            response.status_code == 200
        ), f"Predict failed: {response.status_code} {response.text}"
        payload = response.json()

        # Vérifie que la réponse contient bien les champs attendus
        assert "category" in payload
        assert "probability" in payload
        assert "overall_probabilities" in payload
