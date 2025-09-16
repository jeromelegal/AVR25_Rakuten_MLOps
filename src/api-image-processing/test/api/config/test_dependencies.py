from unittest.mock import patch, Mock
from api.config.dependencies import get_image_classifier_model
from mlflow.exceptions import RestException


class TestDependencies:

    @patch("api.config.dependencies.load_image_classifier_model", return_value=Mock())
    def test_get_image_classifier_model(self, loader_mock: Mock):
        mocked_model = Mock()
        loader_mock.return_value = mocked_model

        model = get_image_classifier_model(settings=Mock())

        assert model == mocked_model

    @patch("api.config.dependencies.load_image_classifier_model", return_value=Mock())
    def test_get_image_classifier_model_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = RestException(
            json={"error_code": 500, "message": "Dummy exception"}
        )

        model = get_image_classifier_model(settings=Mock())

        assert model is None
