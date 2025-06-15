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
(1) $\\frac{x^2}{8} + \\frac{y^2}{2} = 1$ (2) 不在 (3) 最小值为 $\\frac{25}{144}$，斜率为 $\\pm 1$
""", analysis = """
第一问：由椭圆离心率 $e=\\frac{c}{a}=\\frac{\\sqrt{3}}{2}$ 得 $c=\\frac{\\sqrt{3}}{2}a$，根据椭圆性质 $b^2=a^2-c^2=a^2-\\frac{3}{4}a^2=\\frac{a^2}{4}$。将点 $(2,1)$ 代入椭圆标准方程 $\\frac{x^2}{a^2}+\\frac{y^2}{b^2}=1$ 得 $\\frac{4}{a^2}+\\frac{1}{\\frac{a^2}{4}}=1$，整理得 $\\frac{4}{a^2}+\\frac{4}{a^2}=1$，即 $\\frac{8}{a^2}=1$，解得 $a^2=8$，$b^2=2$，故椭圆方程为 $\\frac{x^2}{8} + \\frac{y^2}{2} = 1$。

第二问：将点 $B(1,0)$ 代入椭圆方程 $\\frac{1}{8} + \\frac{0}{2} = \\frac{1}{8} \\neq 1$，因此点 $B$ 不在椭圆上。

第三问：设直线 $l_1$ 的斜率为 $k$，则方程为 $y=k(x-1)$。与椭圆方程联立得 $\\frac{x^2}{8} + \\frac{k^2(x-1)^2}{2} = 1$，整理为 $(1+4k^2)x^2 -8k^2x + (4k^2-8) = 0$。判别式 $\\Delta = 64k^4 -4(1+4k^2)(4k^2-8) = 112k^2+32$。弦长公式得 $|PQ|=\\sqrt{1+k^2} \\cdot \\frac{\\sqrt{112k^2+32}}{1+4k^2}$。同理可得 $|MN|=\\sqrt{1+\\frac{1}{k^2}} \\cdot \\frac{\\sqrt{112/k^2+32}}{1+4/k^2}$。

令 $t=k^2$，则表达式化简为 $S(t)=\\frac{(1+4t)^2}{16(1+t)(7t+2)}+\\frac{(t+4)^2}{16(1+t)(2t+7)}$。合并后得 $S(t)=\\frac{25t^2+46t+25}{16(1+t)(14t^2+53t+14)}$。

求导过程详细计算：
1. 计算分子导数：$(25t^2+46t+25)'=50t+46$
2. 计算分母导数：$[16(1+t)(14t^2+53t+14)]'=16[(14t^2+53t+14)+(1+t)(28t+53)]$
3. 令 $S'(t)=0$，即 $\\frac{50t+46}{25t^2+46t+25}=\\frac{1}{1+t}+\\frac{28t+53}{14t^2+53t+14}$
4. 通过交叉相乘展开计算，最终解得 $t=1$ 是唯一临界点
5. 验证二阶导数在 $t=1$ 处为正，确认为最小值点
6. 代入 $t=1$ 得最小值为 $\\frac{25+46+25}{16\\times2\\times65}=\\frac{96}{2080}=\\frac{25}{144}$，此时 $k=\\pm 1$。
""")
    html_to_picture(name)