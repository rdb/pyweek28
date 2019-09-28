from panda3d import core


def is_image_fully_opaque(img):
    if not img.has_alpha():
        return True

    histogram = core.PNMImageHeader.Histogram()
    img.make_histogram(histogram)

    for pixel in histogram.get_pixels():
        if pixel.get_alpha() < 252:
            return False

    return True


def is_image_alpha_binary(img):
    if not img.has_alpha():
        return True

    histogram = core.PNMImageHeader.Histogram()
    img.make_histogram(histogram)

    for pixel in histogram.get_pixels():
        if pixel.get_alpha() > 2 and pixel.get_alpha() < 252:
            return False

    return True


def optimize_geom(gnode, gi):
    state = gnode.get_geom_state(gi)

    changed = False

    if gnode.get_geom(gi).bounds_type != core.BoundingVolume.BT_box:
        gnode.modify_geom(gi).bounds_type = core.BoundingVolume.BT_box
        changed = True

    tex_attrib = state.get_attrib(core.TextureAttrib)
    if not tex_attrib or tex_attrib.get_num_on_stages() == 0:
        # Nothing to optimize.
        return changed

    stage = tex_attrib.get_on_stage(0)
    tex = tex_attrib.get_on_texture(stage)
    if tex.wrap_u == core.SamplerState.WM_repeat:
        tex.wrap_u = core.SamplerState.WM_clamp
        changed = True
    if tex.wrap_v == core.SamplerState.WM_repeat:
        tex.wrap_v = core.SamplerState.WM_clamp
        changed = True

    img = core.PNMImage()
    img.set_color_space(core.CS_sRGB)
    tex.store(img)

    # Does the image have alpha?
    transp = state.get_attrib(core.TransparencyAttrib)
    if not img.has_alpha():
        if transp and transp.mode != core.TransparencyAttrib.M_off:
            print(f"{tex.name}: turning off TransparencyAttrib")
            state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_off))
            gnode.set_geom_state(gi, state)
            return True
        else:
            # Nothing else to do.
            return changed

    # Crop the image.
    width, height = img.size
    crop_l = 0
    for x in range(width):
        if any(img.get_alpha_val(x, y) > 0 for y in range(height)):
            crop_l = x
            break

    crop_r = width
    for x in reversed(range(crop_l, width)):
        if any(img.get_alpha_val(x, y) > 0 for y in range(height)):
            crop_r = x + 1
            break

    crop_t = 0
    for y in range(height):
        if any(img.get_alpha_val(x, y) > 0 for x in range(crop_l, crop_r)):
            crop_t = y
            break

    crop_b = height
    for y in reversed(range(crop_t, height)):
        if any(img.get_alpha_val(x, y) > 0 for x in range(crop_l, crop_r)):
            crop_b = y + 1
            break

    # No cropping to be done.  Is the image fully opaque, perhaps?
    if crop_l == 0 and crop_r == width and crop_t == 0 and crop_b == height:
        if is_image_fully_opaque(img):
            print(f"{tex.name}: fully opaque, removing alpha channel")
            img.remove_alpha()
            tex.load(img)
            tex.format = core.Texture.F_srgb
            tex.wrap_u = core.SamplerState.WM_clamp
            tex.wrap_v = core.SamplerState.WM_clamp
            tex.wrap_w = core.SamplerState.WM_clamp

            if transp and transp.mode != core.TransparencyAttrib.M_off:
                state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_off))
                gnode.set_geom_state(gi, state)
            return True

    # Premultiply alpha for higher-quality blending.
    transp = state.get_attrib(core.TransparencyAttrib)
    if transp and transp.mode == core.TransparencyAttrib.M_alpha:
        img.premultiply_alpha()
        prev_format = tex.format
        prev_sampler = core.SamplerState(tex.default_sampler)
        tex.load(img)
        tex.default_sampler = prev_sampler
        tex.format = prev_format

        # Check if this has binary alpha.
        if is_image_alpha_binary(img):
            print(f"{tex.name}: premultiplying alpha and setting to binary")
            state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_binary))
        else:
            print(f"{tex.name}: premultiplying alpha and setting to dual")
            #XXX there is no M_premultiplied_dual; this will have to suffice.
            state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_dual))

        gnode.set_geom_state(gi, state)
        changed = True

    # Make sure that the crop region is power-of-two, because why not.
    crop_w = crop_r - crop_l
    #pad_x = core.Texture.up_to_power_2(crop_w) - crop_w
    #pad_l = pad_x // 2
    #pad_r = pad_x - pad_l
    #crop_l -= pad_l
    #crop_r += pad_r
    #if crop_l < 0:
    #    crop_r += -crop_l
    #    crop_l = 0
    #crop_w = crop_r - crop_l
    #assert core.Texture.up_to_power_2(crop_w) == crop_w

    crop_h = crop_b - crop_t
    #pad_y = core.Texture.up_to_power_2(crop_h) - crop_h
    #pad_t = pad_y // 2
    #pad_b = pad_y - pad_t
    #crop_t -= pad_t
    #crop_b += pad_b
    #crop_h = crop_b - crop_t
    #if crop_t < 0:
    #    crop_b += -crop_t
    #    crop_t = 0
    #assert core.Texture.up_to_power_2(crop_h) == crop_h

    # Make sure the cropped region isn't bigger than the original image.
    if crop_w * crop_h >= width * height:
        print(f"{tex.name}: no need to crop, {width}×{height} is already its optimal size")
        return changed

    print(f"{tex.name}: cropping to a {crop_w}×{crop_h} region starting at {crop_l}×{crop_t}")

    new_img = core.PNMImage(crop_w, crop_h, img.num_channels, img.maxval, color_space=core.CS_sRGB)
    new_img.fill(0, 0, 0)
    if new_img.has_alpha():
        new_img.alpha_fill(0)
    new_img.copy_sub_image(img, 0, 0, crop_l, crop_t, crop_w, crop_h)

    prev_sampler = core.SamplerState(tex.default_sampler)

    if is_image_fully_opaque(new_img):
        print(f"{tex.name}: fully opaque after crop, removing alpha channel")
        new_img.remove_alpha()
        tex.load(new_img)
        tex.format = core.Texture.F_srgb
    else:
        prev_format = tex.format
        tex.load(new_img)
        tex.format = prev_format

    tex.default_sampler = prev_sampler

    if crop_w < width:
        tex.wrap_u = core.SamplerState.WM_border_color
    elif tex.wrap_u == core.SamplerState.WM_repeat:
        tex.wrap_u = core.SamplerState.WM_clamp

    if crop_h < height:
        tex.wrap_v = core.SamplerState.WM_border_color
    elif tex.wrap_v == core.SamplerState.WM_repeat:
        tex.wrap_v = core.SamplerState.WM_clamp

    tex.border_color = (0, 0, 0, 0)

    assert tex.x_size == crop_w
    assert tex.y_size == crop_h

    # Now we need to either move the vertices or transform the UVs in order to
    # compensate for the cropped image.
    uv_pos = core.Vec2(crop_l / (width - 1.0), (height - crop_b) / (height - 1.0))
    uv_scale = core.Vec2((crop_w - 1.0) / (width - 1.0), (crop_h - 1.0) / (height - 1.0))

    vertex_data = gnode.modify_geom(gi).modify_vertex_data()

    uv_to_vtx = {}
    vtx_reader = core.GeomVertexReader(vertex_data, 'vertex')
    uv_reader = core.GeomVertexReader(vertex_data, stage.texcoord_name)
    while not vtx_reader.is_at_end() and not uv_reader.is_at_end():
        uv = uv_reader.get_data2()
        vtx = core.LPoint3(vtx_reader.get_data3())
        uv_to_vtx[tuple(uv)] = vtx
    vtx_reader = None
    uv_reader = None

    if (0, 0) in uv_to_vtx and (1, 1) in uv_to_vtx:
        # Crop the card itself, making it smaller, reducing overdraw.
        card_pos = uv_to_vtx[(0, 0)]
        card_size = uv_to_vtx[(1, 1)] - uv_to_vtx[(0, 0)]

        rewriter = core.GeomVertexRewriter(vertex_data, 'vertex')
        uv_reader = core.GeomVertexReader(vertex_data, stage.texcoord_name)
        while not rewriter.is_at_end() and not uv_reader.is_at_end():
            vtx = rewriter.get_data3()
            uv = core.Point2(uv_reader.get_data2())
            uv.componentwise_mult(uv_scale)
            uv += uv_pos
            rewriter.set_data3(uv[0] * card_size[0] + card_pos[0], uv[1] * card_size[1] + card_pos[1], vtx.z)
        rewriter = None

        # We can remove transparency if we cropped it to the opaque part.
        if tex.format == core.Texture.F_srgb:
            print("Removing transparency")
            state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_off))
            gnode.set_geom_state(gi, state)
    else:
        # Transform the UVs.
        rewriter = core.GeomVertexRewriter(gnode.modify_geom(gi).modify_vertex_data(), stage.get_texcoord_name())
        while not rewriter.is_at_end():
            uv = core.Point2(rewriter.get_data2())
            uv -= uv_pos
            uv.x /= uv_scale.x
            uv.y /= uv_scale.y
            rewriter.set_data2(uv)
        rewriter = None

    return True


def analyze_node(node):
    sga = core.SceneGraphAnalyzer()
    sga.add_node(node)
    sga.write(core.Notify.out())


def optimize_bam(path):
    path = core.Filename.from_os_specific(path)
    loader = core.Loader.get_global_ptr()
    node = loader.load_sync(path)
    model = core.NodePath(node)

    print("Before:")
    analyze_node(node)

    any_changed = False

    for child in model.find_all_matches('**/+GeomNode'):
        gnode = child.node()
        for i in range(gnode.get_num_geoms()):
            if optimize_geom(gnode, i):
                any_changed = True

    for tex in model.find_all_textures():
        if tex.name and not tex.filename:
            rel_path = 'layers/' + tex.name + '.png'
            dir = core.Filename(path.get_dirname())
            fn = core.Filename(dir, rel_path)
            if tex.write(fn):
                print(f"{tex.name}: wrote to {fn}")
                tex.filename = 'assets/' + dir.get_basename() + '/' + rel_path
                tex.fullpath = fn
            any_changed = True

    if any_changed:
        model.write_bam_file(path)

        print("After:")
        analyze_node(node)
    else:
        print("File is already optimized, no changes needed.")


if __name__ == '__main__':
    import sys
    import os

    paths = sys.argv[1:]
    for path in paths:
        optimize_bam(os.path.abspath(path))
