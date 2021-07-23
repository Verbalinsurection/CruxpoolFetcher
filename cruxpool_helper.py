#!/usr/bin/python3

"""Cruxpool API module"""

from api_request import ApiReq
from datetime import datetime

CAPI_BASE = 'https://www.cruxpool.com/api/{coin}'
CAPI_ESTIM_EARN = '/estimatedEarnings/{hashrate}'
CAPI_MINER = '/miner/{minerId}'
CAPI_BALANCE = '/balance'
CAPI_PAYMENTS = '/payments'

DATE_FORMAT = '%Y-%m-%d %H:%M'
COIN_TAG = '{coin}'
MINER_TAG = '{minerId}'
HASHRATE_TAG = '{hashrate}'


def hrate_mh(hashrate):
    return round(hashrate / 1000000, 2)


class CruxpoolHelper():
    def __init__(self, coin, wallet, ref_hrate):
        self.__coin = coin
        self.__wallet = wallet
        self.__ref_hrate = ref_hrate
        self.workers = []
        self.payouts = []
        self.__last_error = None

        self.__capi_base = CAPI_BASE.replace(COIN_TAG, coin)
        self.__capi_estim_earn = \
            self.__capi_base + \
            CAPI_ESTIM_EARN.replace(HASHRATE_TAG, str(ref_hrate))
        self.__capi_miner = \
            self.__capi_base + CAPI_MINER.replace(MINER_TAG, wallet)
        self.__capi_balance = self.__capi_miner + CAPI_BALANCE
        self.__capi_payments = self.__capi_miner + CAPI_PAYMENTS

    def update(self):
        self.__last_error = None
        self.__update_miner()
        self.__get_estim_earn()
        self.__get_balance()
        self.__get_payout()
        if self.__last_error is not None:
            return False
        return True

    def __update_miner(self):
        api = ApiReq()
        miner_json = api.api_request(self.__capi_miner)
        self.__last_error = api.last_error
        if miner_json is not None and api.last_error is None:
            try:
                data_json = miner_json['data']
                self.__hrate_reported = hrate_mh(data_json['reportedHashrate'])
                self.__hrate_current = hrate_mh(data_json['realtimeHashrate'])
                self.__hrate_3h = hrate_mh(data_json['hashrate'])
                self.__hrate_day = hrate_mh(data_json['avgHashrate'])
                self.__coin_min = data_json['coinPerMins']
                self.workers.clear()
                for json_worker in data_json['workers']:
                    worker = Worker(json_worker,
                                    data_json['workers'][json_worker])
                    self.workers.append(worker)
            except KeyError as e:
                self.__last_error = '__update_miner: ' + str(e)
            self.__stat_time = datetime.utcnow()
            self.__stat_time_txt = self.stat_time.strftime(DATE_FORMAT)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__update_miner -- Can\'t retrieve json result'

    def __get_estim_earn(self):
        api = ApiReq()
        miner_json = api.api_request(self.__capi_estim_earn)
        self.__last_error = api.last_error
        if miner_json is not None and api.last_error is None:
            try:
                data_json = miner_json['data']
                self.__earn_hour = data_json['estEarningsPerHour']
                self.__earn_day = data_json['estEarningsPerDay']
                self.__earn_month = data_json['estEarningsPerMonth']
                self.__earn_week = data_json['estEarningsPerWeek']
            except KeyError as e:
                self.__last_error = '__get_estim_earn: ' + str(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__get_estim_earn -- Can\'t retrieve json result'

    def __get_balance(self):
        api = ApiReq()
        miner_json = api.api_request(self.__capi_balance)
        self.__last_error = api.last_error
        if miner_json is not None and api.last_error is None:
            try:
                data_json = miner_json['data']
                self.__balance = round(data_json['balance'] / 10e7, 2)
            except KeyError as e:
                self.__last_error = '__get_balance: ' + str(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__get_balance -- Can\'t retrieve json result'

    def __get_payout(self):
        api = ApiReq()
        miner_json = api.api_request(self.__capi_payments)
        self.__last_error = api.last_error
        if miner_json is not None and api.last_error is None:
            try:
                data_json = miner_json['data']
                for payout in data_json['payments']:
                    self.payouts.append(Payout(payout))
            except KeyError as e:
                self.__last_error = '__get_payout: ' + str(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__get_payout -- Can\'t retrieve json result'

    @property
    def hrate_reported(self):
        return self.__hrate_reported

    @property
    def hrate_current(self):
        return self.__hrate_current

    @property
    def hrate_3h(self):
        return self.__hrate_3h

    @property
    def hrate_day(self):
        return self.__hrate_day

    @property
    def coin_min(self):
        return self.__coin_min

    @property
    def stat_time(self):
        return self.__stat_time

    @property
    def stat_time_txt(self):
        return self.__stat_time_txt

    @property
    def last_error(self):
        return self.__last_error

    @property
    def earn_hour(self):
        return self.__earn_hour

    @property
    def earn_day(self):
        return self.__earn_day

    @property
    def earn_month(self):
        return self.__earn_month

    @property
    def earn_week(self):
        return self.__earn_week

    @property
    def balance(self):
        return self.__balance


class Worker():
    def __init__(self, name, json_data):
        self.__last_error = None
        self.__name = name
        self.__hrate_reported = hrate_mh(json_data['reported'])
        self.__hrate_current = hrate_mh(json_data['realtimehr'])
        self.__hrate_3h = hrate_mh(json_data['hr'])
        self.__hrate_day = hrate_mh(json_data['hr2'])
        self.__shares = json_data['shares']
        self.__invalid_shares = json_data['invalidShares']
        self.__stale_shares = json_data['staleShares']

    @property
    def name(self):
        return self.__name

    @property
    def hrate_reported(self):
        return self.__hrate_reported

    @property
    def hrate_current(self):
        return self.__hrate_current

    @property
    def hrate_3h(self):
        return self.__hrate_3h

    @property
    def hrate_day(self):
        return self.__hrate_day

    @property
    def shares(self):
        return self.__shares

    @property
    def invalid_shares(self):
        return self.__invalid_shares

    @property
    def stale_shares(self):
        return self.__stale_shares

    @property
    def last_error(self):
        return self.__last_error


class Payout():
    def __init__(self, json_data):
        self.paid_on = datetime.utcfromtimestamp(
            json_data['timestamp'])
        self.paid_on_txt = self.paid_on.strftime(DATE_FORMAT)
        self.amount = round(json_data['amount'] / 10e7, 5)
        self.tx = json_data['tx']
