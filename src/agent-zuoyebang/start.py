import subprocess
import os
from dotenv import load_dotenv

def get_question() -> None :
    """
    This function will click the button to get question on the device.
    """

    # Load from environment

    button_pos_str = os.getenv("get_question_button")
    button_pos = tuple(map(float, button_pos_str.split(",")))

    result = subprocess.run([
        "adb", "shell", "input", "tap", 
        str(button_pos[0]), 
        str(button_pos[1])
    ])

    print(f"🔫 Click get question button on position ({button_pos[0]}, {button_pos[1]})")

if __name__ == "__main__" :
    load_dotenv()
    get_question()