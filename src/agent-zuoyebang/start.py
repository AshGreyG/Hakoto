import subprocess
import os
import time
import json
import pytesseract
from dotenv import load_dotenv
from enum import Enum
from openai import OpenAI

import prompt

class WhichScreen(Enum) :
    TASK_HALL_INIT = 1
    TASK_HALL_WAITING = 2
    TASK_HALL_ANSWERING = 3
    QUESTION = 4

CURRENT_SCREEN = WhichScreen.TASK_HALL_INIT

CLIENT = OpenAI(
    api_key = os.getenv("ai_api_key"),
    base_url = os.getenv("ai_base_url")
)

class Utils :
    @staticmethod
    def get_position_env(name : str) -> tuple[float, float] :
        """
        This function reads from environment and transform position string
        into tuple of coordinate.

        Args:
            name: The name of environment variable.
        Returns:
            The coordinate syntax of position string, as a tuple.
        """

        pos_str = os.getenv(name)
        return tuple(map(float, pos_str.split(",")))

    @staticmethod
    def ocr_result(name : str) -> str :
        
        ocr_text = pytesseract.image_to_string(
            "./tmp/{}".format(name),
            lang = "chi_sim"
        )

        print("🔍 OCR result of {} is \"{}\"".format(name, ocr_text))

        return ocr_text.lower()

    @staticmethod
    def which_screen() -> None :
        """
        This function takes a screenshot of current screen and use OCR to
        decide which screen.
        """

        screenshot = DeviceActions.take_screenshot("which-screen")

        ocr_text = Utils.ocr_result(screenshot)

        _ = lambda name : os.getenv(name).split(",")

        characteristic : list[tuple[list[str], WhichScreen]] = [
            (_("text_task_hall_init"),      WhichScreen.TASK_HALL_INIT),
            (_("text_task_hall_waiting"),   WhichScreen.TASK_HALL_WAITING),
            (_("text_task_hall_answering"), WhichScreen.TASK_HALL_ANSWERING),
            (_("text_question"),            WhichScreen.QUESTION)
        ]

        for t in characteristic :
            for s in t[0] :
                if s.lower() in ocr_text :
                    CURRENT_SCREEN = t[1]
                    print("🌲 Now we are at {} screen.".format(t[1].name))
                    return

        os.remove(screenshot)

class DeviceActions :
    @staticmethod
    def wakeup_screen() -> None :

        wakeup_pos : tuple[float, float] = (0.0, 0.0)
        match CURRENT_SCREEN :
            case WhichScreen.TASK_HALL_WAITING :
                wakeup_pos = Utils.get_position_env("wakeup_task_hall_init")

        result = subprocess.run([
            "adb", "shell", "input", "tap",
            str(wakeup_pos[0]),
            str(wakeup_pos[1])
        ])

        print("💡 Now on screen {}, click position ({}, {}) to wake up screen.".format(
            CURRENT_SCREEN.name,
            wakeup_pos[0],
            wakeup_pos[1]
        ))

    @staticmethod
    def take_screenshot(prefix : str) -> str :
        """
        This function takes screenshot of Android device and save it to
        PC ./tmp/...
        """

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        name = "{}-{}.png".format(prefix, timestamp)

        android_path = os.getenv("android_device_screenshot_path") + name
        local_path = os.path.join(os.getcwd(), "tmp", name)
        
        subprocess.run(["adb", "shell", "screencap", "-p", android_path])
        print("📸 Take screenshot at Android devices, name: {}.".format(name))
        subprocess.run(["adb", "pull", android_path, local_path])
        print("♻️ Screenshot {} has been saved to ./tmp directory.".format(name))
        subprocess.run(["adb", "shell", "rm", android_path])
        print("🗑️ Delete screenshot {} on Android devices.".format(name))

        return name

class PageActions : ...

class TaskHallInitActions(PageActions) :
    @staticmethod
    def get_question() -> None :
        """
        This function will click the button to get question on the device.
        """

        # Load from environment

        button_pos = Utils.get_position_env("button_get_question")

        subprocess.run([
            "adb", "shell", "input", "tap", 
            str(button_pos[0]), 
            str(button_pos[1])
        ])

        print("🔫 Click get question button on position ({}, {}).".format(
            button_pos[0],
            button_pos[1]
        ))

class QuestionActions(PageActions) :
    @staticmethod
    def take_user_question() -> str :
        return DeviceActions.take_screenshot("take-question")

    @staticmethod
    def open_user_picture() -> None :
        user_picture_pos = Utils.get_position_env("button_user_question_picture")

        subprocess.run([
            "adb", "shell", "input", "tap",
            str(user_picture_pos[0]),
            str(user_picture_pos[1])
        ])

        print("🔫 Click user question picture button on position ({}, {}).".format(
            user_picture_pos[0],
            user_picture_pos[1]
        ))

    @staticmethod
    def close_user_picture() -> None :
        close_pos = Utils.get_position_env("button_user_question_picture")

        # Actually, press anywhere can also cause user picture to close

        subprocess.run([
            "adb", "shell", "input", "tap",
            str(close_pos[0]),
            str(close_pos[1])
        ])

        print("🔫 Click close user question picture button on position ({}, {}).".format(
            close_pos[0],
            close_pos[1]
        ))

class ModelSolving :
    @staticmethod
    def get_rephrased_question(names : list[str]) -> str :
        ocr_texts = [Utils.ocr_result(name) for name in names]
        rephrased_certainty_value = float(os.getenv("rephrased_certainty"))

        messages = [
            { "role": "system", "content": prompt.prompt_rephrase_question},
            { "role": "user",   "content": str(ocr_texts) }
        ]

        response_json = CLIENT.chat.completions.create(
            model = "deepseek-chat",
            messages = messages,
            response_format = {
                "type": "json_object"
            },
            temperature = 0.0,
            stream = False
        )

        rephrased_json = json.loads(response_json.choices[0].message.content)
        rephrased = rephrased_json.rephrased_question
        certainty = rephrased_json.certainty

        if (certainty < rephrased_certainty_value) :
            print("🐣 AI isn't sure for its rephrased question: {}.\n   Please type y/n for continuation.".format(rephrased))
            result = input()

            while result.lower() != "y" and result.lower() != "n" :
                print("💬 You didn't type y or n. Please try again.")
                result = input()
    
            if result.lower() == "y" :
                print("🤖 Rephrase question as {}.".format(rephrased))
                return rephrased
            else :
                print("💥 Rephrased question is not correct.")
                exit()


    @staticmethod
    def get_ai_answer(rephrased : str) -> str :
        ...

if __name__ == "__main__" :
    load_dotenv()

    while True :
        match CURRENT_SCREEN :
            case WhichScreen.TASK_HALL_INIT :
                TaskHallInitActions.get_question()
            case WhichScreen.QUESTION :
                overall = QuestionActions.take_user_question()
                QuestionActions.open_user_picture()
                details = QuestionActions.take_user_question()
                QuestionActions.close_user_picture()
                rephrased = ModelSolving.get_rephrased_question([overall, details])
                answer = ModelSolving.get_ai_answer(rephrased)

        time.sleep(8)
        Utils.which_screen()
        DeviceActions.wakeup_screen()