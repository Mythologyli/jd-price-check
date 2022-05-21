# jd-price-check

京东商品价格、优惠监控，并使用微信推送

## 配置文件说明

新建 config.json，配置如下：

````json
{
    "items": [
        10045003937676, // 商品 ID
        10046635771777
    ],
    "push": {
        "corpid": "xxxxxx", // 微信企业号 CorpID
        "agentid": 1000002, // 微信企业号应用 AgentID
        "corpsecret": "xxxxxx" // 微信企业号应用 CorpSecret
    }
}
````
