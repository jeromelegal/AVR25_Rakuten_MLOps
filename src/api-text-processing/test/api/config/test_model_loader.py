import json
from unittest.mock import patch, Mock, mock_open
from api.config.model_loader import (
    get_text_classifier_model,
    get_translator_model,
    get_language_detector_model,
    get_french_words,
)


class TestModelLoader:

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_text_classifier_model(self, mlflow_mock: Mock):
        mocked_models = {"model": Mock(), "tokenizer": Mock()}
        mlflow_mock.transformers.load_model.return_value = mocked_models

        model, tokenizer = get_text_classifier_model(settings=Mock())

        assert model == mocked_models["model"]
        assert tokenizer == mocked_models["tokenizer"]

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_translator_model(self, mlflow_mock: Mock):
        mocked_models = {"model": Mock(), "tokenizer": Mock()}
        mlflow_mock.transformers.load_model.return_value = mocked_models
        settings = Mock()

        model, tokenizer = get_translator_model(settings=settings)

        assert model == mocked_models["model"]
        assert tokenizer == mocked_models["tokenizer"]
        mlflow_mock.artifacts.download_artifacts.assert_called_once_with(
            run_id=settings.MLFLOW_TEXT_TRANSLATOR_ARTIFACT_RUN_ID,
            artifact_path=settings.MLFLOW_TEXT_TRANSLATOR_CACHE_ARTIFACT_PATH,
            dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
        )

    @patch("api.config.model_loader.mlflow", return_value=Mock())
    def test_get_language_detector_model(self, mlflow_mock: Mock):
        mocked_model = Mock()
        mlflow_mock.pyfunc.load_model.return_value = mocked_model
        settings = Mock()

        model = get_language_detector_model(settings=settings)

        assert model == mocked_model
        mlflow_mock.artifacts.download_artifacts.assert_called_once_with(
            run_id=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_ARTIFACT_RUN_ID,
            artifact_path=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH,
            dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
        )

    def test_get_french_words(self):
        settings = Mock()
        settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH = "index.json"
        french_words = '["un", "deux", "trois"]'
        with patch("builtins.open", mock_open(read_data=french_words)) as mock_file:
            words = get_french_words(settings=settings)

        assert words == set(json.loads(french_words))
