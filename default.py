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
TITLE=u"[-\/ \.\w\d"+CZECH_CHARS+"]+"

def request(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return unicode(data,'UTF-8')

def add_dir(name,id):
        u=sys.argv[0]+"?"+id
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png")
        liz.setInfo( type="Audio", infoLabels={ "Title": name } )
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def add_stream(name,url):
	if url.find('http://') < 0:
		url = PLAYER_BASE_URL+url
	li=xbmcgui.ListItem(name,path = url)
        li.setInfo( type="Audio", infoLabels={ "Title": name } )
	li.setProperty("IsPlayable","true")
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li,isFolder=False)

def get_categories():
	data = request(BASE_URL)
	# get div with categories
	i1 = data.find('<div id=\"categories\"')
	i2 = data.find('</div>',i1)
	data = data[i1:i2]
	for cat in re.compile(u"<li><a href=\"(?P<dest>[\/\w-]+)\" title=\""+TITLE+"\">(?P<name>["+CZECH_CHARS+"\w\.\/\ ]+)</a></li>").finditer(data,re.IGNORECASE|re.DOTALL):
		add_dir(cat.group('name'),'category='+cat.group('dest'))
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def list_category(category):
	data = request(BASE_URL+category)
	i1 = data.find('<ul class=\"stationlist\">')
	i2 = data.find('</ul>',i1)
	data = data[i1:i2]
	for station in re.compile(u"<li?[= \d\w\"]+><h2[\=\w\d\. /\"]+><a href=\"(?P<url>[-:\.\w\d/]+)\" title=\""+TITLE+"\">(?P<name>"+TITLE+")</a>").finditer(data,re.IGNORECASE|re.DOTALL):
		i=re.match('.*/([\d]+)/.*',station.group('url'))
		station_id=i.group(1)
		add_dir(station.group('name'),'station='+station_id)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def resolve_station(id):
	data = request(PLAYER_BASE_URL+'/player/'+id)
	i1 = data.find('<div id=\"playerplugin\">')
	i2 = data.find('</select>',i1)
	data = data[i1:i2]
	for quality in re.compile(u"<option value=\"(?P<stream>[\d]+)\"([=\w\" ]+)?>(?P<name>["+CZECH_CHARS+"\(\)\d\w ]+)</option>").finditer(data,re.IGNORECASE|re.DOTALL):
		stream = resolve_station_link(PLAYER_BASE_URL+'/player/'+id+'/'+quality.group('stream'))
		add_stream(quality.group('name'),stream)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def resolve_station_link(link):
	data = request(link)
	i1 = data.find('<object id=\"iRadio\"')
	i2 = data.find('</object>',i1)
	data = data[i1:i2]
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
