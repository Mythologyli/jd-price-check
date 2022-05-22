import datetime
import json
import os

from loguru import logger
import requests
from typing import List

from bs4 import BeautifulSoup

from wechatpusher import WeChatPusher


class PriceChecker:
    def __init__(self, sku_ids: List[int], proxy: str, wechat_pusher: WeChatPusher):
        self.sku_ids = sku_ids
        self.wechat_pusher = wechat_pusher

        self.item_names = []

        self.old_item_infos = []
        os.makedirs('data', exist_ok=True)
        if os.path.exists('data/old_item_infos.json'):
            with open('data/old_item_infos.json', 'r') as f:
                self.old_item_infos = json.load(f)

        self.new_item_infos = []

        self.session = requests.Session()

        if proxy != '':
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }

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
        return res.json()

    def _save_old_item_infos(self) -> None:
        with open('data/old_item_infos.json', 'w') as f:
            json.dump(self.old_item_infos, f)

    def check_infos_update(self) -> None:
        for i in range(len(self.sku_ids)):
            self.item_names.append(self._get_item_name(self.sku_ids[i]))
            self.new_item_infos.append(self._get_item_info(self.sku_ids[i]))

        if not self.old_item_infos:
            self.old_item_infos = self.new_item_infos
            self._save_old_item_infos()
            return

        for sku_id, item_name, old_item_info, new_item_info in zip(self.sku_ids,
                                                                   self.item_names,
                                                                   self.old_item_infos,
                                                                   self.new_item_infos):
            if old_item_info['price']['p'] != new_item_info['price']['p']:
                logger.info(
                    '{} 价格变动，原价：{}，现价：{}'.format(item_name,
                                                 old_item_info['price']['p'],
                                                 new_item_info['price']['p']))
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
                    logger.info('{} 促销信息变动，原促销信息：{}，现促销信息：{}'.format(item_name,
                                                                     old_activity['value'],
                                                                     new_activity['value']))
                    self.wechat_pusher.send(
                        title='京东促销信息变动',
                        description='{} 促销信息变动，原促销信息：{}，现促销信息：{}'.format(
                            item_name,
                            old_activity['value'],
                            new_activity['value']),
                        url='https://item.jd.com/{}.html'.format(sku_id))

        self._save_old_item_infos()


def main():
    os.makedirs('logs', exist_ok=True)
    logger.add('logs/{time:YYYY-MM-DD}.log',
               rotation='0:00',
               retention='30 days',
               level='DEBUG')

    with open('config.json', 'r') as f:
        config = json.load(f)

    price_checker = PriceChecker(config['items'],
                                 config['proxy'],
                                 WeChatPusher(config['push']['corpid'],
                                              config['push']['agentid'],
                                              config['push']['corpsecret']))

    price_checker.check_infos_update()
    logger.info('{} 时完成检查'.format(datetime.datetime.now()))


if __name__ == '__main__':
    main()
