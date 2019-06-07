import requests


class Session(requests.Session):
    def __init__(self, api_key, baseurl):
        super().__init__()
        self.url_prefix = baseurl.rstrip("/")
        self.headers = {"Authorization": "Bearer %s" % api_key}

    def request(self, method, url, **kwargs):
        return super().request(method, self.url_prefix + url, **kwargs)
