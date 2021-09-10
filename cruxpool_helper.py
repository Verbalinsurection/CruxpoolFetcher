#!/usr/bin/python3

"""Cruxpool API module"""

from datetime import datetime, timedelta

import pytz

from .api_request import ApiReq

CAPI_BASE = 'https://www.cruxpool.com/api/{coin}'
CAPI_ESTIM_EARN = '/estimatedEarnings/{hashrate}'
CAPI_MINER = '/miner/{minerId}'
CAPI_BALANCE = '/balance'
CAPI_PAYMENTS = '/payments'
CAPI_HISTORY = '/history/month'

DATE_FORMAT = '%Y-%m-%d %H:%M'
COIN_TAG = '{coin}'
MINER_TAG = '{minerId}'
HASHRATE_TAG = '{hashrate}'


def hrate_mh(hashrate):
    return round(hashrate / 1000000, 2)


class CruxpoolHelper():
    def __init__(self, coin, wallet, ref_hrate, pay_amount):
        self.__coin = coin
        self.__wallet = wallet
        self.__ref_hrate = ref_hrate
        self.workers = []
        self.payouts = []
        self.history = []
        self.__last_error = None
        self.__min_payout = pay_amount

        self.__capi_base = CAPI_BASE.replace(COIN_TAG, coin)
        self.__capi_estim_earn = \
            self.__capi_base + \
            CAPI_ESTIM_EARN.replace(HASHRATE_TAG, str(ref_hrate))
        self.__capi_miner = \
            self.__capi_base + CAPI_MINER.replace(MINER_TAG, wallet)
        self.__capi_balance = self.__capi_miner + CAPI_BALANCE
        self.__capi_payments = self.__capi_miner + CAPI_PAYMENTS
        self.__capi_history = self.__capi_miner + CAPI_HISTORY

    def update(self):
        self.__last_error = None
        self.__update_miner()
        self.__get_estim_earn()
        self.__get_balance()
        self.__get_payout()
        self.__update_next_payout()
        self.__update_history()
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
                if self.__coin_min == 0:
                    self.__coin_min = 0.0
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

    def __update_next_payout(self):
        to_gain = self.__min_payout - self.__balance
        if self.__coin_min > 0:
            minutes_to_tresh = to_gain / self.__coin_min
        else:
            minutes_to_tresh = 0

        self.__next_payout = \
            datetime.utcnow() + \
            timedelta(minutes=minutes_to_tresh)
        self.__next_payout = self.__next_payout.replace(tzinfo=pytz.UTC)

        time_diff_next = self.__next_payout - datetime.now().astimezone()

        self.__unpaid_at_next = round(
            (time_diff_next.total_seconds() *
             (self.__coin_min / 60) + self.__balance), 5)

        self.__next_payout_txt = \
            self.__next_payout.strftime(DATE_FORMAT)

    def __update_history(self):
        api = ApiReq()
        miner_json = api.api_request(self.__capi_history)
        self.__last_error = api.last_error
        if miner_json is not None and api.last_error is None:
            try:
                data_json = miner_json['data']
                for history in data_json['history']:
                    self.history.append(History(history))
            except KeyError as e:
                self.__last_error = '__update_history: ' + str(e)
        else:
            if self.__last_error is None:
                self.__last_error = \
                    '__update_history -- Can\'t retrieve json result'

    @property
    def wallet(self):
        return self.__wallet

    @property
    def pool_name(self):
        return 'Cruxpool'

    @property
    def hrate_reported(self):
        return self.__hrate_reported

    @property
    def hrate_current(self):
        return self.__hrate_current

    @property
    def hrate_ref(self):
        return self.__ref_hrate

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

    @property
    def next_payout(self):
        return self.__next_payout

    @property
    def unpaid_at_next(self):
        return self.__unpaid_at_next

    @property
    def valid_shares(self):
        shares = 0
        for worker in self.workers:
            shares = shares + worker.shares

        return shares

    @property
    def stale_shares(self):
        shares = 0
        for worker in self.workers:
            shares = shares + worker.stale_shares

        return shares

    @property
    def invalid_shares(self):
        shares = 0
        for worker in self.workers:
            shares = shares + worker.invalid_shares

        return shares


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


class History():
    def __init__(self, json_data):
        self.h_date = datetime.utcfromtimestamp(
            json_data['timestamp'])
        self.amount = round(json_data['amount'] / 10e7, 5)
