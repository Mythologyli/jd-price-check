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

        os.makedirs('data', exist_ok=True)

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

    @staticmethod
    def _get_old_item_info(sku_id: int) -> dict:
        with open('data/{}.json'.format(sku_id), 'r') as f:
            old_item_info = json.load(f)

        return old_item_info

    @staticmethod
    def _save_old_item_info(sku_id: int, item_info: dict) -> None:
        with open('data/{}.json'.format(sku_id), 'w') as f:
            json.dump(item_info, f)

    def check_infos_update(self) -> None:
        for sku_id in self.sku_ids:
            if not os.path.exists('data/{}.json'.format(sku_id)):
                item_info = self._get_item_info(sku_id)
                self._save_old_item_info(sku_id, item_info)

            old_item_info = self._get_old_item_info(sku_id)
            new_item_info = self._get_item_info(sku_id)
            item_name = self._get_item_name(sku_id)

            if old_item_info['price']['p'] != new_item_info['price']['p']:
                logger.info(
                    '{} ????????????????????????{}????????????{}'.format(item_name,
                                                 old_item_info['price']['p'],
                                                 new_item_info['price']['p']))
                self.wechat_pusher.send(
                    title='??????????????????',
                    description='{} ????????????????????????{}????????????{}'.format(
                        item_name,
                        old_item_info['price']['p'],
                        new_item_info['price']['p']),
                    url='https://item.jd.com/{}.html'.format(sku_id))

            for old_activity, new_activity in zip(old_item_info['promotion']['activity'],
                                                  new_item_info['promotion']['activity']):
                if old_activity['value'] != new_activity['value']:
                    logger.info('{} ???????????????????????????????????????{}?????????????????????{}'.format(item_name,
                                                                     old_activity['value'],
                                                                     new_activity['value']))
                    self.wechat_pusher.send(
                        title='????????????????????????',
                        description='{} ???????????????????????????????????????{}?????????????????????{}'.format(
                            item_name,
                            old_activity['value'],
                            new_activity['value']),
                        url='https://item.jd.com/{}.html'.format(sku_id))

            self._save_old_item_info(sku_id, new_item_info)


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
    logger.info('{} ???????????????'.format(datetime.datetime.now()))


if __name__ == '__main__':
    main()
