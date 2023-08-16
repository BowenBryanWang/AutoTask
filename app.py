from aiohttp import ClientSession
import asyncio
import openai

# 设置你的 API 密钥
openai.api_key = "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"  # 填入你的 API 密钥

# 同步调用方式


def sync_chat_completion():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello world"}]
    )
    return response


# 异步调用方式


async def async_chat_completion():

    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello world"}]
    )
    return response

# 同步调用
sync_response = sync_chat_completion()
print("同步调用结果:", sync_response)

# 异步调用


async def main():
    async_response = await async_chat_completion()
    print("异步调用结果:", async_response)

asyncio.run(main())
