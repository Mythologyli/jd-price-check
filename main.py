import datetime
import json
from time import sleep

import requests
from typing import List

from bs4 import BeautifulSoup

from wechatpusher import WeChatPusher


class PriceChecker:
    def __init__(self, sku_ids: List[int], wechat_pusher: WeChatPusher):
        self.sku_ids = sku_ids
        self.wechat_pusher = wechat_pusher

        self.item_names = []

        self.old_item_infos = []
        self.new_item_infos = []

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47 '
        })

    def _get_item_name(self, sku_id: int) -> str:
        res = self.session.get('https://item.jd.com/{}.html'.format(sku_id))
        soup = BeautifulSoup(res.text, 'html.parser')

        item_name = soup.find('div', class_='sku-name').text.strip()

        return item_name

    def _get_item_info(self, sku_id: int) -> dict:
        res = self.session.get('https://item-soa.jd.com/getWareBusiness?skuId={}'.format(sku_id))
        item_info = json.loads(res.text)

        return item_info

    def check_infos_update(self) -> None:
        if not self.old_item_infos:
            for sku_id in self.sku_ids:
                self.item_names.append(self._get_item_name(sku_id))
                self.new_item_infos.append(self._get_item_info(sku_id))

            self.old_item_infos = self.new_item_infos

            return

        for i in range(len(self.sku_ids)):
            self.new_item_infos[i] = self._get_item_info(self.sku_ids[i])

        for sku_id, item_name, old_item_info, new_item_info in zip(self.sku_ids,
                                                                   self.item_names,
                                                                   self.old_item_infos,
                                                                   self.new_item_infos):
            if old_item_info['price']['p'] != new_item_info['price']['p']:
                print('{} 价格变动，原价：{}，现价：{}'.format(item_name, old_item_info['price']['p'], new_item_info['price']['p']))
                self.wechat_pusher.send(
                    title='京东价格变动',
                    description='{} 价格变动，原价：{}，现价：{}'.format(
                        item_name,
                        old_item_info['price']['p'],
                        new_item_info['price']['p']),
                    url='https://item.jd.com/{}.html'.format(sku_id))

            for old_activity, new_activity in zip(old_item_info['promotion']['activity'],
                                                  new_item_info['promotion']['activity']):
                if old_activity['value'] != new_activity['value']:
                    print('{} 促销信息变动，原促销信息：{}，现促销信息：{}'.format(item_name, old_activity['value'], new_activity['value']))
                    self.wechat_pusher.send(
                        title='京东促销信息变动',
                        description='{} 促销信息变动，原促销信息：{}，现促销信息：{}'.format(
                            item_name,
                            old_activity['value'],
                            new_activity['value']),
                        url='https://item.jd.com/{}.html'.format(sku_id))

        self.old_item_infos = self.new_item_infos


def main():
    with open('config.json', 'r') as f:
        config = json.load(f)

    price_checker = PriceChecker(config['items'],
                                 WeChatPusher(config['push']['corpid'],
                                              config['push']['agentid'],
                                              config['push']['corpsecret']))

    price_checker.check_infos_update()
    while True:
        price_checker.check_infos_update()
        print('{} 时完成检查'.format(datetime.datetime.now()))
        sleep(60)


if __name__ == '__main__':
    main()
