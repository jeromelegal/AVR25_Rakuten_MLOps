import json
from unittest.mock import patch, Mock, mock_open
from api.config.dependencies import (
    load_text_classifier_model,
    load_translator_model,
    load_language_detector_model,
    load_french_words,
)


class TestModelLoader:

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_text_classifier_model(self, mlflow_mock: Mock):
        expected_model_name = "my-model"
        expected_model_version = "my-version"
        expected_mlflow_addr = "my-addr"
        expected_model = Mock()
        expected_tokenizer = Mock()
        mlflow_mock.transformers.load_model.return_value = {
            "model": expected_model,
            "tokenizer": expected_tokenizer,
        }

        model, tokenizer = load_text_classifier_model(
            model_name=expected_model_name,
            model_version=expected_model_version,
            server_addr=expected_mlflow_addr,
        )

        assert model == expected_model
        assert tokenizer == expected_tokenizer
        mlflow_mock.set_tracking_uri.assert_called_once_with(expected_mlflow_addr)
        mlflow_mock.transformers.load_model.assert_called_once_with(
            model_uri=f"models:/{expected_model_name}/{expected_model_version}",
            return_type="components",
        )

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_translator_model(self, mlflow_mock: Mock):
        expected_model_name = "my-model"
        expected_model_version = "my-version"
        expected_mlflow_addr = "my-addr"
        expected_artifact_run_id = "my-artifact_run_id"
        expected_artifact_path = "my-artifact_path"
        expected_destination_path = "my-destination_path"
        expected_model = Mock()
        expected_tokenizer = Mock()
        mlflow_mock.transformers.load_model.return_value = {
            "model": expected_model,
            "tokenizer": expected_tokenizer,
        }

        model, tokenizer = load_translator_model(
            model_name=expected_model_name,
            model_version=expected_model_version,
            server_addr=expected_mlflow_addr,
            artifact_run_id=expected_artifact_run_id,
            artifact_path=expected_artifact_path,
            destination_path=expected_destination_path,
        )

        assert model == expected_model
        assert tokenizer == expected_tokenizer
        mlflow_mock.transformers.load_model.assert_called_once_with(
            model_uri=f"models:/{expected_model_name}/{expected_model_version}",
            return_type="components",
        )
        mlflow_mock.artifacts.download_artifacts.assert_called_once_with(
            run_id=expected_artifact_run_id,
            artifact_path=expected_artifact_path,
            dst_path=expected_destination_path,
        )

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_language_detector_model(self, mlflow_mock: Mock):
        expected_model_name = ("my-model_name",)
        expected_model_version = ("my-model_version",)
        expected_mlflow_addr = ("my-server_addr",)
        expected_artifact_run_id = ("my-artifact_run_id",)
        expected_artifact_path = ("my-artifact_path",)
        expected_destination_path = ("my-destination_path",)
        mocked_model = Mock()
        mlflow_mock.pyfunc.load_model.return_value = mocked_model

        model = load_language_detector_model(
            model_name=expected_model_name,
            model_version=expected_model_version,
            server_addr=expected_mlflow_addr,
            artifact_run_id=expected_artifact_run_id,
            artifact_path=expected_artifact_path,
            destination_path=expected_destination_path,
        )

        assert model == mocked_model
        mlflow_mock.pyfunc.load_model.assert_called_once_with(
            model_uri=f"models:/{expected_model_name}/{expected_model_version}"
        )
        mlflow_mock.artifacts.download_artifacts.assert_called_once_with(
            run_id=expected_artifact_run_id,
            artifact_path=expected_artifact_path,
            dst_path=expected_destination_path,
        )

    def test_get_french_words(self):
        expected_artifact_dir = "my-artifact_dir"
        expected_artifact_path = "my-artifact_path"
        french_words = '["un", "deux", "trois"]'
        with patch("builtins.open", mock_open(read_data=french_words)) as mock_file:
            words = load_french_words(
                artifact_dir=expected_artifact_dir,
                artifact_path=expected_artifact_path,
            )

        assert words == set(json.loads(french_words))
