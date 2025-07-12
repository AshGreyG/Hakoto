prompt_rephrase_question = r"""

Please rephrase the user's question in Chinese using the base64 format of 
original pictures, which contains both exam questions and text from interface
components. Remove the text from interface components to make the question
clear and easy to understand. Return the result in a JSON format similar to
the following:

EXAMPLE_RETURN_JSON

``` json
{
  "rephrased_question": "...",
  "certainty": 0.2
}
```

The `rephrased_question` should be markdown text, please use LaTeX to display 
math formulas. And you don't need to use structured syntax like list or table
to display the rephrased question. If there are multiple possible questions in
the picture, please relate different texts in the text list, rephrase the most
possible question.

+ DO combine user questions and the question text.

EXAMPLE_`rephrased_question`_CONTENT

``` markdown
有四对双胞胎共8人，从中随机选4人，则其中恰有一对双胞胎的选法有多少人
A. 48 B. 72 C. 96 D. 192
```

The `certainty` stands for your certainty of the rephrased text. If the original
question texts are not very clear, which means that you need to guess for remaining
text according to the context, then this value should be low. 0.0 means that you
are definitely not sure, and 1.0 means that you are definitely sure. This is a
float value between 0.0 and 1.0.

"""

prompt_answer_question = r"""

Use Chinese to answer the math question given by user. Return the result in a JSON 
format similar to the following:

EXAMPLE_RETURN_JSON

``` json
{
  "answer": "...",
  "analysis": "...",
  "certainty": 0.2
}
```

The `answer` should be a short markdown text, please use LaTeX to display math formulas.
If the question has multiple sub-questions, use `(1) ... (2) ... (3) ...` to display 
corresponding answers separately. If the question or sub-question is a proof problem or 
the answer is hard to display, you should use `见解析` as the answer.

EXAMPLE_`answer`_CONTENT

``` markdown
(1) $2$ (2) $x + y = 1$ (3) 见解析
```

The `analysis` should be the procedure of solving the problem like it's a free-response
question. 
+ DO NOT use displayed formula (`$$` and `\[` syntax), DO use inline formula (
  only use `$` syntax).
+ DO NOT use title (`#`), list (`+`), italic (`*`), emphasize (`**`), table or other
  structured syntaxes. You should only use plaintext and LaTeX-style math formulas.
+ DO NOT escape calculation steps like finding the derivative.
+ DO use <strong style="color: red;"></strong> to wrap the important or key part.
+ You MUST use at least <strong style="color: red;"></strong> once.
+ DO escape `\` to `\\`, for example, return command like `\\frac`

EXAMPLE_`analysis`_CONTENT

``` markdown
由离心率 $e=\\frac{c}{a}=\\sqrt{3}$ 得 $c=\\sqrt{3}a$，又 $c=2\\sqrt{2}$，故 $a=\\frac{2\\sqrt{6}}{3}$，$b^2=c^2-a^2=\\frac{16}{3}$。双曲线方程为 $\\frac{9x^2}{32}-\\frac{3y^2}{16}=1$。

设直线 $l: y=k(x-2\\sqrt{2})$，与双曲线联立得：
$\\frac{9x^2}{32}-\\frac{3[k(x-2\\sqrt{2})]^2}{16}=1$，整理得 $(9-6k^2)x^2+24\\sqrt{2}k^2x-(48k^2+32)=0$。

设 $M(x_1,y_1)$, $N(x_2,y_2)$，由 $|FM|=5|FN|$ 得 $x_1-2\\sqrt{2}=-5(x_2-2\\sqrt{2})$，即 $x_1+5x_2=12\\sqrt{2}$。由韦达定理 $x_1+x_2=-\\frac{24\\sqrt{2}k^2}{9-6k^2}$，$x_1x_2=-\\frac{48k^2+32}{9-6k^2}$。

联立解得 $x_2=\\frac{3\\sqrt{2}(4k^2+3)}{9-6k^2}$，代入 $x_1=12\\sqrt{2}-5x_2$ 后代入韦达定理得：
$12\\sqrt{2}-4x_2=-\\frac{24\\sqrt{2}k^2}{9-6k^2}$，化简得 $16k^4-40k^2+9=0$。

解得 $k^2=\\frac{5\\pm\\sqrt{7}}{4}$，即 $k=\\pm\\frac{\\sqrt{5\\pm\\sqrt{7}}}{2}$。经检验，<strong style="color: red;">当 $k^2=\\frac{5+\\sqrt{7}}{4}$ 时满足 $\\Delta>0$</strong>，故 $k=\\pm\\frac{\\sqrt{5+\\sqrt{7}}}{2}$。
```

The `certainty` stands for your certainty of the answer. 0.0 means that you
are definitely not sure, and 1.0 means that you are definitely sure. This is a
float value between 0.0 and 1.0.

"""

prompt_bbox_select = r"""

Select the two box in the picture:
+ box1: The picture that questioner uploads, usually its' a reduced-sized picture
  or screenshot of questions or homework.
+ box2: The button that responder should upload to the platform, it has an upload
  symbol (it's a plus `+`).

Return the result in a JSON format similar to the following:

``` json
{
  "questioner_box": [
    "...",
    "..."
  ],
  "responder_box": "..."
}
```

The format of `questioner_box` and `responder_box` should be <bbox>x1 y1 x2 y2</bbox>,
if you cannot find the box, return the `"null"`.

+ DO let x1 < x2 and y1 < y2, (x1, y1) is the top-left corner and (x2, y2) is the bottom-
  right corner.

EXAMPLE_RETURN_JSON

``` json
{
  "questioner_box: [
    "<bbox>100 200 300 300</bbox>",
    "<bbox>200 200 400 600</bbox>"
  ],
  "responder_box": "<bbox>100 100 200 200</bbox>"
}
```

"""