# -*- coding: utf-8 -*-
#/*
# *      Copyright (C) 2010 Libor Zoubek
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */
import urllib2,re,string,sys
import xbmcaddon,xbmc,xbmcgui,xbmcplugin

BASE_URL='http://abradio.cz'
PLAYER_BASE_URL='http://static.abradio.cz'
CZECH_CHARS=u"ěščřžýáíéúóČŽ"
TITLE=u"[;\&-\/ \.\w\d"+CZECH_CHARS+"]+"

def request(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return unicode(data,'UTF-8')

def request2(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

def add_dir(name,id,logo):
	name = name.replace('&amp;','&')
        u=sys.argv[0]+"?"+id
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=logo)
        liz.setInfo( type="Audio", infoLabels={ "Title": name } )
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def add_stream(name,url,bitrate,logo):
	name = name.replace('&amp;','&')
	if url.find('http://') < 0:
		url = PLAYER_BASE_URL+url
	url = parse_asx(url)
	li=xbmcgui.ListItem(name,path = url,iconImage="DefaultAudio.png",thumbnailImage=logo)
        li.setInfo( type="Music", infoLabels={ "Title": name,"Size":bitrate } )
	li.setProperty("IsPlayable","true")
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li,isFolder=False)

def parse_asx(url):
	if not url.endswith('asx'):
		return url
	data = request2(url)
	refs = re.compile('.*<Ref href = \"((mms|http)://[\?\d:\w_\.\/=-]+)\".*').findall(data,re.IGNORECASE|re.DOTALL|re.MULTILINE)
	urls = []
	for ref in refs:
		stream = parse_asx(ref[0])
		urls.append(stream)
	if urls == []:
		print 'Unable to parse '+url
		print data
		return ''
	return urls[-1]

def substring(data,start,end):
	i1 = data.find(start)
	i2 = data.find(end,i1+1)
	return data[i1:i2]

def get_categories():
	data = substring(request(BASE_URL),'<div id=\"categories\"','</div>')
	for cat in re.compile(u"<li><a href=\"(?P<dest>[\/\w-]+)\" title=\""+TITLE+"\">(?P<name>"+TITLE+")</a></li>").finditer(data,re.IGNORECASE|re.DOTALL):
		add_dir(cat.group('name'),'category='+cat.group('dest'),'')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def list_category(category):
	data = request(BASE_URL+category)
	data = substring(data,'<ul class=\"stationlist\">','</ul>')
	for station in re.compile(u"<li?[= \d\w\"]+><h2[\=\w\d\. /\"]+><a href=\"(?P<url>[-:\.\w\d/]+)\" title=\""+TITLE+"\">(?P<name>"+TITLE+")</a>").finditer(data,re.IGNORECASE|re.DOTALL):
		i=re.match('.*/([\d]+)/.*',station.group('url'))
		station_id=i.group(1)
		add_dir(station.group('name'),'station='+station_id,BASE_URL+'/data/s/'+station_id+'/logo.gif')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

#def get_logo(station):
#	data = substring(request(station),'<link rel=\"image_src\"','/>')
#	return BASE_URL+re.compile('.*href=\"([-\d\w\/\.]+)\"').findall(data)[0]

def station_name(data):
	data = substring(data,'<div class=\"logo\">','</h1>')
	return re.compile('.*<h1>('+TITLE+')').findall(data)[0]

def station_logo(data):
	logo = substring(data,'<img class=\"logo\" src=\"','alt')
	logo = re.compile('.*src=\"([\w\d\/\.]+)\".*').findall(logo)
	return BASE_URL+logo[0]

def resolve_station(id):
	data = request(PLAYER_BASE_URL+'/player/'+id)
	name =  station_name(data)
	logo = station_logo(data)
	data = substring(data,'<div id=\"playerplugin\">','</select>')
	for quality in re.compile(u"<option value=\"(?P<stream>[\d]+)\"([=\w\" ]+)?>(?P<name>["+CZECH_CHARS+"\(\)\d\w ]+)</option>").finditer(data,re.IGNORECASE|re.DOTALL):
		stream = resolve_station_link(PLAYER_BASE_URL+'/player/'+id+'/'+quality.group('stream'))
		bitrate = quality.group('name')[quality.group('name').find('(')+1:len(quality.group('name'))-5]
		bit = 0
		try:
			bit = int(bitrate)
		except:
			pass
		add_stream(name,stream,bit,logo)
	xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
	xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X")
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def resolve_station_link(link):
	data = substring(request(link),'<object id=\"iRadio\"','</object>')
	link = re.compile('.*<param name=\"url\" value=\"([-/\d\w\.:]+)\".*').match(data)
	if link == None:
		return ''
	return link.group(1)

def get_params():
        param={}
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

__settings__ = xbmcaddon.Addon(id='plugin.audio.abradio.cz')
__language__ = __settings__.getLocalizedString
params=get_params()
if params=={}:
	get_categories()
if 'category' in params.keys():
	list_category(params['category']+'/')
if 'station' in params.keys():
	resolve_station(params['station'])
