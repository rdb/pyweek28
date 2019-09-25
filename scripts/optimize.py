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


def optimize_geom(gnode, gi):
    state = gnode.get_geom_state(gi)

    tex_attrib = state.get_attrib(core.TextureAttrib)
    if not tex_attrib or tex_attrib.get_num_on_stages() == 0:
        # Nothing to optimize.
        return False

    changed = False

    stage = tex_attrib.get_on_stage(0)
    tex = tex_attrib.get_on_texture(stage)
    if tex.wrap_u == core.SamplerState.WM_repeat:
        tex.wrap_u = core.SamplerState.WM_clamp
        changed = True
    if tex.wrap_v == core.SamplerState.WM_repeat:
        tex.wrap_v = core.SamplerState.WM_clamp
        changed = True

    if changed:
        print(f"{tex.name}: wrap mode changed to clamp")

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
        print(f"{tex.name}: premultiplying alpha")
        img.premultiply_alpha()
        prev_format = tex.format
        prev_sampler = core.SamplerState(tex.default_sampler)
        tex.load(img)
        tex.default_sampler = prev_sampler
        tex.format = prev_format
        state = state.set_attrib(core.TransparencyAttrib.make(core.TransparencyAttrib.M_premultiplied_alpha))
        gnode.set_geom_state(gi, state)
        changed = True

    # Make sure that the crop region is power-of-two, because why not.
    crop_w = crop_r - crop_l
    pad_x = core.Texture.up_to_power_2(crop_w) - crop_w
    pad_l = pad_x // 2
    pad_r = pad_x - pad_l
    crop_l -= pad_l
    crop_r += pad_r
    if crop_l < 0:
        crop_r += -crop_l
        crop_l = 0
    crop_w = crop_r - crop_l
    assert core.Texture.up_to_power_2(crop_w) == crop_w

    crop_h = crop_b - crop_t
    pad_y = core.Texture.up_to_power_2(crop_h) - crop_h
    pad_t = pad_y // 2
    pad_b = pad_y - pad_t
    crop_t -= pad_t
    crop_b += pad_b
    crop_h = crop_b - crop_t
    if crop_t < 0:
        crop_b += -crop_t
        crop_t = 0
    assert core.Texture.up_to_power_2(crop_h) == crop_h

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
    prev_format = tex.format
    prev_sampler = core.SamplerState(tex.default_sampler)
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

    # Transform the UVs.
    uv_pos = core.Vec2(crop_l / (width - 1.0), (height - crop_b) / (height - 1.0))
    uv_scale = core.Vec2((width - 1.0) / (crop_w - 1.0), (height - 1.0) / (crop_h - 1.0))

    rewriter = core.GeomVertexRewriter(gnode.modify_geom(gi).modify_vertex_data(), stage.get_texcoord_name())
    while not rewriter.is_at_end():
        uv = core.Point2(rewriter.get_data2())
        uv -= uv_pos
        uv.componentwise_mult(uv_scale)
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
