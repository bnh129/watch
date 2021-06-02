import sqlite3
import json
import time
import tornado.web
import tornado.ioloop
import tornado.template
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor


sql_select_exchange_quote_assets = """SELECT DISTINCT quote_asset, exchange FROM markets WHERE base_asset=?;"""

sql_select_asset_history = """SELECT * FROM markets WHERE exchange=? AND base_asset=? AND quote_asset=? AND ts >= ? AND ts <= ? ORDER BY ts ASC;"""

sql_select_assets = """SELECT DISTINCT base_asset FROM markets ASC;"""


class CryptoAssetHistoryRequestHandler(tornado.web.RequestHandler):

	db_path = "data/market.dat"
	executor = ThreadPoolExecutor(4)

	def initialize(self, path, logger):
		self.path = path
		self.logger = logger
		self.logger.info("Initialized.")

	@run_on_executor
	def get_data(self, exchange, base, quote):
		t_end = int(time.time())
		t_start = t_end - 86400 # 24 hr reporting period

		db = sqlite3.connect(self.db_path)
		cursor = db.cursor()
		cursor.execute(sql_select_asset_history, (exchange, base, quote, t_start, t_end,))
		db.commit()
		results = cursor.fetchall()

		return results

	@tornado.gen.coroutine
	def get(self, path):
		parts = path.split("/")
		exchange = parts[0]
		base_asset = parts[1]
		quote_asset = parts[2]

		data = yield self.get_data(exchange, base_asset, quote_asset)
		yield self.write(json.dumps(data))

class CryptoAssetsRequestHandler(tornado.web.RequestHandler):

	db_path = "data/market.dat"
	executor = ThreadPoolExecutor(4)

	def initialize(self, path, logger):
		self.path = path
		self.logger = logger
		self.logger.info("Initialized.")

	@run_on_executor
	def get_data(self, base):
		#self.logger.info("base: %s" % base)
		db = sqlite3.connect(self.db_path)
		cursor = db.cursor()
		cursor.execute(sql_select_exchange_quote_assets, (base,))
		db.commit()
		results = cursor.fetchall()
		#self.logger.info("%s" % (results))

		return results

	@tornado.gen.coroutine
	def get(self, path):
		asset = path.split("/")
		base_asset = asset[0]

		data = yield self.get_data(base_asset)
		yield self.write(json.dumps(data))

class CryptoWatchListRequestHandler(tornado.web.RequestHandler):

	db_path = "data/market.dat"
	executor = ThreadPoolExecutor(4)

	def initialize(self, path, logger):
		self.path = path
		self.logger = logger
		self.logger.info("Initialized.")

	@run_on_executor
	def get_data(self):
		db = sqlite3.connect(self.db_path)
		cursor = db.cursor()
		cursor.execute(sql_select_assets)
		db.commit()
		results = cursor.fetchall()

		return results

	@tornado.gen.coroutine
	def get(self):
		data = yield self.get_data()
		yield self.render(self.path + "www/index.ht", data=data)


