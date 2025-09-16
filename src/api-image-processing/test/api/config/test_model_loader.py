from unittest.mock import patch, Mock
from api.config.model_loader import load_image_classifier_model


class TestModelLoader:

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_load_image_classifier_model(self, mlflow_mock: Mock):
        mocked_model = Mock()
        mlflow_mock.tensorflow.load_model.return_value = mocked_model
        expected_model_name = "my-model"
        expected_model_version = "my-version"
        expected_mlflow_addr = "my-addr"

        model = load_image_classifier_model(
            model_name=expected_model_name,
            model_version=expected_model_version,
            mlflow_addr=expected_mlflow_addr,
        )

        assert model == mocked_model
        mlflow_mock.set_tracking_uri.assert_called_once_with(expected_mlflow_addr)
        mlflow_mock.tensorflow.load_model.assert_called_once_with(
            model_uri=f"models:/{expected_model_name}/{expected_model_version}"
        )
