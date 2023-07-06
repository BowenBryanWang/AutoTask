import math
import numpy as np
import openai
import pandas as pd
import scipy
from page.init import Screen

from page.init import Screen
from model import Model


class Feedback():
    def __init__(self,model:Model) -> None:
        self.model=model
        pass


