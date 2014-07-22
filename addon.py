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

def login():
    dialog = xbmcgui.Dialog()
    username = dialog.input('Username')
    if username:
        password = dialog.input('Password')
        if password:
            if wimp.login(username, password):
                addon.setSetting('session_id', wimp.session_id)
                addon.setSetting('country_code', wimp.country_code)
                addon.setSetting('user_id', unicode(wimp.user.id))
                return
    raise Exception('failed to login')

if not session_id:
    login()

plugin = Plugin()


def view(data_items, urls):
    list_items = []
    for item, url in zip(data_items, urls):
        li = ListItem(item.name)
        playable = plugin.route_for(url) is play
        if playable:
            li.setProperty('isplayable', 'true')
        list_items.append((url, li, not playable))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


def add_tracks(tracks):
    xbmcplugin.setContent(plugin.handle, 'songs')
    list_items = []
    for track in tracks:
        url = plugin.url_for(play, track_id=track.id)
        li = ListItem(track.name)
        li.setProperty('isplayable', 'true')
        li.setInfo('music', {
            'title': track.name,
            'tracknumber': track.track_num,
            'artist': track.artist.name,
            'album': track.album.name})
        if track.album:
            li.setThumbnailImage(track.album.image)
        list_items.append((url, li, False))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


def add_directory(title, view_func):
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(view_func), ListItem(title), True)


def urls_from_id(view_func, items):
    return [plugin.url_for(view_func, item.id) for item in items]


@plugin.route('/')
def root():
    add_directory('My music', my_music)
    add_directory('New', not_implemented)
    add_directory('Recommended', not_implemented)
    add_directory('Top', not_implemented)
    add_directory('Playlist Browser', not_implemented)
    add_directory('Genre Browser', not_implemented)
    add_directory('Search', search)
    add_directory('Logout', logout)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/my_music')
def my_music():
    add_directory('Playlists', my_playlists)
    add_directory('Favourite Artists', favourite_artists)
    add_directory('Favourite Albums', favourite_albums)
    add_directory('Favourite Tracks', favourite_tracks)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/not_implemented')
def not_implemented():
    raise NotImplementedError()


@plugin.route('/album/<album_id>')
def album_view(album_id):
    tracks = wimp.get_album_tracks(album_id)
    add_tracks(tracks)


@plugin.route('/artist/<artist_id>')
def artist_view(artist_id):
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(top_tracks, artist_id),
        ListItem('Top Tracks'), True
    )
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(artist_radio, artist_id),
        ListItem('Artist Radio'), True
    )
    albums = wimp.get_artist_albums(artist_id) + \
             wimp.get_artist_albums_ep_singles(artist_id) + \
             wimp.get_artist_albums_other(artist_id)
    view(albums, urls_from_id(album_view, albums))


@plugin.route('/artist/<artist_id>/radio')
def artist_radio(artist_id):
    tracks = wimp.get_artist_radio(artist_id)
    add_tracks(tracks)


@plugin.route('/artist/<artist_id>/top')
def top_tracks(artist_id):
    tracks = wimp.get_artist_top_tracks(artist_id)
    add_tracks(tracks)


@plugin.route('/playlist/<playlist_id>')
def playlist_view(playlist_id):
    tracks = wimp.get_playlist_tracks(playlist_id)
    add_tracks(tracks)


@plugin.route('/user_playlists')
def my_playlists():
    items = wimp.user.playlists
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/favourite_artists')
def favourite_artists():
    items = wimp.user.favourite_artists
    view(items, urls_from_id(artist_view, items))


@plugin.route('/favourite_albums')
def favourite_albums():
    items = wimp.user.favourite_albums
    view(items, urls_from_id(album_view, items))


@plugin.route('/favourite_tracks')
def favourite_tracks():
    items = wimp.user.favourite_tracks
    add_tracks(items)


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard(heading='Search')
    keyboard.doModal()
    query = keyboard.getText()
    if query:
        artist = wimp.search('artists', query)
        view(artist, urls_from_id(artist_view, artist))


@plugin.route('/logout')
def logout():
    addon.setSetting('session_id', '')
    addon.setSetting('country_code', '')
    addon.setSetting('user_id', '')


@plugin.route('/play/<track_id>')
def play(track_id):
    media_url = wimp.get_media_url(track_id)
    host, app, playpath = media_url.split('/', 3)
    rtmp_url = 'rtmp://%s app=%s playpath=%s' % (host, app, playpath)
    li = ListItem('', path=rtmp_url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


if __name__ == '__main__':
    plugin.run()
