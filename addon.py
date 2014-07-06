# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from xbmcgui import ListItem
from lib import wimpy
from routing import Plugin

addon = xbmcaddon.Addon()
session_id = addon.getSetting('session_id')
country_code = addon.getSetting('country_code') or 'NO'
user_id = addon.getSetting('user_id')
wimp = wimpy.Session(session_id, country_code, user_id)
plugin = Plugin()


def view(data_items, urls):
    list_items = []
    for item, url in zip(data_items, urls):
        li = ListItem(item.name)
        playable = plugin.route_for(url) is play
        li.setInfo('audio', {'title': '', 'plot': ''})
        list_items.append((url, li, not playable))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/')
def root():
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(search),
        ListItem('Search'), True)
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(login),
        ListItem('Login'), True)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/album/<album_id>')
def album_view(album_id):
    tracks = wimp.get_album(album_id)
    urls = [plugin.url_for(play, track_id=t.id) for t in tracks]
    view(tracks, urls)


@plugin.route('/artist/<artist_id>')
def artist_view(artist_id):
    albums = wimp.get_albums(artist_id)
    urls = [plugin.url_for(album_view, album_id=a.id) for a in albums]
    view(albums, urls)


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard(heading='Search')
    keyboard.doModal()
    query = keyboard.getText()
    if query:
        artist = wimp.search('artists', query)
        urls = [plugin.url_for(artist_view, artist_id=a.id) for a in artist]
        view(artist, urls)


@plugin.route('/login')
def login():
    dialog = xbmcgui.Dialog()
    username = dialog.input('Username')
    if username:
        password = dialog.input('Password')
        if password:
            if wimp.login(username, password):
                addon.setSetting('session_id', wimp.session_id)
                addon.setSetting('country_code', wimp.country_code)
                addon.setSetting('user_id', wimp.user.id)


@plugin.route('/play/<track_id>')
def play(track_id):
    url = wimp.get_media_url(track_id)
    li = ListItem('')
    li.setProperty('mimetype', 'audio/mp4')

    #TODO: paplayer fails to play these streams, investigate
    player = xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER)
    player.play(url)
    while player.isPlaying:
        xbmc.sleep(1000)


if __name__ == '__main__':
    plugin.run()
