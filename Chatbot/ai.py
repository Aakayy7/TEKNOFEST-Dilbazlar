import numpy as np

from utils import get_configs
import logging
import os
from dotenv import load_dotenv
load_dotenv()


import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import HfApi

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SOTA:
    """
    This model comprehends all state-of-the-art models in this project.
    """
    def __init__(self):
        self.anxiety_labels = ['Agorafobi', 'Panik', 'Fobi', 'Seçici Dilsizlik', 'Sosyal Anksiyete']
        self.depression_labels = ['Distimi', 'PMDD']
        self.disorder_or_not_labels = ["Normal", "Hastalık"]
        self.depression_detect_labels = ["Normal", "Depresyon"]
        self.anxiety_detect_labels = ["Normal", "Anksiyete"]

        self.message_counter = 0
        self.results = []
        self.disorder_ratio = 0
        self.disorders_percentages = {
            "Normal": 0,
            "Depresyon": 0,
            "Anksiyete": 0,
            "PMDD": 0,
            "Distimi": 0,
            "Agorafobi": 0,
            "Panik": 0,
            "Fobi": 0,
            "Seçici Dilsizlik": 0,
            "Sosyal Anksiyete": 0
        }
        self.normalized_percentages = {
            "Normal": 0,
            "Depresyon": 0,
            "Anksiyete": 0,
            "PMDD": 0,
            "Distimi": 0,
            "Agorafobi": 0,
            "Panik": 0,
            "Fobi": 0,
            "Seçici Dilsizlik": 0,
            "Sosyal Anksiyete": 0
        }

        self._setup_logger()
        self._connect_hugging_face()
        self.configs = get_configs()
        (self.anxiety_trainer, self.depression_trainer,
         self.disorder_or_not_trainer, self.anx_detect_trainer,
         self.dep_detect_trainer) = self.load_models()

    def _setup_logger(self):
        """
        Setting logger to make logging properly.
        :return:
        """
        # Configure the logger
        self.logger = logging.getLogger('HuggingFaceLogin')
        self.logger.setLevel(logging.DEBUG)

        # Create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        self.logger.addHandler(ch)

    def update_percentages(self):
        """
        Update distributions of disorders. It is generally run periodically.
        :return:
        """

        # Specify main distribution by adding one
        for element in self.results:
            self.disorders_percentages[element['result']] += 1

        # It calculates total percentage
        total_percentage = sum(self.disorders_percentages.values())


        # Normalize distributions
        self.normalized_percentages = {k: (v / total_percentage) * 100 if total_percentage > 0 else 0
                                  for k, v in self.disorders_percentages.items()}

        self.logger.info("Percentages calculated")


    @staticmethod
    def _connect_hugging_face():
        """
        Connecting to HuggingFace
        :return:
        """
        api = HfApi(os.environ.get('HG_ACCESS_TOKEN'))
        print("Successfully logged in Huggingface!")

    def empty_cache(self):
        """
        Make empty cache such as message_counter, model results, disorder percentages.
        :return:
        """
        self.message_counter = 0
        self.results = []

        self.disorders_percentages = {
            "Normal": 0,
            "Depresyon": 0,
            "Anksiyete": 0,
            "PMDD": 0,
            "Distimi": 0,
            "Agorafobi": 0,
            "Panik": 0,
            "Fobi": 0,
            "Seçici Dilsizlik": 0,
            "Sosyal Anksiyete": 0
        }
        self.logger.info("Counter and Results were cleaned.")

    def load_models(self):
        """
        Load Anxiety, depression, disorder or not, anxiety detection and depression detection.
        :return: anxiety_model, depression_model, disorder_or_not_model, anxiety_detection model, depression_detection model
        """
        anxiety_model = self._load_single_model(model_url=self.configs["ANXIETY_MODEL_ID"], num_labels=5)
        depression_model = self._load_single_model(model_url=self.configs["DEPRESSION_MODEL_ID"], num_labels=2)
        disorder_or_not_model = self._load_single_model(model_url=self.configs["DISORDER_MODEL_ID"], num_labels=2)
        anx_detect_model = self._load_single_model(model_url=self.configs["ANX_DETECT_MODEL_ID"], num_labels=2)
        dep_detect_model = self._load_single_model(model_url=self.configs["DEP_DETECT_MODEL_ID"], num_labels=2)

        self.logger.info("All huggingface models have been loaded.")
        return anxiety_model, depression_model, disorder_or_not_model, anx_detect_model, dep_detect_model

    @staticmethod
    def _load_single_model(model_url: str, num_labels: int):
        """
        it loads single model and returns
        :param model_url: the huggingface url of the url
        :param num_labels: number of labels of this model
        :return:
        """

        model = AutoModelForSequenceClassification.from_pretrained(
            model_url,
            num_labels=num_labels)
        tokenizer = AutoTokenizer.from_pretrained(model_url)

        # Move the model to the appropriate device
        global device
        model.to(device)

        # Ensure model is in evaluation mode
        model.eval()

        return {
            'model': model,
            'tokenizer': tokenizer
        }

    @staticmethod
    def predict(model, tokenizer, labels, input_text):
        """
        AI prediction process

        :param model: Loaded huggingface model
        :param tokenizer: Loaded huggingface tokenizer
        :param labels: Model labels in list format
        :param input_text: Input text to predict
        :return:
        """
        inputs = tokenizer(input_text, max_length=150, padding="max_length", truncation=True, return_tensors="pt")

        # Move the inputs to the appropriate device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Disable gradient computation for inference
        with torch.no_grad():
            # Forward pass to get outputs
            outputs = model(**inputs)

            # Get the prediction
            # Note: `AutoModel` might not include logits. Ensure you use the appropriate model class for your task.
            if hasattr(outputs, 'logits'):
                preds = torch.argmax(outputs.logits, dim=-1)
            else:
                # Handle the case where the model does not have logits (e.g., outputs are raw hidden states)
                preds = torch.argmax(outputs[0], dim=-1)

        # Convert prediction to numpy array and print (if needed)
        prediction = preds.cpu().numpy()[0]

        return labels[prediction], outputs

    def update_disorder_ratio(self):
        """
        Update disorder ratio
        :return: disorder ratio
        """
        temp_counter = 0
        print("Results: ", self.results)

        for element in self.results:
            if element['result'] != 'Normal':
                temp_counter += 1

        print("temp_counter: ", temp_counter)
        print("Length: ", len(self.results))

        disorder_ratio = round(temp_counter/len(self.results), 2)
        self.logger.info(f"Disorder was updated. Updated disorder ratio: {disorder_ratio}")

        return disorder_ratio

    def anxiety_predict(self, sentence):
        """
        Prediction process for anxiety specifically.
        :param sentence: input_text for anxiety prediction
        :return:
        """

        label, outputs_probs = self.predict(model=self.anxiety_trainer['model'],
                                            tokenizer=self.anxiety_trainer['tokenizer'],
                                            labels=self.anxiety_labels,
                                            input_text=sentence)

        return label, outputs_probs.logits

    def depression_predict(self, sentence):
        """
        Prediction process for depression specifically.
        :param sentence: input_text for depression
        :return: label, outputs_probs
        """
        label, outputs_probs = self.predict(model=self.depression_trainer['model'],
                                            tokenizer=self.depression_trainer['tokenizer'],
                                            labels=self.depression_labels,
                                            input_text=sentence)

        return label, outputs_probs.logits

    def anx_detect_predict(self, sentence):
        """
        Prediction process for anxiety detection.
        :param sentence: input_text for anxiety
        :return: label, outputs_probs
        """
        label, outputs_probs = self.predict(model=self.anx_detect_trainer['model'],
                                            tokenizer=self.anx_detect_trainer['tokenizer'],
                                            labels=self.anxiety_detect_labels,
                                            input_text=sentence)

        self.logger.info(f"Anxiety detection model probs: {outputs_probs}")

        return label, outputs_probs.logits

    def dep_detect_predict(self, sentence):
        """
        Prediction process for depression detection.
        :param sentence: input_text for depression
        :return: label, outputs_probs
        """
        label, outputs_probs = self.predict(model=self.dep_detect_trainer['model'],
                                            tokenizer=self.dep_detect_trainer['tokenizer'],
                                            labels=self.depression_detect_labels,
                                            input_text=sentence)

        self.logger.info(f"Depression detection model probs: {outputs_probs}")

        return label, outputs_probs.logits

    def disorder_or_not_predict(self, sentence):
        """
        Disorder or not model prediction
        :param sentence: input text
        :return: label
        """
        label, outputs_probs = self.predict(model=self.disorder_or_not_trainer['model'],
                                            tokenizer=self.disorder_or_not_trainer['tokenizer'],
                                            labels=self.disorder_or_not_labels,
                                            input_text=sentence)

        self.logger.info(f"Is disorder detection model probs: {outputs_probs}")
        if float(outputs_probs.logits[0, 1]) > self.configs['is_disorder_threshold']:
            return label
        else:
            return "Normal"

    def prediction_flow_standard(self, sentence):
        """
        It manages the condition state of the prediction progress. (Main Runnable version)
        :param sentence: input_text
        :return: specific disorder result
        """

        # Is it disorder or not
        is_disorder_result_label = self.disorder_or_not_predict(sentence)
        specific_result = ""

        # For Normal result
        if is_disorder_result_label == 'Normal':
            self.logger.info(f"This sentence is {is_disorder_result_label}")

            return "Normal"

        # Hastalık
        else:
            self.logger.info(f"This sentence is {is_disorder_result_label}")

            anx_result_label, anx_probs = self.anx_detect_predict(sentence)
            dep_result_label, dep_probs = self.dep_detect_predict(sentence)
            anx_dep_result = ""

            if anx_probs[0, 0] > anx_probs[0, 1] and dep_probs[0, 0] < dep_probs[0, 1]:
                anx_dep_result = "Depresyon"
            elif anx_probs[0, 0] < anx_probs[0, 1] and dep_probs[0, 0] > dep_probs[0, 1]:
                anx_dep_result = "Anksiyete"
            elif anx_probs[0, 0] > anx_probs[0, 1] and dep_probs[0, 0] > dep_probs[0, 1]: # There is not like anxiety or depression
                anx_dep_result = "Normal"

            # Both of them are high
            elif anx_probs[0, 0] < anx_probs[0, 1] and dep_probs[0, 0] < dep_probs[0, 1]:
                if anx_probs[0, 1] > self.configs['anxiety_detection_threshold'] and dep_probs[0, 1] > self.configs['depression_detection_threshold']:
                    anx_dep_result = "Anksiyete ve Depresyon"
                elif anx_probs[0, 1] > self.configs['anxiety_detection_threshold']:
                    anx_dep_result = "Anksiyete"
                elif dep_probs[0, 1] > self.configs['depression_detection_threshold']:
                    anx_dep_result = "Depresyon"
                else: # If both of them are less then thresholds
                    if anx_probs[0, 1] > dep_probs[0, 1]:
                        anx_dep_result = "Anksiyete"
                    elif anx_probs[0, 1] < dep_probs[0, 1]:
                        anx_dep_result = "Depresyon"

            self.logger.info(f"Anx Dep Result: {anx_dep_result}")

            # Specific part of prediction
            if anx_dep_result == 'Depresyon':
                specific_result, dep_specific_probs = self.depression_predict(sentence)
                if dep_specific_probs[0, np.argmax(dep_specific_probs)] < self.configs['depression_specific_threshold']:
                    specific_result = "Depresyon"
                self.logger.info(f"Depression Specific Probs: {dep_specific_probs}")

            elif anx_dep_result == 'Anksiyete':
                specific_result, anx_specific_probs = self.anxiety_predict(sentence)
                if anx_specific_probs[0, np.argmax(anx_specific_probs)] < self.configs['anxiety_specific_threshold']:
                    specific_result = "Anksiyete"
                self.logger.info(f"Anxiety Specific Probs: {anx_specific_probs}")

            elif anx_dep_result == 'Anksiyete ve Depresyon':
                specific_result = []
                specific_result_1, dep_specific_probs = self.depression_predict(sentence)
                specific_result_2, anx_specific_probs = self.anxiety_predict(sentence)

                # Conditions when it comes anxiety and depression at the same time.
                if anx_specific_probs[0, np.argmax(anx_specific_probs)] < self.configs['anxiety_specific_threshold']:
                    specific_result.append("Anksiyete")
                else:
                    specific_result.append(specific_result_2)
                if dep_specific_probs[0, np.argmax(dep_specific_probs)] < self.configs['depression_specific_threshold']:
                    specific_result.append("Depresyon")
                else:
                    specific_result.append(specific_result_1)

                self.logger.info(f"Depression Specific Probs: {dep_specific_probs}")
                self.logger.info(f"Anxiety Specific Probs: {anx_specific_probs}")
            else:
                specific_result = "Normal"

            self.logger.info(f"Specific Result: {specific_result}")

            return specific_result
