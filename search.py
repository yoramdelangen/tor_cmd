import math, os
from tqdm import tqdm
from tabulate import tabulate
from webscrap import Scraper, Config
from urllib.parse import quote_plus
import pandas as pd
from slugify import slugify


class Searcher():
	def __init__(self, searchTerm):
		self.s = searchTerm
		self.p = {
			'eztv': 'EzTV',
			'kickass': 'Kickass Torrent',
			'thepiratebay': 'The Pirate Bay',
			'torrentgalaxy': 'TorrentGalaxy',
			# 'torrentz2': 'TorrentZ2'
		}
		self.f = ['name', 'seeders', 'leechers', 'size', 'magnet', 'provider']
		self.r = None
		self.fc = False

	def cleanNum_(self, x) -> int:
		if x is None or type(x) is not str and math.isnan(x):
			return 0
		elif not x.isdigit():
			return 0

		return int(''.join(e for e in str(x) if e.isalnum()))

	def fromCache(self) -> bool:
		"""
		Was the search loaded from cache
		"""
		return self.fc

	def lookup(self, provider=None, confPath='providers'):
		"""
		Start searching on the given provider.
		"""

		# Check if we searched for it already....
		# When found cache file load it and return it...
		if self.hasCache():
			self.fc = True
			return self.loadCache()

		# set default all providers
		if provider is None:
			provider = self.p

		# init scraper
		s = Scraper(self.f, provider)
		s.collectionsPath = confPath

		bar = tqdm(total=len(provider), leave=False)

		for collect in s.getCollections():
			config = Config(collect)

			s.setConfig(config)

			url = config.get('url')
			url = url.format(quote_plus(self.s))

			bar.update()

			if config.hasPagination():
				for i in range(1, config.getPagination()+1):
					url = url.format(i)
					if config.withDetails():
						s.scrapePageWithDetails(url)
						continue
					s.scrapePage(url)
				continue

			# When no pagination is involved
			if config.withDetails():
				s.scrapePageWithDetails(url)
				continue

			s.scrapePage(url)

		bar.close()

		r = s.getDataset()

		r['seeders'] = r['seeders'].apply(self.cleanNum_)
		r['leechers'] = r['leechers'].apply(self.cleanNum_)
		r['size'].fillna('', inplace=True)

		self.r = r[r['seeders'] > 0]
		self.r = self.r.sort_values(by='seeders', ascending=False)

		# TODO: store within cache file
		self.storeCache(self.r)

		return self.r

	def hasResults(self):
		"""
		Check if the result set is not empty
		"""
		return not self.r.empty

	def show(self, fmt='tablefmt'):
		"""
		Show the search results within
		"""
		r = self.r[['provider', 'name', 'seeders', 'leechers', 'size']] \
			.to_dict('records')

		h = {
			'name': 'Name',
			'seeders': 'Seeders',
			'leechers': 'Leechers',
			'size': 'Size',
			'provider': 'Provider'
		}

		return tabulate(r, headers=h, tablefmt=fmt, showindex='always')

	def getMagnet(self, idx: int):
		"""
		Get magnet URL from the results
		"""
		magnet = self.r.iloc[idx]['magnet']

		return magnet.replace(' ', '+')

	def getCacheFilename(self):
		"""
		Get the cache filename
		"""
		cacheSlug = slugify(self.s, to_lower=True)

		return 'caches/%s.tor-cache' % cacheSlug

	def loadCache(self):
		"""
		Load cache file.
		"""
		if not self.hasCache():
			raise Exception('Cache did not exists for search '+ self.s)

		self.r = pd.read_csv(self.getCacheFilename());

		return self.r

	def storeCache(self, results: pd.DataFrame):
		"""
		Store the results within a cache file.
		"""
		results.to_csv(self.getCacheFilename(), index=False)

	def hasCache(self):
		"""
		Check if there a cache file for this search
		"""
		return os.path.isfile(self.getCacheFilename())

