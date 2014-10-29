#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.
from __future__ import print_function

import os
import sys
import yaml

from fontaine.font import FontFactory
from fontaine.cmap import Library

from bakery_cli.system import prun
from bakery_cli.utils import UpstreamDirectory


class App(object):

    commit = 'HEAD'
    process_files = []
    subset = []
    compiler = 'fontforge'
    ttfautohint = None
    afdko = ''
    downstream = True
    optimize = True
    license = ''
    pyftsubset = '--notdef-outline --name-IDs=* --hinting'
    notes = ''
    newfamily = ''
    fontcrunch = None

    def __init__(self):
        config = {}

        if os.path.exists('bakery.yaml'):
            config = yaml.load(open('bakery.yaml'))
        elif os.path.exists('bakery.yml'):
            config = yaml.load(open('bakery.yml'))

        self.commit = config.get('commit', 'HEAD')
        self.process_files = config.get('process_files', [])
        self.subset = config.get('subset', [])
        self.compiler = config.get('compiler', 'fontforge')
        self.ttfautohint = config.get('ttfautohint', '')
        self.afdko = config.get('afdko', '')

        self.downstream = config.get('downstream', True)
        self.optimize = config.get('optimize', True)
        self.license = config.get('license', '')
        self.pyftsubset = config.get('pyftsubset', '--notdef-outline --name-IDs=* --hinting')
        self.notes = config.get('notes', '')
        self.fontcrunch = config.get('fontcrunch')
        self.newfamily = config.get('newfamily', '')


def save(*args, **kwargs):
    print('bakery.yml exists...')
    print('Wrote bakery.yml.new')
    sys.exit(1)


def get_subsets_coverage_data(source_fonts_paths):
    """ Return dict mapping key to the corresponding subsets coverage

        {'subsetname':
            {'fontname-light': 13, 'fontname-bold': 45},
         'subsetname':
            {'fontname-light': 9, 'fontname-bold': 100}
        }
    """
    library = Library(collections=['subsets'])
    subsets = {}
    for fontpath in source_fonts_paths:
        try:
            font = FontFactory.openfont(fontpath)
        except AssertionError:
            continue
        for info in font.get_orthographies(_library=library):

            subsetname = info.charmap.common_name.replace('Subset ', '')
            if subsetname not in subsets:
                subsets[subsetname] = {}

            subsets[subsetname][fontpath] = info.coverage
    return subsets


def generate_subsets_coverage_list():
    directory = UpstreamDirectory('.')

    source_fonts_paths = []
    # `get_sources_list` returns list of paths relative to root.
    # To complete to absolute paths use python os.path.join method
    # on root and path
    for p in directory.ALL_FONTS:
        source_fonts_paths.append(p)
    return get_subsets_coverage_data(source_fonts_paths)


process_files = []

extensions = ['.sfd', '.ufo', '.ttx', '.ttf']

for path, dirs, files in os.walk('.'):

    for f in files:
        for ext in extensions:
            if not f.endswith(ext):
                continue
            process_files.append('/'.join([path, f]))

    for d in dirs:
        for ext in extensions:
            if not d.endswith(ext):
                continue
            process_files.append('/'.join([path, d]))

import urwid.curses_display
import urwid.raw_display
import urwid.web_display
import urwid

def show_or_exit(key):
    if key in ('q', 'Q', 'esc'):
        raise urwid.ExitMainLoop()


if urwid.web_display.is_web_request():
    Screen = urwid.web_display.Screen
else:
    Screen = urwid.curses_display.Screen


screen = Screen()
header = urwid.Text("Fontbakery Setup. Q exits.")


app = App()


widgets = []
if os.path.exists('.git/config'):
    githead = urwid.Text(u"Build a specific git commit, or HEAD? ")
    widgets.append(urwid.AttrMap(githead, 'key'))
    widgets.append(urwid.LineBox(urwid.Edit(edit_text=app.commit)))
    widgets.append(urwid.Divider())


widgets.append(urwid.AttrMap(urwid.Text('Which files to process?'), 'key'))
for f in process_files:
    try:
        state = app.process_files.index(f) >= 0
    except ValueError:
        state = False
    widgets.append(urwid.CheckBox(f, state=state))

widgets.append(urwid.Divider())
licenses = ['OFL.txt', 'LICENSE.txt', 'LICENSE']
group = []
widgets.append(
    urwid.AttrMap(
        urwid.Text('License filename?'), 'key'))
for f in licenses:
    if os.path.exists(f):
        widgets.append(urwid.RadioButton(group, f + ' (exists)', state=bool(f == app.license)))
    else:
        widgets.append(urwid.RadioButton(group, f, state=bool(f == app.license)))

widgets.append(urwid.Divider())
widgets.append(
    urwid.AttrMap(
        urwid.Text('What subsets do you want to create?'), 'key'))

subsets = generate_subsets_coverage_list()
for s in sorted(subsets):
    ll = ', '.join(set(['{}%'.format(subsets[s][k])
                        for k in subsets[s] if subsets[s][k]]))
    if ll:
        widgets.append(urwid.CheckBox('{0} ({1})'.format(s, ll), state=bool(s in app.subset)))


widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(
    urwid.CheckBox('Use ttfautohint?', state=bool(app.ttfautohint)), 'key'))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(
    urwid.Text('ttfautohint command line parameters?'), 'key'))

widgets.append(urwid.LineBox(urwid.Edit(edit_text=app.ttfautohint)))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(
    urwid.Text(('New font family name (ie, replacing repo'
                ' codename with RFN)?')), 'key'))

widgets.append(urwid.LineBox(urwid.Edit(edit_text=app.newfamily)))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(urwid.CheckBox('Use FontCrunch?', state=app.fontcrunch), 'key'))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(urwid.CheckBox('Run tests?', state=app.downstream), 'key'))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(urwid.CheckBox('Run optimization?', state=app.optimize), 'key'))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(
    urwid.Text('pyftsubset defaults parameters?'), 'key'))

widgets.append(urwid.LineBox(urwid.Edit(edit_text=app.pyftsubset)))

widgets.append(urwid.Divider())

widgets.append(urwid.AttrMap(
    urwid.Text('Which compiler to use?'), 'key'))

widgets.append(urwid.Divider())
quote = ('By default, bakery uses fontforge to build fonts from ufo.'
         ' But some projects use automake, or their own build system'
         ' and perhaps the AFDKO.')
widgets.append(urwid.Padding(urwid.Text(quote), left=4))
widgets.append(urwid.Divider())

choices = ['fontforge', 'afdko', 'make', 'build.py']
group = []
for choice in choices:
    widgets.append(urwid.RadioButton(group, choice, state=bool(choice == app.compiler)))


widgets.append(urwid.Divider())
widgets.append(urwid.AttrMap(
    urwid.Text('Notes to display on Summary page?'), 'key'))

widgets.append(urwid.LineBox(urwid.Edit(edit_text=app.notes)))

widgets.append(urwid.Button(u'Save and Exit', on_press=save))

header = urwid.AttrWrap(header, 'header')
lw = urwid.SimpleListWalker(widgets)

listbox = urwid.ListBox(lw)
listbox = urwid.AttrWrap(listbox, 'listbox')
top = urwid.Frame(listbox, header)


#     fill = urwid.Filler(txt, 'top')
palette = [('header', 'black', 'dark cyan', 'standout'),
           ('key', 'white', 'dark blue', 'bold'),
           ('listbox', 'light gray', 'black')]
loop = urwid.MainLoop(top, palette, screen, unhandled_input=show_or_exit)
loop.run()
