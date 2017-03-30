# imdbscrape
#
# Inspired by the Simple IMDB scraping script
# David Dohan via https://gist.github.com/dmrd/9340468
# massively updated by Jason Fleischer 3/14/2017 for current IMdB html format
#
# usage: go to IMdB website, initiate a search of the type you want to do. Look at the URL on the search results page, you'll be able to figure out how to generalize that to what you want to scrape. Call scrape_movies(url) for that same search from Python. You can make your own version of scrape_many(...) to parameterize that search.  The current version of scrape_many(...) grabs the top XX movies, according to US Box Office $$, from each year you ask it to.
#
