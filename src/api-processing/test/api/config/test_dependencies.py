from unittest.mock import patch, Mock
from api.config.dependencies import get_classifier


class TestDependencies:

    @patch("api.config.dependencies.load_classifier", return_value=Mock())
    def test_get_classifier(self, loader_mock: Mock):
        mocked_model = Mock()
        loader_mock.return_value = mocked_model

        model = get_classifier(settings=Mock())

        assert model == mocked_model

    @patch("api.config.dependencies.load_classifier", return_value=Mock())
    def test_get_classifier_loader_exception(self, loader_mock: Mock):
        loader_mock.side_effect = ValueError("Dummy error")

        model = get_classifier(settings=Mock())

        assert model is None
