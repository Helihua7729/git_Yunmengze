import logging
import http.client as http_client
from volcenginesdkarkruntime import Ark

# 启用详细的HTTP请求日志
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

client = Ark(api_key="51e09aa5-d2dd-41ab-bf91-51ef798844e7")
try:
    response = client.chat.completions.create(
        model="doubao-seed-1-6-lite-251015",
        messages=[{"role": "user", "content": "你是谁"}],
        timeout=30
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"连接测试失败: {e}")