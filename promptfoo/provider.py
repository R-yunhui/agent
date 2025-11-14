# Learn more about building a Python provider: https://promptfoo.dev/docs/providers/python/
import json

import requests
import requests

def call_api(prompt, options, context):
    # The 'options' parameter contains additional configuration for the API call.
    config = options.get('config', None)
    additional_option = config.get('additionalOption', None)

    # The 'context' parameter provides info about which vars were used to create the final prompt.
    user_variable = context['vars'].get('userVariable', None)

    # The prompt is the final prompt string after the variables have been processed.
    # Custom logic to process the prompt goes here.
    # For instance, you might call an external API or run some computations.
    # TODO: Replace with actual LLM API implementation.
    output = call_llm(prompt)

    # The result should be a dictionary with at least an 'output' field.
    result = {
        "output": output['choices'][0]['message']['content'],
    }

    # tokenUsage的使用信息，用于结果统计
    usage = output['usage']
    # If you want to report token usage, you can set the 'tokenUsage' field.
    result['tokenUsage'] = {"total": usage['total_tokens'], "prompt": usage['prompt_tokens'],
                            "completion": usage['completion_tokens']}

    return result


def call_llm(prompt):
    url = "http://192.168.2.59:8000/v1/chat/completions"

    headers = {
        "Authorization": "Bearer 738e8958225caf2514f163e3f91a6381",
        "Content-Type": "application/json"
    }

    # 注意：原curl的data-raw是'{}'，即空JSON对象，这里保持一致
    data = {
        "messages": [
            {
                "content": prompt,
                "role": "user"
            }
        ],
        "model": "qwen3-vl-32b-instruct",
        "max_tokens": 8000,
        "stream": False,
        "temperature": 0.1,
        "top_p": 0.1,
    }
    return requests.post(url, headers=headers, json=data).json()

# if __name__ == '__main__':
#     prompt = "你是谁？"
#     options = {
#         "config": {
#             "additionalOption": "value"
#         }
#     }
#     context = {
#         "vars": {
#             "userVariable": "value"
#         }
#     }
#     result = call_api(prompt, options, context)
#     print(result)

