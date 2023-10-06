import openai
import chainlit as cl
from chainlit import user_session

model_name = "gpt-3.5-turbo"
settings = {
    "temperature": 0.7,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


def get_dalle_image(prompt):
    response = openai.Image.create(
        prompt=f"Dubai in the future and {prompt}", n=1, size="256x256"
    )
    image_url = response["data"][0]["url"]
    return image_url


@cl.on_chat_start
async def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "assistant", "content": "What is your name?"}],
    )

    message_history = cl.user_session.get("message_history")
    msg = cl.Message(content="What is your name?")

    message_history.append({"role": "assistant", "content": msg.content})
    user_session.set("NAME", "")
    user_session.set("PICTURE", "")

    await msg.send()


@cl.on_message
async def main(message: str):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message})

    msg = cl.Message(content="")

    if user_session.get("NAME") == "":
        user_session.set("NAME", message)
        msg = cl.Message(
            content=f'Hello {user_session.get("NAME")}, I want to create an image of the UAE in the future, in three words can you describe your idea? [eg. "Futuristic, Snowy and vibrant"]'
        )
        message_history.append({"role": "assistant", "content": msg.content})
    elif user_session.get("PICTURE") == "":
        user_session.set("PICTURE", message)

        image_url = await cl.make_async(get_dalle_image)(message)
        elements = [cl.Image(name="UAE in the future", display="inline", url=image_url)]

        await cl.Message(
            content="Do you think it would look like this?", elements=elements
        ).send()
        msg = cl.Message(
            content=f"Congratulations {user_session.get('NAME')}, you just generated an image using AI! The text that you sent was used as a prompt to control the output of the image. Have a look at our [Generative AI Guide](https://ai.gov.ae) to learn more. Feel free to talk to me if you want to learn more about AI/ generative AI or anything else."
        )
        message_history.append({"role": "assistant", "content": msg.content})
    else:
        async for stream_resp in await openai.ChatCompletion.acreate(
            model=model_name, messages=message_history, stream=True, **settings
        ):
            token = stream_resp.choices[0]["delta"].get("content", "")
            await msg.stream_token(token)
        message_history.append({"role": "assistant", "content": msg.content})

    await msg.send()
