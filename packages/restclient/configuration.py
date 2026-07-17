from collections.abc import Mapping


class Configuration:
    def __init__(
        self,
        host: str,
        headers: Mapping[str, str] | None = None,
        disable_log: bool = True,
        verify: bool = True,
    ) -> None:
        self.host = host
        self.headers = headers
        self.disable_log = disable_log
        self.verify = verify
