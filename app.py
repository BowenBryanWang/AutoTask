import os

import openai
import re
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        animal = request.form["animal"]
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=generate_prompt(animal),
            temperature=1,
            max_tokens=100,
        )
        print(response)
        result=response.choices[0].text
        #正则匹配result中的每句以.结尾的句子,并只保留该句子当中的单词或者数字或者标点符号，拼接起来以\n分割成一个新的字符串
        result=re.sub(r'[^a-zA-Z0-9,.?! ]', '', result)
        #将每一句话后接上一个换行符
        result=re.sub(r'([.?!])', r'\1\n', result)
        print(result)
        return redirect(url_for("index", result=result))

    result = request.args.get("result")
    return render_template("index.html", result=result)


def generate_prompt(animal):
    return """A user's intention is to "Search for information about Elon Musk on Twitter and to express his opinion about him".
He may do the following sequence:
1, user clicked the "Twitter" icon to enter the Twitter page.
2, user clicked on the search box and type in "Elon Musk".
3, user clicked on the Twitter user "Elon Musk" and enters his personal page.
4, the user liked Elon Musk's second tweet.
5, the user commented "You awful man!" to his third tweet.
A user's intention is "{}".
Let's think step by step, he may do the following sequence:
1,The user enters the app.
2,
""".format(
        animal.capitalize()
    )
