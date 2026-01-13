# window.py
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

from collections import OrderedDict
from gi.repository import Adw
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from hashlib import sha1
from io import BytesIO
from math import copysign
from math import exp
from pathlib import Path
from pathlib import PosixPath
from PIL import Image
from PIL import ImageOps
from threading import Thread
from typing import Any

@Gtk.Template(resource_path = '/com/macipra/alusin/window.ui')
class Window(Adw.ApplicationWindow):
    __gtype_name__ = 'Window'

    main_canvas = Gtk.Template.Child()
    v_scrollbar = Gtk.Template.Child()

    THUMB_DIRPATH = '~/.cache/alusin-studio/'
    # Or '~/.var/app/com.macipra.alusin/cache/alusin/'

    THUMB_BUCKETS = (256, 512, 1024)
    THUMB_IFORMAT = 'JPEG'
    THUMB_QUALITY = 85

    GALLERY_PATH = '/home/naruaika/Pictures/unsplash.com'
    # Or '/home/naruaika/Repositories/sample-images/docs'
    # from https://github.com/yavuzceliker/sample-images

    def __init__(self, **kwargs) -> None:
        """"""
        super().__init__(**kwargs)

        self._image_paths = []
        self._image_sizes = []
        self._image_bytes = OrderedDict()

        self._toload_indices = []
        self._max_cache_size = -1

        self._inertia_tick_id = 0

        self._setup_data()
        self._setup_controllers()

    @property
    def image_paths(self) -> list[str]:
        """"""
        return self._image_paths

    @property
    def image_sizes(self) -> list[tuple[int, int]]:
        """"""
        return self._image_sizes

    def get_image_byte(self,
                       index: int,
                       ) ->   Any:
        """"""
        texture = self._image_bytes.get(index)
        if texture:
            self._image_bytes.move_to_end(index)
        return texture

    def set_image_byte(self,
                       index:   int,
                       texture: Gdk.MemoryTexture,
                       ) ->     Any:
        """"""
        self._image_bytes[index] = texture
        self._image_bytes.move_to_end(index)

        cache_size = len(self._image_bytes)
        if self._max_cache_size < cache_size:
            n_difference = cache_size - self._max_cache_size
            for _ in range(n_difference):
                _, texture = self._image_bytes.popitem(last = False)
                del texture

    @property
    def toload_indices(self) -> list[int]:
        """"""
        return self._toload_indices

    @property
    def max_cache_size(self) -> int:
        """"""
        return self._max_cache_size

    @max_cache_size.setter
    def max_cache_size(self,
                       size: int,
                       ) ->  None:
        """"""
        self._max_cache_size = max(self._max_cache_size, size, 256)

    def _setup_data(self) -> None:
        """"""
        file = Gio.File.new_for_path(self.GALLERY_PATH)
        enumerator = file.enumerate_children('standard::*', Gio.FileQueryInfoFlags.NONE)

        # TODO: do not process all images at once

        for info in enumerator:
            content_type = info.get_content_type()
            if not content_type.startswith('image'):
                continue

            file_path = Path(self.GALLERY_PATH, info.get_name())
            self._image_paths.append(str(file_path))

            with Image.open(file_path) as image:
                self._image_sizes.append((image.width, image.height))

    def _setup_controllers(self) -> None:
        """"""
        controller = Gtk.EventControllerMotion()
        controller.connect('enter', self._on_scrollbar_entered)
        controller.connect('leave', self._on_scrollbar_left)
        self.v_scrollbar.add_controller(controller)

        adjustment = Gtk.Adjustment.new(0, 0, 1, 3, 20, 0)
        adjustment.connect('value-changed', self._on_scrollbar_changed)
        self.v_scrollbar.set_adjustment(adjustment)

        controller = Gtk.EventControllerScroll()
        controller.set_flags(Gtk.EventControllerScrollFlags.VERTICAL |
                             Gtk.EventControllerScrollFlags.KINETIC)
        controller.connect('scroll', self._on_canvas_scrolled)
        controller.connect('decelerate', self._on_canvas_decelerated)
        self.main_canvas.add_controller(controller)

        # TODO: when resizing the window and the scrollbar hits the bottom,
        # maybe we want to keep it stick to the bottom when the window size
        # goes smaller. Or even keep the scrollbar position relative to the
        # logical masonry row whenever possible.

    def _on_scrollbar_entered(self,
                              motion: Gtk.EventControllerMotion,
                              x:      float,
                              y:      float,
                              ) ->    None:
        """"""
        scrollbar = motion.get_widget()
        scrollbar.add_css_class('hovering')

    def _on_scrollbar_left(self,
                           motion: Gtk.EventControllerMotion,
                           ) ->    None:
        """"""
        scrollbar = motion.get_widget()
        scrollbar.remove_css_class('hovering')

    def _on_scrollbar_changed(self,
                              source: GObject.Object,
                              ) ->    None:
        """"""
        self.main_canvas.queue_draw()

    def _on_canvas_scrolled(self,
                            event: Gtk.EventControllerScroll,
                            dx:    float,
                            dy:    float,
                            ) ->   bool:
        """"""
        dy = int(dy * 20 * 3)

        scroll_unit = event.get_unit()
        if scroll_unit == Gdk.ScrollUnit.SURFACE:
            dy *= 0.05

        v_adjustment = self.v_scrollbar.get_adjustment()

        value = v_adjustment.get_value()
        upper = v_adjustment.get_upper()
        page_size = v_adjustment.get_page_size()

        value = max(0, min(value + dy, upper - page_size))
        v_adjustment.set_value(value)

        if self._inertia_tick_id:
            self.main_canvas.remove_tick_callback(self._inertia_tick_id)
            self._inertia_tick_id = 0

        return Gdk.EVENT_PROPAGATE

    def _on_canvas_decelerated(self,
                               event: Gtk.EventControllerScroll,
                               vel_x: float,
                               vel_y: float,
                               ) ->   None:
        """"""
        vel_y = vel_y / 16.666

        if abs(vel_y) < 50:
            return

        self._inertia_speed = copysign(abs(vel_y) ** 1.02, vel_y)
        self._last_frame_time = 0

        self._inertia_tick_id = self.main_canvas.add_tick_callback(self._on_inertia_tick)

    def _on_inertia_tick(self,
                         widget:      Gtk.Widget,
                         frame_clock: Gdk.FrameClock,
                         ) ->         bool:
        """"""
        v_adjustment = self.v_scrollbar.get_adjustment()

        frame_time = frame_clock.get_frame_time()

        if self._last_frame_time == 0:
            self._last_frame_time = frame_time
            return Gdk.EVENT_STOP

        delta_time = (frame_time - self._last_frame_time) / 1_000
        self._last_frame_time = frame_time

        delta = self._inertia_speed * (delta_time / 16.666)

        value = v_adjustment.get_value() + delta
        lower = 0.0
        upper = v_adjustment.get_upper() - v_adjustment.get_page_size()

        if value < lower or value > upper:
            return self._stop_inertia_tick()

        v_adjustment.set_value(value)

        self._inertia_speed *= exp(-0.0025 * delta_time)

        if abs(self._inertia_speed) < 0.1:
            return self._stop_inertia_tick()

        return Gdk.EVENT_STOP

    def _stop_inertia_tick(self) -> None:
        """"""
        self._inertia_speed = 0.0
        self._inertia_tick_id = 0
        return Gdk.EVENT_PROPAGATE

    def load_images_worker(self,
                           indices: list[int] = [],
                           ) ->     None:
        """"""
        # Get the monitor where the window resides on
        surface = self.get_surface()
        display = self.get_display()
        monitor = display.get_monitor_at_surface(surface)

        # Calculate image thumbnail height
        monitor_height = monitor.get_geometry().height
        thumb_height = self.main_canvas.MAX_ROW_HEIGHT
        thumb_height *= monitor_height
#       thumb_height *= 1.5 # try to avoids upscaling artifacts

        thumb_dir = self._create_thumbnail_directory()

        if indices:
            self._toload_indices += indices

            for index in indices:
                path = self._image_paths[index]
                self._load_image_task(index, thumb_height, thumb_dir, path)

        else:
            self._toload_indices += list(range(len(self._image_paths)))

            for index, path in enumerate(self._image_paths):
                self._load_image_task(index, thumb_height, thumb_dir, path)

    def _load_image_task(self,
                         index:     int,
                         height:    int,
                         thumb_dir: PosixPath,
                         file_path: str,
                         ) ->       None:
        """"""
        thumb_path = self._create_thumbnail_path(thumb_dir, file_path)

        if thumb_path.is_file():
            try:
                mapped = GLib.MappedFile.new(str(thumb_path), writable = False)
                texture = Gdk.Texture.new_from_bytes(mapped.get_bytes())
            except:
                fbytes = self._create_image_thumbnail(height, file_path, thumb_path)
                gbytes = GLib.Bytes.new(fbytes)
                texture = Gdk.Texture.new_from_bytes(gbytes)

        else:
            fbytes = self._create_image_thumbnail(height, file_path, thumb_path)
            gbytes = GLib.Bytes.new(fbytes)
            texture = Gdk.Texture.new_from_bytes(gbytes)

        GLib.idle_add(self._on_image_loaded,
                      index,
                      texture,
                      priority = GLib.PRIORITY_LOW)

    def _create_thumbnail_directory(self) -> PosixPath:
        """"""
        thumb_dir = Path(self.THUMB_DIRPATH, 'thumbnails').expanduser()
        thumb_dir.mkdir(parents = True, exist_ok = True)
        return thumb_dir

    def _create_thumbnail_path(self,
                               thumb_dir: PosixPath,
                               file_path: str,
                               ) ->       PosixPath:
        """"""
        fstat = Path(file_path).stat()
        fkey = f'{file_path}:{fstat.st_mtime_ns}:{fstat.st_size}'
        digest = sha1(fkey.encode('utf-8')).hexdigest()
        return Path(thumb_dir, digest + '.jpeg')

    def _create_image_thumbnail(self,
                                height:      int,
                                source_path: str,
                                target_path: PosixPath,
                                ) ->         bytes:
        """"""
        bucket = self._get_image_bucket(height)
        buffer = BytesIO()

        with Image.open(source_path) as image:
            image = ImageOps.exif_transpose(image)
            image.draft('RGB', (bucket, bucket))

            width, height = image.size
            scale = bucket / max(width, height)
            new_size = (int(width * scale), int(height * scale))

            image = image.resize(new_size, Image.BILINEAR)

            image.save(buffer,
                        format      = self.THUMB_IFORMAT,
                        quality     = self.THUMB_QUALITY,
                        optimize    = False,
                        progressive = False,
                        subsampling = '4:2:0')

            fbytes = buffer.getvalue()

        thread = Thread(target = self._save_image_thumbnail,
                        args   = (fbytes, str(target_path)),
                        daemon = True)
        thread.start()

        return fbytes

    def _get_image_bucket(self,
                          height: int,
                          ) ->    int:
        """"""
        for bucket in self.THUMB_BUCKETS:
            if bucket >= height:
                return bucket
        return self.THUMB_BUCKETS[-1]

    def _save_image_thumbnail(self,
                              data: bytes,
                              path: str,
                              ) ->  None:
        """"""
        with open(path, 'wb') as file:
            file.write(data)

    def _on_image_loaded(self,
                         index:   int,
                         texture: Gdk.MemoryTexture,
                         ) ->     bool:
        """"""
        if index in self._toload_indices:
            self._toload_indices.remove(index)

        self.set_image_byte(index, texture)

        self.main_canvas.queue_draw()

        return GLib.SOURCE_REMOVE
