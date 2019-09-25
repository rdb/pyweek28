from direct.showbase.ShowBase import ShowBase
from panda3d import core

core.load_prc_file_data("", "framebuffer-srgb true")


def view_bam(path):
    path = core.Filename.from_os_specific(path)
    loader = core.Loader.get_global_ptr()
    node = loader.load_sync(path)

    lens = core.OrthographicLens()
    lens.film_size = (1, 1)
    lens.set_view_vector((0, 0, -1), (0, 1, 0))
    lens.set_near_far(-100, 100)

    base = ShowBase()
    base.render.attach_new_node(node)

    base.disable_mouse()
    base.cam.node().set_lens(lens)
    base.camLens = lens

    base.run()


if __name__ == '__main__':
    import sys
    import os

    paths = sys.argv[1:]
    for path in paths:
        view_bam(os.path.abspath(path))
