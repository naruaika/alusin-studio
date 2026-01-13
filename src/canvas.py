# canvas.py
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
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Graphene
from gi.repository import Gsk
from gi.repository import Gtk
from threading import Thread

@Gtk.Template(resource_path = '/com/macipra/alusin/canvas.ui')
class Canvas(Adw.Bin):
    __gtype_name__ = 'Canvas'

    CANVAS_PADDING = 10 # defined in CSS
    BORDER_SPACING = 10

    MIN_ROW_HEIGHT = 2/11
    MAX_ROW_HEIGHT = 1/5

    RADIUS = 10.0
    FCOLOR = Gdk.RGBA(0.5, 0.5, 0.5, 1.0)

    def do_snapshot(self,
                    snapshot: Gtk.Snapshot,
                    ) ->      None:
        """"""
        window = self.get_root()

        CANVAS_WIDTH = self.get_width()
        CANVAS_HEIGHT = self.get_height()

        surface = window.get_surface()
        display = window.get_display()
        monitor = display.get_monitor_at_surface(surface)

        monitor_height = monitor.get_geometry().height
        MIN_ROW_HEIGHT = self.MIN_ROW_HEIGHT * monitor_height
        MAX_ROW_HEIGHT = self.MAX_ROW_HEIGHT * monitor_height

        v_adjustment = window.v_scrollbar.get_adjustment()
        scroll_position = v_adjustment.get_value()

        offset_y = 0

        def do_scroll() -> None:
            """"""
            upper = max(offset_y, CANVAS_HEIGHT)
            v_adjustment.set_page_size(CANVAS_HEIGHT)
            v_adjustment.set_upper(upper)

            if upper < scroll_position + CANVAS_HEIGHT:
                v_adjustment.set_value(upper)

        image_sizes = window.image_sizes

        if not image_sizes:
            GLib.idle_add(do_scroll)
            return

        i = 0
        j = 0

        bounds = Graphene.Rect()
        roundr = Gsk.RoundedRect()

        toload_indices = []

        while i < len(image_sizes):
            row_width = 0
            row_sizes = []

            # Append image to row until it fulls
            for k in range(i, len(image_sizes)):
                row_sizes.append(image_sizes[k])
                i += 1

                width, height = image_sizes[k]
                scaled_width = width * (MAX_ROW_HEIGHT / height)

                if row_sizes:
                    row_width += self.BORDER_SPACING
                row_width += scaled_width

                if row_sizes and CANVAS_WIDTH < row_width:
                    break

            # Calculate the row height to make the row fits the canvas width
            total_spacing = self.BORDER_SPACING * (len(row_sizes) - 1)
            total_width = sum(w * (MAX_ROW_HEIGHT / h) for w, h in row_sizes)
            scale = (CANVAS_WIDTH - total_spacing) / total_width
            row_height = MAX_ROW_HEIGHT * scale

            # Make sure that the row height isn't too low
            if 1 < len(row_sizes) and row_height < MIN_ROW_HEIGHT:
                row_sizes.pop()
                i -= 1

                # Recalculate the row height after removing the last image in row
                total_spacing = self.BORDER_SPACING * (len(row_sizes) - 1)
                total_width = sum(w * (MAX_ROW_HEIGHT / h) for w, h in row_sizes)
                scale = (CANVAS_WIDTH - total_spacing) / total_width
                row_height = MAX_ROW_HEIGHT * scale

            # Prevent the last row from being stretched except when
            # the difference can be compensated for a better visual
            if self.BORDER_SPACING < CANVAS_WIDTH - row_width:
                row_height = max(MIN_ROW_HEIGHT, min(MAX_ROW_HEIGHT, row_height))

            offset_x = 0

            if offset_y:
                offset_y += self.BORDER_SPACING

            for k, (width, height) in enumerate(row_sizes):
                scaled_width = (width / height) * row_height

                # Display image content or placeholder when it's visible in the view
                if (
                    scroll_position < offset_y + row_height + self.CANVAS_PADDING and
                    offset_y - self.CANVAS_PADDING < scroll_position + CANVAS_HEIGHT
                ):
                    bounds.init(offset_x, offset_y - scroll_position, scaled_width, row_height)
                    roundr.init_from_rect(bounds, self.RADIUS)

                    snapshot.push_rounded_clip(roundr)

                    # TODO: handle very wide image aspect ratio

                    if texture := window.get_image_byte(j):
                        snapshot.append_texture(texture, bounds)
                    else:
                        snapshot.append_color(self.FCOLOR, bounds)

                        # Add to the image loading queue
                        if j not in window.toload_indices:
                            toload_indices.append(j)

                    snapshot.pop()

                j += 1
                offset_x += scaled_width + self.BORDER_SPACING

            offset_y += row_height

        if toload_indices:
            window.max_cache_size = len(toload_indices) * 5

            # Request image contents loading
            thread = Thread(target = window.load_images_worker,
                            args   = [toload_indices],
                            daemon = True)
            thread.start()

        GLib.idle_add(do_scroll)
