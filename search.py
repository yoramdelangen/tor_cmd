import math
from tqdm import tqdm
from tabulate import tabulate
from webscrap import Scraper, Config
from urllib.parse import quote_plus

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

	def cleanNum_(self, x) -> int:
		if x is None or type(x) is not str and math.isnan(x):
			return 0
		elif not x.isdigit():
			return 0

		return int(''.join(e for e in str(x) if e.isalnum()))

	def lookup(self, provider=None, confPath='providers'):
		"""
		Start searching on the given provider.
		"""

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

		return self.r

	def hasResults(self):
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
		return self.r.iloc[idx]['magnet']
