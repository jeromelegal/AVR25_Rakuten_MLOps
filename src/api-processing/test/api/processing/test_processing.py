from fastapi import HTTPException
from api.processing.processing import get_categories, AdToClassify
from unittest.mock import patch, Mock
import pytest
import logging


class TestProcessing:
    async def test_get_categories(self):
        ad = AdToClassify(
            description="my-description",
            designation="my-designation",
            file=[bytes([0, 1, 2])],
        )
        mock_model = Mock()
        expected_result = {
            "category": "my-category",
            "probability": 0.79,
            "overall_probabilities": {"cat1": 0.79, "cat2": 0.21},
            "image_probabilities": {"cat1": 0.79, "cat2": 0.21},
            "text_probabilities": {"cat1": 0.79, "cat2": 0.21},
        }
        mock_model.predict.return_value = expected_result

        res = await get_categories(ad=ad, model=mock_model)

        mock_model.predict.assert_called_once_with(
            description=ad.description, designation=ad.designation, files=[ad.file]
        )
        assert res.model_dump() == expected_result

    async def test_get_categories_raise_exception(self):
        ad = AdToClassify(
            description="my-description",
            designation="my-designation",
            file=[bytes([0, 1, 2])],
        )
        mock_model = Mock()
        mock_model.predict.side_effect = ValueError

        with pytest.raises(HTTPException) as e:
            await get_categories(ad=ad, model=mock_model)

        assert e.value.status_code == 500
