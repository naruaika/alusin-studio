# main.py
#
# Copyright 2026 Naufan Rusyda Faikar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk
import sys

from .window import Window

class Application(Adw.Application):
    """The main application singleton class."""

    def __init__(self) -> None:
        """"""
        super().__init__(application_id     = 'com.macipra.alusin',
                         flags              = Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path = '/com/macipra/alusin')

        self.create_action('quit',  lambda *_: self.quit(),
                                    ['<Primary>q'])
        self.create_action('about', self._on_about_action,
                                    ['F12'])

    def do_activate(self) -> None:
        """"""
        window = self.props.active_window

        if not window:
            window = Window(application=self)

        window.present()

    def _on_about_action(self,
                         action:    Gio.SimpleAction,
                         parameter: GLib.Variant,
                         ) ->       None:
        """"""
        about = Adw.AboutDialog(application_name   = 'Alusin Studio',
                                application_icon   = 'com.macipra.alusin',
                                version            = '0.1.0',
                                copyright          = '© 2025 Naufan Rusyda Faikar',
                                license_type       = Gtk.License.AGPL_3_0,
                                designers          = ['Naufan Rusyda Faikar'],
                                developer_name     = 'Naufan Rusyda Faikar',
                                developers         = ['Naufan Rusyda Faikar'],
                                translator_credits = _('translator-credits'))
        window = self.props.active_window
        about.present(window)

    def create_action(self,
                      name:      str,
                      callback:  callable  = None,
                      shortcuts: list[str] = None,
                      ) ->       None:
        """"""
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)

        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

def main(version) -> None:
    """The application's entry point."""
    return Application().run(sys.argv)
