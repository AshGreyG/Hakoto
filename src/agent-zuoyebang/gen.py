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
                result = content.replace(r"{answer}", html_answer).replace(r"{analysis}", html_analysis)
                name = "no-picture-" +  time.strftime("%Y%m%d-%H%M%S") + ".html"
                with open("./tmp/{}".format(name), "w", encoding = "utf-8") as new_html :
                    new_html.write(result)
                    new_html.close()

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
        page.wait_for_selector("math", state = "attached", timeout = 100000)
        page_height = page.locator("body").bounding_box()["height"]
        page.screenshot(
            path = output_path,
            full_page = True,
            type = "jpeg",
            quality = 85
        )
        print("📦 Answer picture has been saved to {}".format(output_path))
        browser.close()

if __name__ == "__main__" :
    name = generate_html(
        answer = """
(1) $a_n = 2^n$ (2) $T_n = \\frac{2n}{n+1}$
""", 
        analysis = """
(1) 设首项为 $a_1$，公比为 $q$（$a_1>0,q>0$）。由 $3S_2 = a_1 + 2a_3$ 得 $3(a_1 + a_1q) = a_1 + 2a_1q^2$，化简得 $2q^2 - 3q - 2 = 0$。解得 $q=2$（舍负根）。由 $a_4=a_1q^3=16$ 得 $a_1=2$，故通项公式为 <strong style=\"color: red;\">$a_n = 2 \\times 2^{n-1} = 2^n$</strong>。\n\n(2) 由 $\\log_2 a_n = \\log_2(2^n) = n$，得 $\\frac{b_{n+1}}{b_n} = \\frac{n}{n+2}$。累乘得 $b_n = b_1 \\times \\prod_{k=1}^{n-1} \\frac{k}{k+2} = 1 \\times \\frac{1}{3} \\times \\frac{2}{4} \\times \\frac{3}{5} \\times \\cdots \\times \\frac{n-1}{n+1}$。分子分母约简后得 $b_n = \\frac{2}{n(n+1)} = 2\\left(\\frac{1}{n} - \\frac{1}{n+1}\\right)$。<strong style=\"color: red;\">且当 $n=1$ 时 $b_1=1$ 符合上式 </strong>，故 $T_n = \\sum_{k=1}^n b_k = 2\\sum_{k=1}^n \\left(\\frac{1}{k} - \\frac{1}{k+1}\\right) = 2\\left(1 - \\frac{1}{n+1}\\right) = \\frac{2n}{n+1}$。\n\n分类讨论原因：在数列问题中，<strong style=\"color: red;\">递推关系 $a_n = S_n - S_{n-1}$ 仅对 $n \\geq 2$ 成立</strong>，而 $n=1$ 时 $a_1 = S_1$ 需单独处理。例如求 $a_n$ 通项时，若用 $S_n$ 表达式求 $a_n$，必须分 $n=1$ 和 $n \\geq 2$ 讨论。在递推数列如 $\\{b_n\\}$ 中，若递推式定义域从 $n \\geq 2$ 开始（如 $b_n = f(b_{n-1})$），则 $b_1$ 需单独处理以保证完备性。
""")
    html_to_picture(name)