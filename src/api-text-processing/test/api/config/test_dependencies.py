from unittest.mock import patch, Mock
from api.config.dependencies import (
    get_french_words,
    get_language_detector_model,
    get_text_classifier_model,
    get_translator_model,
)
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


class TestDependencies:

    @patch("api.config.dependencies.load_text_classifier_model", return_value=Mock())
    def test_get_text_classifier_model(self, loader_mock: Mock):
        expected_model = Mock()
        expected_tokenizer = Mock()
        loader_mock.return_value = expected_model, expected_tokenizer

        model, tokenizer = get_text_classifier_model(settings=Mock())

        assert model == expected_model
        assert tokenizer == expected_tokenizer

    @patch("api.config.dependencies.load_text_classifier_model", return_value=Mock())
    def test_get_text_classifier_model_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = RestException(
            json={"error_code": 500, "message": "Dummy exception"}
        )

        model = get_text_classifier_model(settings=Mock())

        assert model == (None, None)
        loader_mock.cache_clear.assert_called_once()

    @patch("api.config.dependencies.load_translator_model", return_value=Mock())
    def test_get_translator_model(self, loader_mock: Mock):
        expected_model = Mock()
        expected_tokenizer = Mock()
        loader_mock.return_value = expected_model, expected_tokenizer

        model, tokenizer = get_translator_model(settings=Mock())

        assert model == expected_model
        assert tokenizer == expected_tokenizer

    @patch("api.config.dependencies.load_translator_model", return_value=Mock())
    def test_get_translator_model_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = RestException(
            json={"error_code": 500, "message": "Dummy exception"}
        )

        model = get_translator_model(settings=Mock())

        assert model == (None, None)
        loader_mock.cache_clear.assert_called_once()

    @patch("api.config.dependencies.load_language_detector_model", return_value=Mock())
    def test_get_language_detector_model(self, loader_mock: Mock):
        expected_model = Mock()
        loader_mock.return_value = expected_model

        model = get_language_detector_model(settings=Mock())

        assert model == expected_model

    @patch("api.config.dependencies.load_language_detector_model", return_value=Mock())
    def test_get_language_detector_model_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = RestException(
            json={"error_code": 500, "message": "Dummy exception"}
        )

        model = get_language_detector_model(settings=Mock())

        assert model == None
        loader_mock.cache_clear.assert_called_once()

    @patch("api.config.dependencies.load_french_words", return_value=Mock())
    def test_get_language_detector_model(self, loader_mock: Mock):
        expected_model = Mock()
        loader_mock.return_value = expected_model

        model = get_french_words(settings=Mock())

        assert model == expected_model

    @patch("api.config.dependencies.load_french_words", return_value=Mock())
    def test_get_language_detector_model_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = RestException(
            json={"error_code": 500, "message": "Dummy exception"}
        )

        model = get_french_words(settings=Mock())

        assert model == None
        loader_mock.cache_clear.assert_called_once()
