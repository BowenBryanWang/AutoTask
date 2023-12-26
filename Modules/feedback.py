from Modules.utility import GPT
import json
import openai
import os

openai.api_key = os.getenv('OPENAI_API_KEY')


class Feedback:
    """
    Class for providing feedback based on the logs of a primitive LLM model.

    Attributes:
        model (AutoTaskModel): The model instance associated with this feedback.
    """

    def __init__(self, model) -> None:
        """
        Initialize the Feedback object with a model.

        Args:
            model (AutoTaskModel): The model instance to provide feedback for.
        """
        self.model = model

    def feedback(self, reason):
        """
        Generate feedback based on the reason and model's logs.

        Args:
            reason (str): The reason for the feedback.

        Returns:
            tuple: Confirmation of feedback processing.
        """
        log_file_path = f"logs/log{self.model.index+1}.json"
        # Reading log file
        with open(log_file_path, "r", encoding="utf-8") as f:
            self.info: dict = json.loads(f.read())
        # Building prompt for feedback
        self.prompt = [
            {
                "role": "system",
                "content": (
                    "You are an expert in UI automation and robust error handling. Your task is to critique an "
                    "operation sequence produced by a [primitive LLM], following a user task but inaccurately. "
                    "Analyze the logs from each module of the current step of the [primitive LLM], locate errors "
                    "in the final element chosen to operate on, and output the punishment coefficient."
                )
            },
            {"role": "user", "content": f"Wrong reason: {reason}"},
            {"role": "user",
                "content": f"User intent: {self.info['@User_intent']}"},
            {"role": "user",
                "content": f"Page components: {self.info['@Page_components']}"},
            {"role": "user",
                "content": f"Previous Steps: {self.info['@History_operation']}"},
            {"role": "user",
                "content": f"Action on this step: {self.info['@Current_Action']}"},
            {"role": "user",
                "content": f"Latest Page: {self.info.get('@Successive_Page', 'No changes in the latest page!')}"},
            {"role": "user", "content": f"Modules: {self.info['@Module'][1]}"}
        ]
        # Getting feedback from GPT
        response = GPT(self.prompt, tag=f"feedback{self.model.index}")
        punishment_score = response.get("punishment")
        # Updating model with the feedback
        self.model.evaluate_module.update_weights(punishment_score)
        return "yes", "yes"
