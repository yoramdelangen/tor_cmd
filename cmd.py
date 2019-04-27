#!/usr/bin/env python3
import click
from search import Searcher

@click.command()
@click.argument('search', nargs=1)
@click.option('--season', '-s', type=int, help='Season number; it will add the searchterm "S{num}" to the search. eg.`-s 1` -> S01')
@click.option('--episode', '-e', type=int, help='Episode number; it will add the searchterm "S{num}" to the search. eg.`-e 1` -> E01')
@click.option('--provider', '-p', type=str, default='', help='Search on certain providers: eztv, kickass, thepiratebay, torrentgalaxy. Add a `-` to exclude a provider')
@click.option('--quiet', '-q', is_flag=True, help='When true this will only show the cache result file relative path. Very usefull for programs that will use this package.')

def tor_cmd(search, season, episode, provider, quiet):
	click.clear()

	show = ''
	if season is not None:
		show += 's{:02d}'.format(season)

	if episode is not None:
		show += 'e{:02d}'.format(episode)

	if show != '':
		search += ' '+show

	# init searcher/webscrape framework
	s = Searcher(search)
	p = list(filter(None, provider.split(',')))
	lp = s.p

	# do we only show the cache filename, cause its quiet
	if quiet is True:
		callQuietMode(s, lp, p)

	click.echo('')
	click.echo('Searching: '+ search)
	click.echo('Providers: '+ ', '.join(s.p.keys()))
	click.echo('')

	for k in p:
		del lp[k]

	# search the web
	r = s.lookup(lp)

	# Can we load it from cache??
	if s.fromCache():
		click.echo('Load from cache')
		click.echo('')

	click.echo(s.show())
	click.echo('')

	# Check if we have results
	if not s.hasResults():
		click.echo('No results for'+ search)
		exit()

	idx = askForInput(s)

	click.echo('')
	click.secho('Magnet:', bold=True)
	click.echo('')
	click.secho(s.getMagnet(idx), fg='green')
	click.echo('')
	click.echo('Do `cmd+click` or `ctrl+click` for opening the magnet url.')

def callQuietMode(s, lp, p):
	for k in p:
		del lp[k]

	# search the web
	s.lookup(lp)
	click.echo(s.getCacheFilename())
	exit()

def askForInput(d):
	idx = click.prompt('Please enter a valid search index', type=int)

	if idx not in d.r.index:
		click.echo('')
		click.echo('Invalid search index given')

		return askForInput(d)

	return idx

if __name__ == '__main__':
	tor_cmd()
