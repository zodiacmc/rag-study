import json

import requests

from util.GetProperties import GetProperties

API_URL = "https://api.longcat.chat/openai/v1/chat/completions"
API_KEY = GetProperties().get_property("longcat", "apikey")

API_URL_GET_MODELS = "https://api.longcat.chat/openai/v1/models"
API_URL_GET_MODELS_INFO = "https://api.longcat.chat/openai/v1/models/"


def chat(messages, model="LongCat-2.5", temperature=0.3, stream=False):
    """
    通用对话助手
    :param messages: 请求大模型messages信息，单独传入字符串或者列表信息
    :param model: 模型
    :param temperature: 温度参数
    :param stream: 是否流式返回
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,  # 问答场景调低
        "thinking": {
            "type": "disabled"  # 先关闭思考过程
        },
        "stream": stream
    }
    try:
        resp = requests.post(API_URL, json=payload,
                             headers={"Authorization": f"Bearer {API_KEY}"},
                             timeout=60, stream=stream)
        if resp is None:
            return "请求异常: 空响应"
        rtn_status = resp.status_code
        if rtn_status != 200:
            return f"请求异常: {rtn_status} {resp.text}"
        if stream is False:  # 非流式返回
            dataJson = resp.json()
            if dataJson is None or dataJson == "":
                return "请求异常: 空响应"
            # 获取具体的内容信息
            # data["choices"][0]["message"]["content"]
            if dataJson["choices"] is not None \
                    and len(dataJson["choices"]) > 0 \
                    and dataJson["choices"][0]["message"] is not None \
                    and dataJson["choices"][0]["message"]["content"] is not None:
                return dataJson["choices"][0]["message"]["content"]
            else:
                return f"请求异常，获取内容失败,{json.dumps(dataJson)}"

        full = ""
        # 流式返回
        for line in resp.iter_lines():
            if line is None:
                continue
            text = line.decode("utf-8")
            if not text.startswith("data:"):
                continue
            chunk = text[len("data:"):].strip()
            if chunk == "[DONE]":
                break
            json_data = json.loads(chunk)
            if json_data is not None \
                    and json_data["choices"] is not None \
                    and len(json_data["choices"]) > 0 \
                    and json_data["choices"][0]["delta"] is not None:
                delta = json_data["choices"][0]["delta"].get("content", "")
                if delta == "" or delta is None:
                    continue
                print(delta, end="", flush=True)  # 不换行、立即打印 → 打字机效果
                full += delta

        return full

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except Exception as e:
        return f"请求异常: {e}"


def chat_once(question):
    """发一次请求，返回完整回答"""
    payload = {
        "model": "LongCat-2.5",
        "messages": [
            {"role": "system", "content": "你是一个知识库助手，回答简洁准确"},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,  # 问答场景调低
        "thinking": {
            "type": "disabled"
        }
    }
    resp = requests.post(API_URL, json=payload,
                         headers={"Authorization": f"Bearer {API_KEY}"},
                         timeout=30)
    resp.raise_for_status()  # 4xx/5xx 直接抛错
    data = resp.json()

    print("===================")
    print(data)
    print("===================")

    use_token = data["usage"]["prompt_tokens"]  # 花了多少 token（可用来记账）
    print(f"Use {use_token} tokens")

    return data["choices"][0]["message"]["content"]


def get_chat_models():
    """
    获取模型列表
    :return: 模型泪飙json
    """
    resp = requests.get(API_URL_GET_MODELS, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()


def get_models_info():
    """
    获取模型信息
    :return: 模型信息json
    """
    model_name_list = []
    model_json = get_chat_models()  # 获取模型列表
    if model_json is not None and model_json["data"] is not None:
        for model in model_json["data"]:
            model_name_list.append(model["id"])
    else:
        print("Failed to get models info", model_json)

    model_json_info = {}
    if len(model_name_list) > 0:
        for model_name in model_name_list:
            resp = requests.get(API_URL_GET_MODELS_INFO + model_name, headers={"Authorization": f"Bearer {API_KEY}"})
            model_json_info[model_name] = resp.json()

    return model_json_info


def chat_stream(messages: json):
    """
    流式请求
    :param messages: json 格式的 messages 问题
     [
        {"role": "system", "content": "xxxx"},
        {"role": "user", "content": "xxxxxx"},
    ]
    """
    payload = {
        "model": "LongCat-2.5",
        "messages": messages,
        "temperature": 0.3,  # 问答场景调低
        "stream": True,
    }
    resp = requests.post(API_URL, json=payload,
                         headers={"Authorization": f"Bearer {API_KEY}"},
                         timeout=30, stream=True)

    resp.raise_for_status()  # 4xx/5xx 直接抛错

    for line in resp.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if not text.startswith("data:"):
            continue
        # 去掉 "data: " 前缀，以及空格
        chunk = text[len("data:"):].strip()
        if chunk == "[DONE]":
            break
        json_data = json.loads(chunk)
        delta = ""
        if json_data is not None \
                and json_data["choices"] is not None \
                and len(json_data["choices"]) > 0 \
                and json_data["choices"][0]["delta"] is not None:
            delta = json_data["choices"][0]["delta"].get("content", "")
        if delta == "" or delta is None:
            continue
        print(delta, end="", flush=True)  # 不换行、立即打印 → 打字机效果


def chat_stream2(messages):
    """
    流式请求（生成器版本），逐段 yield delta 文本，供 FastAPI StreamingResponse 使用。
    :param messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    :yield: 每段增量文本字符串
    """
    payload = {
        "model": "LongCat-2.5",
        "messages": messages,
        "temperature": 0.3,
        "stream": True,
    }
    resp = requests.post(API_URL, json=payload,
                         headers={"Authorization": f"Bearer {API_KEY}"},
                         timeout=60, stream=True)
    resp.raise_for_status()

    for line in resp.iter_lines():
        if not line:
            continue
        text = line.decode("utf-8")
        if not text.startswith("data:"):
            continue
        chunk = text[len("data:"):].strip()
        if chunk == "[DONE]":
            break
        try:
            json_data = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if (json_data and json_data.get("choices")
                and len(json_data["choices"]) > 0
                and json_data["choices"][0].get("delta")):
            delta = json_data["choices"][0]["delta"].get("content", "")
            if delta:
                yield delta


# messages = [{"role": "user", "content": "你在干什么？？？"}]
# print(chat(messages))
# print(chat(messages, stream=True))

if __name__ == "__main__":
    # 多轮对话：只有直接运行 python llm_client.py 时才执行，被 import 时不跑
    history = [{"role": "system", "content": "你是知识库助手，请基于知识库进行回答"}]

    while True:
        user_input = input("你问：")
        if user_input in ("exit", "退出"):
            break
        history.append({"role": "user", "content": user_input})
        answer = chat(history, stream=True)
        history.append({"role": "assistant", "content": answer})
        print("AI：", answer)

