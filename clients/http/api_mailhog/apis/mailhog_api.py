import allure

from packages.restclient.client import RestClient


class MailhogApi(RestClient):
    @allure.step("Send GET request to /api/v2/messages (Mailhog API)")
    async def get_api_v2_messages(self, limit=50):
        """
        Get users emails

        Args:
            limit

        Returns:
            _type_: Response
        """

        params = {
            'limit': limit,
        }

        response = await self.get(
            path="/api/v2/messages",
            params=params
        )

        return response