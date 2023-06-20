import asyncio

from starlette.responses import StreamingResponse

from chatstream.default_finish_token import DEFAULT_FINISH_TOKEN


def create_streaming_response(request,
                              response_text,
                              streaming_finished_callback,
                              headers: dict = None,
                              eos_token=DEFAULT_FINISH_TOKEN,
                              finish_message="success"):
    """
    ストリーミングレスポンスを生成する
    :param request:
    :param response_text:
    :param streaming_finished_callback:
    :param headers:
    :param eos_token:
    :param finish_message:
    :return:
    """

    async def generate():
        merged_response_text = ""

        for partial_char in list(response_text):
            await asyncio.sleep(0.01)
            merged_response_text += partial_char

            yield merged_response_text + eos_token
        await streaming_finished_callback(request, finish_message)

    generator = generate()

    streaming_response = StreamingResponse(generator, media_type="text/plain")

    if headers is not None:
        # - レスポンスヘッダーとなるヘッダー定義dict がセットされていたとき
        for key, value in headers.items():
            streaming_response.headers[key] = value

    return streaming_response
