# Don't rescale textures to power-of-two size
textures-power-2 none

# Center the window
win-origin -2 -2
win-size 1280 800
window-title Hobot's Ascent
icon-filename $MAIN_DIR/assets/icon.ico

# sRGB
framebuffer-srgb true

# Find assets
model-path $MAIN_DIR/assets

# We don't need culling
view-frustum-cull false

# Smoother animations
interpolate-frames false

# FPS meter
show-frame-rate-meter false

#notify-level-chan info
#notify-level-char info

restore-initial-pose false


client-sleep 0.001
