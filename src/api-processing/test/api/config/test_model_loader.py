from unittest.mock import patch, Mock
from api.config.model_loader import load_classifier


class TestModelLoader:

    @patch("api.config.model_loader.ImageTextClassifier")
    def test_load_classifier(self, classifier_class_mock: Mock):
        clf_mock = Mock()
        expected_text_api_url = "my-text_api_url"
        expected_image_api_url = "my-image_api_url"
        classifier_class_mock.return_value = clf_mock

        model = load_classifier(
            text_api_url=expected_text_api_url, image_api_url=expected_image_api_url
        )

        assert model == clf_mock
        classifier_class_mock.assert_called_once_with(
            text_api_url=expected_text_api_url,
            image_api_url=expected_image_api_url,
        )
