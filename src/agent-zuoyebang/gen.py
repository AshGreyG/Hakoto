import pypandoc
import time
import os
from playwright.sync_api import sync_playwright

def generate_html(answer : str, analysis : str, mode : str = "no-picture") -> str :
    unescaped_answer = rf"{answer}"
    unescaped_analysis = rf"{analysis}"

    html_answer = pypandoc.convert_text(
        unescaped_answer,
        to = "html",
        format = "markdown",
        extra_args = ["--mathjax"]
    )

    html_analysis = pypandoc.convert_text(
        unescaped_analysis,
        to = "html",
        format = "markdown",
        extra_args = ["--mathjax"]
    )

    match mode :
        case "no-picture" :
            with open("./templates/no-picture.template.html", "r", encoding = "utf-8") as f :
                content = f.read()
                result = content.replace(r"{{answer}}", html_answer).replace(r"{{analysis}}", html_analysis)
                name = "no-picture-" +  time.strftime("%Y%m%d-%H%M%S") + ".html"
                new_html = open("./tmp/{}".format(name))
                new_html.write(result)

                print("✈️ Write answer and analysis to file ./tmp/{}".format(name))

                return name

def html_to_picture(name : str) -> str :
    abs_html_path = os.path.join(os.getcwd(), "tmp", name)
    output_path = os.path.join(
        os.getcwd(),
        "tmp/"
        "screenshot-playwright-" + time.strftime("%Y%m%d-%H%M%S") + ".jpg"
    )
    
    with sync_playwright() as p :
        browser = p.chromium.launch(
            headless = True,
            args = ["--disable-gpu", "--no-sandbox"]
        )
        page = browser.new_page()
        page.goto("file:///{}".format(abs_html_path))
        page.wait_for_selector("math", state = "attached", timeout = 10000)
        page_height = page.locator("body").bounding_box()["height"]
        page.screenshot(
            path = output_path,
            full_page = True,
            type = "jpeg",
            quality = 85
        )
        browser.close()