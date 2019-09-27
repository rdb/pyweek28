# Don't rescale textures to power-of-two size
textures-power-2 none

# Center the window
win-origin -2 -2

# sRGB
framebuffer-srgb true

# Find assets
model-path $MAIN_DIR/assets

# We don't need culling
view-frustum-cull false

# Smoother animations
interpolate-frames true


show-frame-rate-meter true

#notify-level-chan info
#notify-level-char info

restore-initial-pose false


client-sleep 0.001
