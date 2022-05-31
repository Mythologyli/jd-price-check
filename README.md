# jd-price-check

京东商品价格、优惠监控，并使用微信推送

## 使用说明

请使用 cron 定时执行脚本

## 配置文件说明

新建 config.json，配置如下：（使用时请删除 // 及后面的文字）

````
{
    "items": [
        10045003937676, // 商品 ID
        10046635771777
    ],
    "proxy": "http://127.0.0.1:9999", // 代理地址，为空则不使用代理
    "push": {
        "corpid": "xxxxxx", // 微信企业号 CorpID
        "agentid": 1000002, // 微信企业号应用 AgentID
        "corpsecret": "xxxxxx" // 微信企业号应用 CorpSecret
    }
}
````
