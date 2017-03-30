#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Inspired by the Simple IMDB scraping script
# David Dohan via https://gist.github.com/dmrd/9340468
# massively updated by Jason Fleischer 3/14/2017 for current IMdB html format
#
# usage: go to IMdB website, initiate a search of the type you want to do 
#     which will probably mean using advanced search BTW
#     Look at the URL on the search results page, you'll be able to 
#     figure out how to generalize that to what you want to scrape.
#     Call scrape_movies(url) for that same search from Python.
#     You can make your own version of scrape_many(...) to parameterize 
#     that search.  The current version of scrape_many(...) grabs the top XX 
#     movies, according to US Box Office $$, from each year you ask it to.
#
 
import urllib2
import bs4
import time
import json
import re

#%%
def scrape_movies(url):
    html = urllib2.urlopen(url).read()
    soup = bs4.BeautifulSoup(html)

    titles = soup.findAll(class_="lister-item-content")

    movies = []

    for title in titles:
        try:
            # First hyperlink is the title
            name = None
            name_block = title.find("a")
            if name_block: 
                name = name_block.text
                                   
            # Release date
            # <span "lister-item-year text-muted unbold">(1993)</span>
            year = None
            year_block = title.findAll(class_="lister-item-year") # sometimes there are multiple year blocks, for instance episodes of a series.  we want the last one which will be the episode
            if year_block:
                m = re.search('[0-9]{4}',year_block[-1].text) # find the year as 4 contiguous integers
                year = int(m.group(0)) 
                
            # in those cases where there are two  year blocks, we need to get the episode name
            # then we no longer need the first hyperlink for the name, but the 2nd (or 3rd or whatever)
            if len(year_block)==2:
                name_block = title.findAll("a")
                if name_block: 
                    name = name_block[0].text + u':' + name_block[1].text
                                                                          
            # User rating
            # <meta itemprop="ratingValue" content="8.1" />
            # <meta itemprop="bestRating" content="10" />
            # <meta itemprop="ratingCount" content="653966" />
            rating = None
            metacontent = title.find( attrs={"itemprop":"ratingValue"})
            if metacontent:
                rating = float(metacontent['content'])
            
            votes = None
            metacontent = title.find( attrs={"itemprop":"ratingCount"})
            if metacontent:
                votes = int(metacontent['content'])
            
            metascore_block = title.find(class_="metascore")
            metascore = None
            if metascore_block:
                metascore = int(metascore_block.text.strip())

            # Outline/synopysis: its the 2nd <p> tag!
            # <p class="text-muted">
            # During a preview tour, a theme park suffers a major power breakdown that allows its cloned dinosaur exhibits to run amok.</p>
            plist = title.find_all("p")
            outline = None
            if plist[1]:
                outline = plist[1].text    

            # Get actors and directors: the 3rd <p> tag!
            #   <p class="">
            # Director:
            # <a href="/name/nm0000229/?ref_=adv_li_dr_0">Steven Spielberg</a>
            #          <span class="ghost">|</span> 
            #  Stars:
            # <a href="/name/nm0000554/?ref_=adv_li_st_0">Sam Neill</a>, 
            # <a href="/name/nm0000368/?ref_=adv_li_st_1">Laura Dern</a>, 
            # <a href="/name/nm0000156/?ref_=adv_li_st_2">Jeff Goldblum</a>, 
            # <a href="/name/nm0000277/?ref_=adv_li_st_3">Richard Attenborough</a>
            # </p>
            directors = None
            actors = None
            if plist[2]:
                credits = plist[2].text
                if "|" in credits:
                    directors, actors = credits.split("|")

                    _,directors=directors.split(':')
                    directors=re.split('\n|, \n',directors.strip())
                    
                    _,actors=actors.split(':')
                    actors=re.split('\n|, \n',actors.strip())
                elif "Star" in credits: # don't have a director listed
                    _,actors=credits.split(':')
                    actors=re.split('\n|, \n',actors.strip())
                elif "Director" in credits: # don't have stars listed
                    _,directors=credits.split(':')
                    directors=re.split('\n|, \n',directors.strip())
                    
                    
            # Get US Box Office gross: the last span item inside the 4th <p> tag! 
            # <<p class="sort-num_votes-visible">\n<span class="text-muted">Votes:</span>\n<span data-value="653966" name="nv">653,966</span>\n<span class="ghost">|</span> <span class="text-muted">Gross:</span>\n<span data-value="356,784,000" name="nv">$356.78M</span>\n</p>
            usbox = None
            usbox_block = plist[3].find_all("span")
            if usbox_block:
                usbox = int(usbox_block[-1]["data-value"].replace(',',''))
            
            # Scrape set of genres
            # <span class="genre"><a href="/genre/comedy">Comedy</a> |
            #       <a href="/genre/drama">Drama</a> | <a href="/genre/sci_fi">Sci-Fi</a></span>
            genre_block = title.find(class_="genre")
            genres = None
            if genre_block:
                genres = genre_block.text.strip().split(', ')

            # "100 mins. -> 100"
            # <span class="runtime">103 mins.</span>
            runtime_block = title.find("span", "runtime")
            runtime = None
            if runtime_block:
                runtime = int(runtime_block.text.split()[0])

            # <span class="certificate">PG-13</span>
            mpaa_block = title.find("span", "certificate")
            mpaa = None
            if mpaa_block:
                mpaa = mpaa_block.text
             

            movies.append({"name": name,
                           "year": year,
                           "rating": rating,
                           "metascore": metascore,
                           "votes": votes,
                           "outline": outline,
                           "directors": directors,
                           "actors": actors,
                           "genres": genres,
                           "runtime": runtime,
                           "usbox": usbox,
                           "mpaa": mpaa})
        except:
            print("Error while processing {}: {}".format(url,name))
            #useful debug:
            #return title
        
    return movies
#%%

def scrape_many( years, pages_per_year=2, second_delay=1,
        url_format = "http://www.imdb.com/search/title?release_date={yr},{yr}&title_type=feature&sort=boxoffice_gross_us,desc&page={pg}"):
        
    """
    For every year in _years_ scrape _pages_per_year_  total pages

    Default IMDB url loads 50 movies per page
    """
    movies = []
    for year in years:
        for page in range(1,pages_per_year+1):
            print("Scraping results for year {}, page {}".format(year,page))
            movies.extend(scrape_movies(url_format.format(yr=year,pg=page)))
            time.sleep(second_delay)
    
    return movies


def save_movies(movies, path):
    with open(path, 'w') as f:
        json.dump(movies, f, sort_keys=True, indent=4,
                  separators=(',', ': '))

def load_movies(path):
    with open(path, 'r') as f:
        movies = json.load(f)
    return movies


#allmovies = scrape_many(range(1946,2017),pages_per_year=4)
