import feedparser
import sys
import urlparse
import youtube_dl

print 'Olls Youtube Subscription Downloader'

feedUrl = 'http://gdata.youtube.com/feeds/api/users/' + sys.argv[1] + '/uploads?max-results=1&alt=rss&orderby=published'
print 'Feed URL: ' + feedUrl + '\n'

feed = feedparser.parse(feedUrl)

videoLink = feed['entries'][0]['links'][0]['href']
print 'Video Link: ' + videoLink + '\n'

youtube_dl.main()