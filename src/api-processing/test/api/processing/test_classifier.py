from unittest.mock import patch, Mock, call
import pytest

from api.processing.classifier import (
    Prediction,
    ImageTextClassifier,
    RAKUTEN_CATEGORIES,
)


class TestPredictionClass:
    def test_prediction_to_dict(self):
        expected_category = "expected_category"
        expected_probability = 0.3
        expected_overall_probabilities = {"cat1": 0.68, "cat2": 0.32}
        expected_image_probabilities = {"cat1": 0.6, "cat2": 0.4}
        expected_text_probabilities = {"cat1": 0.8, "cat2": 0.2}
        pred = Prediction(
            category=expected_category,
            probability=expected_probability,
            overall_probabilities=expected_overall_probabilities,
            image_probabilities=expected_image_probabilities,
            text_probabilities=expected_text_probabilities,
        )
        expected_dict = {
            "category": expected_category,
            "probability": expected_probability,
            "overall_probabilities": expected_overall_probabilities,
            "image_probabilities": expected_image_probabilities,
            "text_probabilities": expected_text_probabilities,
        }

        res = pred.to_dict()

        assert res == expected_dict


class TestImageTextClassifier:
    def test_constructor(self):
        assert (
            ImageTextClassifier(
                text_api_url="text_api_url",
                image_api_url="image_api_url",
                text_classifier_weight=0.3,
                timeout=2,
            )
            is not None
        )

    @pytest.mark.parametrize("wrong_weight", [-0.1, 1.2])
    def test_constructor_wrong_weight_raise_exception(self, wrong_weight):
        with pytest.raises(ValueError) as e:
            ImageTextClassifier(
                text_api_url="text_api_url",
                image_api_url="image_api_url",
                text_classifier_weight=wrong_weight,
                timeout=2,
            )

            assert "Argument text_classifier_weight must be in [0, 1]" in str(e)

    @patch("api.processing.classifier.requests")
    def test_predict_correct_api_answer(self, mocked_request: Mock):
        description = "my-description"
        designation = "my-designation"
        files = []
        expected_text_api_url = "text_api_url"
        expected_image_api_url = "image_api_url"
        expected_timeout = 7
        clf = ImageTextClassifier(
            text_api_url=expected_text_api_url,
            image_api_url=expected_image_api_url,
            text_classifier_weight=0.3,
            timeout=expected_timeout,
        )
        request_result = Mock()
        request_result.status_code = 200
        request_result.json.return_value = {
            "category_codes": list(RAKUTEN_CATEGORIES.keys()),
            "results": [
                {
                    "predicted_category": 10,
                    "categories_probabilities": [0.7, 0.2, 0.1]
                    + [0] * (len(RAKUTEN_CATEGORIES) - 3),
                }
            ],
        }
        mocked_request.post.return_value = request_result
        expected_post_calls = [
            call(
                url=expected_text_api_url,
                data={
                    "inputs": [{"description": description, "designation": designation}]
                },
                files=None,
                timeout=expected_timeout,
            ),
            call(
                url=expected_image_api_url,
                data=None,
                files=files,
                timeout=expected_timeout,
            ),
        ]

        clf.predict(description=description, designation=designation, files=files)

        assert mocked_request.post.call_count == 2
        mocked_request.post.assert_has_calls(calls=expected_post_calls, any_order=True)
