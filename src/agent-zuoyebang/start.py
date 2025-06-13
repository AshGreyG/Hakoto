import subprocess
import os
import time
import json
import pytesseract
from dotenv import load_dotenv
from enum import Enum
from openai import OpenAI

import prompt
import gen

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
    def click_position(pos_name : str, description : str) -> None :
        pos = Utils.get_position_env(pos_name)

        subprocess.run([
            "adb", "shell", "input", "tap", 
            str(pos[0]), 
            str(pos[1])
        ])

        print("🔫 Click {} button on position ({}, {}).".format(
            description,
            pos[0],
            pos[1]
        ))

    @staticmethod
    def ocr_result(name : str) -> str :
        
        ocr_text = pytesseract.image_to_string(
            "./tmp/{}".format(name),
            lang = "chi_sim"
        )

        print("🔍 OCR result of {} is \"{}\"".format(name, ocr_text))

        return ocr_text.lower().replace(" ", "")

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
                    global CURRENT_SCREEN
                    CURRENT_SCREEN = t[1]
                    print("🌲 Now we are at {} screen.".format(t[1].name))
                    os.remove("./tmp/" + screenshot)
                    return

        os.remove("./tmp/" + screenshot)


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
        local_path = os.path.join(os.getcwd(), "tmp/", name)
        
        subprocess.run(["adb", "shell", "screencap", "-p", android_path])
        print("📸 Take screenshot at Android devices, name: {}.".format(name))
        subprocess.run(["adb", "pull", android_path, local_path])
        print("♻️ Screenshot {} has been saved to ./tmp directory.".format(name))
        subprocess.run(["adb", "shell", "rm", android_path])
        print("🗑️ Delete screenshot {} on Android devices.".format(name))

        return name

    @staticmethod
    def transfer_answer_picture(name : str) -> None :
        android_path = os.getenv("android_device_screenshot_path")
        local_path = os.path.join(os.getcwd(), "tmp/", name)
        subprocess.run(["adb", "push", local_path, android_path])

class PageActions : ...

class TaskHallInitActions(PageActions) :
    @staticmethod
    def get_question() -> None :
        """
        This function will click the button to get question on the device.
        """

        Utils.click_position("button_get_question", "get question")

class QuestionActions(PageActions) :
    @staticmethod
    def take_user_question() -> str :
        return DeviceActions.take_screenshot("take-question")

    @staticmethod
    def open_user_picture() -> None :
        Utils.click_position("button_user_question_picture", "user question picture")

    @staticmethod
    def close_user_picture() -> None :
        Utils.click_position("button_user_question_picture", "close user question picture")

    @staticmethod
    def take_from_gallery() -> None :
        Utils.click_position("button_take_from_gallery", "take from gallery")

    @staticmethod
    def select_first_picture() -> None :
        Utils.click_position("button_select_first_picture", "select first picture")
    
    @staticmethod
    def confirm_first_picture() -> None :
        Utils.click_position("button_confirm_first_picture", "confirm first picture")

    @staticmethod
    def confirm_upload() -> None :
        Utils.click_position("button_confirm_upload", "confirm upload")
    
    @staticmethod
    def upload_answer() -> None :
        Utils.click_position("button_upload_answer", "upload answer")

    @staticmethod
    def confirm_answer() -> None :
        Utils.click_position("button_confirm_answer", "confirm answer")


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
            print("🐣 AI isn't sure for its rephrased question: {}.\n   Please type y/n to continue.".format(rephrased))
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
    def get_ai_answer(rephrased : str) -> tuple[str, str] :
        answer_certainty_value = os.getenv("answer_certainty")

        messages = [
            { "role": "system", "content": prompt.prompt_answer_question },
            { "role": "user",   "content": rephrased }
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

        answer_analysis_json = json.loads(response_json.choices[0].message.content)
        answer = answer_analysis_json.answer
        analysis = answer_analysis_json.analysis
        certainty = answer_analysis_json.certainty
        
        if certainty < answer_certainty_value :
            print("🐣 AI isn't sure for its answer: {}.\n   Please type y/n to continue. You can open your Firefox to review".format(answer))
            name = gen.generate_html(answer, analysis)
            subprocess.run(["firefox", "./tmp/{}".format(name)])

            result = input()

            while result.lower() != "y" and result.lower() != "n" :
                print("💬 You didn't type y or n. Please try again.")
                result = input()

            if result.lower() == "y" :
                print("🤖 Answer question as {}.".format(rephrased))
                os.remove("./tmp/{}".format(name))
                return (answer, analysis)
            else :
                print("💥 Answer is not correct.")
                exit()

if __name__ == "__main__" :
    load_dotenv()

    _ = lambda : time.sleep(8)

    while True :
        match CURRENT_SCREEN :
            case WhichScreen.TASK_HALL_INIT :
                TaskHallInitActions.get_question()
            case WhichScreen.QUESTION :
                overall = QuestionActions.take_user_question()
                _()
                QuestionActions.open_user_picture()
                _()
                details = QuestionActions.take_user_question()
                _()
                QuestionActions.close_user_picture()
                _()
                rephrased = ModelSolving.get_rephrased_question([overall, details])
                answer, analysis = ModelSolving.get_ai_answer(rephrased)
                html_name = gen.generate_html(answer, analysis)
                picture_name = gen.html_to_picture(html_name)
                _()
                DeviceActions.transfer_answer_picture(picture_name)
                QuestionActions.take_from_gallery()
                _()
                QuestionActions.select_first_picture()
                _()
                QuestionActions.confirm_first_picture()
                _()
                QuestionActions.confirm_upload()
                _()
                QuestionActions.upload_answer()
                _()
                QuestionActions.confirm_answer()

        _()
        Utils.which_screen()
        DeviceActions.wakeup_screen()