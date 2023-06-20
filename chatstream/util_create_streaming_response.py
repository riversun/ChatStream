import asyncio

from starlette.responses import StreamingResponse

from chatstream.default_finish_token import DEFAULT_FINISH_TOKEN


def create_streaming_response(request,
                              response_text,
                              streaming_finished_callback,
                              headers: dict = None,
                              eos_token=DEFAULT_FINISH_TOKEN,
                              finish_message="success"):
    # session["client_roles"] = role_name  # 開発モードでWebAPIにアクセスすることを許可する
    async def generate():
        ttl = ""
        for val in list(response_text):
            await asyncio.sleep(0.01)
            ttl += val
            print(f"イールド {ttl}")
            yield ttl + eos_token  # TODO 他パートにも EOS_TOKEN 付与する
        await streaming_finished_callback(request, finish_message)

    generator = generate()

    streaming_response = StreamingResponse(generator, media_type="text/plain")

    if headers is not None:
        for key, value in headers.items():
            print(f"key:{key} value:{value}")
            streaming_response.headers[key] = value

    return streaming_response
