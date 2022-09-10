import os
import sys

# include app package for package&module search
APP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app"
)
sys.path.append(APP_PATH)
