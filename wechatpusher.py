import requests
import json


class WeChatPusher:
    """企业微信推送"""

    def __init__(self, corpid, agentid, corpsecret):
        # 企业ID
        self.corpid = corpid

        # 企业应用ID
        self.agentid = agentid

        # 应用的凭证密钥
        self.corpsecret = corpsecret

        # access_token
        self.access_token = ''

        # access_token 获取调用接口
        self.token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?'

        # 应用消息发送接口
        self.send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token='

        # 请求 session
        self.sess = requests.Session()

    def _get_token(self):
        """获取 access_token"""

        res = json.loads(
            self.sess.get(self.token_url + 'corpid=' + self.corpid + '&corpsecret=' + self.corpsecret).text)

        if res['errcode'] != 0:
            return res['errcode']

        self.access_token = res['access_token']

        return 0

    def send(self, title, description='', url='', btntxt='', user='@all'):
        """应用消息发送"""

        if description == '':
            description = title

        if url == '':
            url = 'https://github.com/Mythologyli/WeChatPusher'

        if self.access_token == '':
            res_get = self._get_token()  # 更新 access_token
            if res_get != 0:
                return res_get

        data = {
            'touser': user,
            'toparty': '@all',
            'totag': '@all',
            'msgtype': 'textcard',
            'agentid': self.agentid,
            'textcard': {
                'title': title,
                'description': description,
                'url': url,
                'btntxt': btntxt
            },
            'safe': 0,
            'enable_id_trans': 0,
            'enable_duplicate_check': 0,
            'duplicate_check_interval': 1800
        }

        res = json.loads(self.sess.post(url=(self.send_url + self.access_token), data=json.dumps(data)).text)

        if res['errcode'] != 0:  # 可能由 access_token 过期造成
            res_get = self._get_token()  # 更新 access_token
            if res_get != 0:
                return res_get

            res = json.loads(self.sess.post(url=(self.send_url + self.access_token), data=json.dumps(data)).text)

            return res['errcode']
        else:
            return 0
