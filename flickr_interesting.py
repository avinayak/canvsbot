import urllib2
import json
import time
import random
import datetime

def save_image():
	rand_time = random.randrange(1104537600,int(time.time()))
	date = datetime.datetime.fromtimestamp(rand_time)

	response = urllib2.urlopen('https://api.flickr.com/services/rest/?method=flickr.interestingness.getList&api_key=a150f2418d88878966d18da8ed96d7ff&date=%s&extras=license&format=json&nojsoncallback=1&'%(date.strftime("%Y-%m-%d")))
	data = json.load(response)   

	ids = [ {"title":x["title"],"id":x["id"]} for x in data["photos"]["photo"] if x["license"]!="0"]

	print ids[0]["title"]
	response = urllib2.urlopen('https://api.flickr.com/services/rest/?method=flickr.photos.getSizes&api_key=a150f2418d88878966d18da8ed96d7ff&photo_id=%s&format=json&nojsoncallback=1'%ids[0]["id"])
	urls = json.load(response)   
	dlfile(urls["sizes"]["size"][5]["source"], "image.jpg")
	
def dlfile(url,name):
    # Open the url
    try:
        f = urllib2.urlopen(url)
        print "downloading " + url

        # Open our local file for writing
        with open(name, "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except HTTPError, e:
        print "HTTP Error:", e.code, url
    except URLError, e:
        print "URL Error:", e.reason, urllib2

if __name__ == '__main__':
	save_image()