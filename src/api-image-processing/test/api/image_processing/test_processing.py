from fastapi import HTTPException
from api.image_processing.processing import get_categories
from unittest.mock import patch, Mock
import pytest


class TestProcessing:
    @patch(
        "api.image_processing.processing.get_images_predictions", return_value=Mock()
    )
    def test_get_categories(self, mock_get_images_predictions: Mock):
        mock_result = Mock()
        mock_get_images_predictions.return_value = mock_result
        files = [Mock()]
        model = Mock()

        res = get_categories(files=files, model=model)

        mock_get_images_predictions.assert_called_once_with(files=files, model=model)
        assert res == mock_result

    @patch("api.image_processing.processing.get_images_predictions")
    def test_get_categories_raise_exception(self, mock_get_images_predictions: Mock):
        mock_get_images_predictions.side_effect = Exception()

        with pytest.raises(HTTPException) as e:
            get_categories(files=[Mock()], model=Mock())

            assert e.status_code == 500
