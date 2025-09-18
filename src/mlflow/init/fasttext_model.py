from typing import List
from mlflow.pyfunc import PythonModel
from mlflow.models import set_model
import fasttext

LANGUAGE_DETECTOR_ARTIFACT_NAME = "text-language-detector-bin"


class FastTextModel(PythonModel):

    def load_context(self, context):
        self.model = fasttext.load_model(
            context.artifacts[LANGUAGE_DETECTOR_ARTIFACT_NAME]
        )

    def predict(self, context, model_input: List[str]):
        return [self.model.predict(i) for i in model_input]


# Define the custom PythonModel instance that will be used for inference
set_model(FastTextModel())
