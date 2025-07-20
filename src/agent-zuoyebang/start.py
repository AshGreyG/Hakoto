import base64
import subprocess
import os
import time
import json
import pytesseract
from dotenv import load_dotenv
from enum import Enum
from openai import OpenAI
from volcenginesdkarkruntime import Ark

import prompt
import gen

class WhichScreen(Enum) :
    TASK_HALL_INIT = 1
    TASK_HALL_WAITING = 2
    TASK_HALL_ANSWERING = 3
    QUESTION = 4

CURRENT_SCREEN = WhichScreen.QUESTION

REPHRASE_CLIENT = Ark(api_key = "")
ANSWER_CLIENT = OpenAI(api_key = "", base_url = "")

def init_models() -> None :
    global ANSWER_CLIENT
    ANSWER_CLIENT = OpenAI(
        api_key = os.getenv("answer_ai_api_key"),
        base_url = os.getenv("answer_ai_base_url")
    )

    global REPHRASE_CLIENT
    REPHRASE_CLIENT = Ark(api_key = os.getenv("rephrase_ai_api_key"))

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
    def parse_bbox_to_center(bbox : str) -> tuple[float, float] :
        x_scale = float(os.getenv("x_scale"))
        y_scale = float(os.getenv("y_scale"))

        xy : list[float] = list(map(float, bbox.replace("<bbox>", "").replace("</bbox>", "").split(" ")))
        return (
            (xy[0] + xy[2]) * x_scale / 2, 
            (xy[1] + xy[3]) * y_scale / 2
        )

    @staticmethod
    def ocr_result(name : str) -> str :

        ocr_text = pytesseract.image_to_string(
            "./tmp/{}".format(name),
            lang = "chi_sim"
        )

        print("🔍 OCR result of {} is \"{}\"".format(name, ocr_text))

        return ocr_text.lower().replace(" ", "")

    @staticmethod
    def encode_image(name : str) -> str :
        with open("./tmp/{}".format(name), "rb") as img :
            return base64.b64encode(img.read()).decode("utf-8")

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
        local_path = "./tmp/{}".format(name)
        
        subprocess.run(["adb", "shell", "screencap", "-p", android_path])
        print("📸 Take screenshot at Android devices, name: {}.".format(name))
        subprocess.run(["adb", "pull", android_path, local_path])
        print("♻️ Screenshot {} has been saved to ./tmp directory.".format(name))
        subprocess.run(["adb", "shell", "rm", android_path])
        print("🗑️ Delete screenshot {} on Android devices.".format(name))

        return name

    @staticmethod
    def transfer_answer_picture(name : str, mode : str) -> None :
        match mode :
            case "screenshot" :
                android_path = os.getenv("android_device_screenshot_path")
            case "answer" :
                android_path = os.getenv("android_device_wechat_path")
        local_path = "./tmp/{}".format(name)
        subprocess.run(["adb", "push", local_path, android_path])

    @staticmethod
    def get_system_match_problem() -> str :
        subprocess.run(["adb", "shell", "input", "swipe", "500", "1500", "500", "500", "300"])
        name = DeviceActions.take_screenshot("system-match")
        subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1500", "300"])
        return name

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
        Utils.click_position(
            "button_user_question_picture",
            "user question picture"
        )

    @staticmethod
    def close_user_picture() -> None :
        Utils.click_position(
            "button_user_question_picture",
            "close user question picture"
        )

    @staticmethod
    def take_from_gallery() -> None :
        Utils.click_position(
            "button_take_from_gallery",
            "take from gallery"
        )

    @staticmethod
    def upload_picture() -> None :
        Utils.click_position(
            "button_upload_picture",
            "upload picture"
        )

    @staticmethod
    def select_first_picture() -> None :
        Utils.click_position(
            "button_select_first_picture",
            "select first picture"
        )
    
    @staticmethod
    def confirm_first_picture() -> None :
        Utils.click_position(
            "button_confirm_first_picture",
            "confirm first picture"
        )

    @staticmethod
    def confirm_upload() -> None :
        Utils.click_position(
            "button_confirm_upload",
            "confirm upload"
        )
    
    @staticmethod
    def upload_answer() -> None :
        Utils.click_position(
            "button_upload_answer", 
            "upload answer"
        )

    @staticmethod
    def confirm_answer() -> None :
        Utils.click_position(
            "button_confirm_answer", 
            "confirm answer"
        )

class ModelSolving :
    @staticmethod
    def get_bbox_center(image : str) -> tuple[list[tuple[float, float]], tuple[float, float]] :

        image_base64_content = []
        image_base64_content.append({
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,{}".format(Utils.encode_image(image))
            }
        })

        messages = [
            { "role": "system", "content": prompt.prompt_bbox_select },
            { "role": "user", "content": image_base64_content }
        ]

        response_json = REPHRASE_CLIENT.chat.completions.create(
            model = "doubao-1.5-vision-pro-250328",
            messages = messages,
            response_format = {
                "type": "json_object"
            },
            temperature = 0.0,
            stream = False
        )

        bbox_json = json.loads(response_json.choices[0].message.content)

        print("🤖 Get border box of question pictures and submit button: {}".format(bbox_json))

        questioner_str : list[str] = bbox_json["questioner_box"]
        responder_str : str = bbox_json["responder_box"]

        print("🎯 Get str {} {}".format(questioner_str, responder_str))

        questioners = list(map(Utils.parse_bbox_to_center, questioner_str))
        responder = Utils.parse_bbox_to_center(responder_str)

        return (questioners, responder)

    @staticmethod
    def get_rephrased_question(names : list[str]) -> str :
        rephrased_certainty_value = float(os.getenv("rephrased_certainty"))

        images_base64_content = []

        for name in names :
            images_base64_content.append({
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;base64,{}".format(Utils.encode_image(name))
                }
            })

        messages = [
            { "role": "system", "content": prompt.prompt_rephrase_question},
            { "role": "user",   "content": images_base64_content}
        ]

        response_json = REPHRASE_CLIENT.chat.completions.create(
            model = "doubao-1.5-vision-pro-250328",
            messages = messages,
            response_format = {
                "type": "json_object"
            },
            temperature = 0.0,
            stream = False
        )

        print("🐝 Raw response: {}".format(response_json))

        rephrased_json = json.loads(response_json.choices[0].message.content)

        print("🤖 Get rephrased question as {}.".format(rephrased_json))

        rephrased = rephrased_json["rephrased_question"]
        certainty = rephrased_json["certainty"]

        if (certainty <= rephrased_certainty_value) :
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
        answer_certainty_value = float(os.getenv("answer_certainty"))

        messages = [
            { "role": "system", "content": prompt.prompt_answer_question },
            { "role": "user",   "content": rephrased }
        ]

        response_json = ANSWER_CLIENT.chat.completions.create(
            model = "deepseek-reasoner",
            messages = messages,
            response_format = {
                "type": "json_object"
            },
            temperature = 0.0,
            stream = False
        )

        print("🐝 Raw response: {}".format(response_json))

        answer_analysis_json = json.loads(response_json.choices[0].message.content)
        answer : str = answer_analysis_json["answer"]
        analysis : str = answer_analysis_json["analysis"]
        certainty = answer_analysis_json["certainty"]

        print("🤖 Answer to this question is {}".format(analysis))
        
        if certainty <= answer_certainty_value :
            print("🐣 AI isn't sure for its answer: {}.\n   Please type y/n to continue. You can open your Firefox to review".format(analysis))
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
    init_models()

    _ = lambda : time.sleep(8)

    while True :
        match CURRENT_SCREEN :
            case WhichScreen.TASK_HALL_INIT :
                TaskHallInitActions.get_question()
            case WhichScreen.QUESTION :
                overall = QuestionActions.take_user_question()
                _()
                questioners, responder = ModelSolving.get_bbox_center(overall)
                _()

                details : list[str] = []
                for questioner in questioners :
                    os.environ["button_user_question_picture"] = "{},{}".format(
                        questioner[0],
                        questioner[1]
                    )
                    QuestionActions.open_user_picture()
                    _()
                    details.append(QuestionActions.take_user_question())
                    _()
                    QuestionActions.close_user_picture()
                    _()
                system_match = DeviceActions.get_system_match_problem()
                rephrased = ModelSolving.get_rephrased_question([overall, system_match, *details])
                answer, analysis = ModelSolving.get_ai_answer(rephrased)
                html_name = gen.generate_html(answer, analysis)
                picture_name = gen.html_to_picture(html_name)
                _()
                DeviceActions.transfer_answer_picture(picture_name, "answer")

                os.environ["button_take_from_gallery"] = "{},{}".format(
                    responder[0],
                    responder[1]
                )
                QuestionActions.take_from_gallery()
                _()
                QuestionActions.upload_picture()
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