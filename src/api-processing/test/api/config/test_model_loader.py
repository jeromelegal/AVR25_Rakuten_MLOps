from unittest.mock import patch, Mock
from api.config.model_loader import get_classifier


class TestModelLoader:

    @patch("api.config.model_loader.ImageTextClassifier")
    def test_get_classifier_model(self, classifier_class_mock: Mock):
        clf_mock = Mock()
        settings = Mock()
        settings.API_TEXT_PROCESSING_SERVICE_NAME = "service-text"
        settings.API_TEXT_PROCESSING_SERVICE_PORT = 80
        settings.API_IMAGE_PROCESSING_SERVICE_NAME = "service-image"
        settings.API_IMAGE_PROCESSING_SERVICE_PORT = 81

        classifier_class_mock.return_value = clf_mock

        model = get_classifier(settings=settings)

        assert model == clf_mock
        classifier_class_mock.assert_called_once_with(
            text_api_url="https://service-text:80",
            image_api_url="https://service-image:81",
        )
