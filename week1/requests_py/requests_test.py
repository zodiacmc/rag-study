import requests
from requests import Response
from util.GetProperties import GetProperties

# resp: Response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
# print(resp.status_code)
# print(resp.text)
# print(resp.json())


apikey = GetProperties().get_property("longcat", "apikey")

url = "https://api.longcat.chat/openai/v1/chat/completions"
headers = {
    "Authorization": "Bearer " + apikey,
    "Content-Type": "application/json"
}

data = {
    "model": "LongCat-2.5",
    "messages": [
        {"role": "system", "content": "你是一个医疗助手，不要回答不相干内容"},
        {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 1000,
    "temperature": 0.7
}

response = requests.post(url, headers=headers, json=data)
print(response.status_code)
print(response.content)
print(response.json()["choices"][0]["message"]["content"])


# 向服务器传参数，如 https://xxx.com/search?q=python&page=2
# params = {"q": "python", "page": 2}
# resp = requests.get("https://jsonplaceholder.typicode.com/posts", params=params)
# print(resp.url)             # 看看最终拼出来的URL长啥样
# print(len(resp.json()))     # 返回了多少条