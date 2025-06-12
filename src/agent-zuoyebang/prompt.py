prompt_rephrase_question = """

Please rephrase the user's question in Chinese using the text obtained
from image OCR, which contains both exam questions and text from interface
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

The `rephrased_question` should be Markdown text, please use LaTeX to display 
math formulas. And you don't need to use structured syntax like list or table
to display the rephrased question.

EXAMPLE `rephrased_question` CONTENT

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

prompt_answer_question = """



"""