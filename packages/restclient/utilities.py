import json
import functools

import allure
import curlify2


def allure_attach(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        body = kwargs.get("json")

        if body:
            allure.attach(
                json.dumps(body, indent=4),
                name="request_body",
                attachment_type=allure.attachment_type.JSON,
            )

        response = await fn(*args, **kwargs)
        curl = curlify2.Curlify(response.request).to_curl()
        allure.attach(curl, name="curl", attachment_type=allure.attachment_type.TEXT)

        try:
            response_json = response.json()

        except json.decoder.JSONDecodeError:
            response_text = response.text
            status_code = f"status code = {response.status_code}"

            allure.attach(
                response_text if len(response_text) > 0 else status_code,
                name="response_body",
                attachment_type=allure.attachment_type.TEXT,
            )

        else:
            allure.attach(
                json.dumps(response_json, indent=4),
                name="response_body",
                attachment_type=allure.attachment_type.JSON,
            )

        return response

    return wrapper
