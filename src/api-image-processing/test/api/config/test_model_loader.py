from unittest.mock import patch, Mock
from api.config.model_loader import get_image_classifier_model, get_settings


class TestModelLoader:

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_image_classifier_model(self, mlflow_mock):
        mocked_model = Mock()
        mlflow_mock.tensorflow.load_model.return_value = mocked_model

        model = get_image_classifier_model(settings=Mock())

        assert model == mocked_model
