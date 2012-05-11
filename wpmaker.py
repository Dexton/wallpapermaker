#!/usr/bin/env python
# TODO, before I release:
#
#   rename wpmaker.py and wpmaker_tray.py to remove .py extension
#       - for being like an executable on linux
#
#   make path able to be set as a list
#       - create multiple imagequeues
#       - select a random queue when calling make_wallpaper
#       - chances of each queue reliant upon the ratio between sum of the queue sizes and size of each queue
#
#   Seperate ImageQueue's for each subfolder
#       - with chances of being selected representative of no of elements
#
#   Compatibility
#       - Make mac compatible
#       - Make xmonad compatible
#       - Make kde compatible
#
#   Installation
#       - Create .dmg thingie for mac
#       - Create yum and apt packages
#       - Create installer for windows
#
# IDEAS, to be done after release:
#   - Make each split occupy a seperate folder
#   - Multiple instances of the thread running at once? With seperate configurations from config.py
#       * Option to only create image, don't set as wallpaper
#
# Optimization
#   - Multiple threads for resize and make_split functions so that it can be done on multiple cores?
#     Try to lower cpu usage, even though it's running for a while
#   - Use OpenGL or similar to create images, might save A LOT of time. However might be harder to implement.
#     Although a 3d image collage might be cool
#
# Possible installation problems
#   - MAC
#       Was fixed with installing osx version specific pygames installation
#
import os
import sys
import threading
import time
import pygame

from docopt import docopt
from config import Config, get_doc
from compatibility import get_screen_resolution, set_wallpaper
from images import ImageQueue
from wallpaper import wallpaper_split

class Application(threading.Thread):
    def __init__(self, config):
        self.config = config
        self.wallpapers = ImageQueue(self)
        self.resolution = (0,0)
        self._stop = False
        self._no_file_check_interval = self.config['file_check_interval']

    # Use only one update period, for now
    def run(self, single_run=False, sleep_after=False):
        while not self._stop:
            # Check files
            if self._no_file_check_interval == self.config['file_check_interval']:
                self.wallpapers.walk_path()
                self._no_file_check_interval = 0
            else:
                self._no_file_check_interval += 1

            if self.wallpapers.count():
                self.resolution = self._get_resolution()

                # Create wallpaper
                wp_name = self._make_wallpaper(self.resolution)
                self.wallpapers.shuffle_check()
                # Change wallpaper
                self._set_wallpaper(wp_name)
            else:
                raise ValueError('No wallpapers found')

            if self.config['single_run'] or single_run:
                if self.config['verbose'] and not single_run:
                    print 'single run, now exiting'
                elif self.config['verbose'] and sleep_after:
                    print 'sleep %ds' % self.config['update_period']

                try:
                    return os.EX_OK # Exit without errors
                except AttributeError:
                    return 0

            if self.config['verbose']:
                print 'sleep %ds' % self.config['update_period']
            try:
                time.sleep(self.config['update_period'])
            except KeyboardInterrupt:
                try:
                    return os.EX_OK
                except AttributeError:
                    return 0 # On windows just exit, windwos doesnt care about results

    def stop(self):
        self._stop = True

    def stopped(self):
        return self._stop

    # 'private' wallpaper manipulation functions
    def _make_wallpaper(self, size):
        """ Creates a wallpaper and saves it """
        img = wallpaper_split(size,
                              self.wallpapers.pop_image,
                              recursion_depth=self.config['recursion_depth'] - 1)

        wp_name = self.config['generated_wallpaper']

        pygame.image.save(img, wp_name)

        if '\\' in wp_name:
            return wp_name.replace('/', '\\')
        else:
            return wp_name

    def _set_wallpaper(self, wp_name):
        """ Sets the wallpaper to latest generated wallpaper """
        set_wallpaper(wp_name, self.config['desktop_environment'])

    def _get_resolution(self):
        resolution = self.resolution
        if self.config['resolution']:
            resolution = self.config['resolution']
        else:
            resolution = get_screen_resolution()
            if not resolution == self.resolution and self.config['verbose']:
                print 'resolution changed to %sx%s' % (resolution[0], resolution[1])

        if max(*resolution) < 1:
            raise ValueError('Resolution incorrect: %sx%s' % (resolution[0], resolution[1]))

        return resolution

if __name__ == '__main__':
    __doc__ = get_doc()

    # get input options and arguments
    ioptions, iarguments = docopt(__doc__)
    # parse options
    cfg = Config(ioptions)

    app = Application(cfg)
    sys.exit(app.run())

