# Rigging research and production decision

## Decision
The previous image-warp preview is not acceptable for production. The production path must use character rigs: layered character parts, fixed pivots, bones, deformers, weights, and animation tests before rendering full episodes.

## Research summary
- Spine uses meshes and weights so image vertices follow bones. This is the right principle for limbs, horns, tails, and soft plush deformation.
- Live2D Cubism uses ArtMeshes per PSD layer and deformers. Rotation deformers are for fixed pivots; warp deformers are for soft shape changes.
- Rive supports bones, constraints, timeline keys, and motion paths for interactive 2D animation. It is useful as a reference for lightweight runtime animation, but for a plush series we still need modeled parts and pivots first.

## Sources checked
- Spine official user guide, weights: https://en.esotericsoftware.com/spine-weights
- Spine official features overview: https://en.esotericsoftware.com/
- Live2D Cubism official deformer manual: https://docs.live2d.com/en/cubism-editor-manual/deformer/
- Live2D Cubism official deformer tutorial: https://docs.live2d.com/4.2/en/cubism-editor-tutorials/figure/
- Rive feature overview: https://rive.app/features
- Rive 101 bones overview: https://rive101.com/en/lesson/5-2/

## Required Mochi rig
- root
- body
- belly_star
- head
- horn_left
- horn_right
- arm_left_upper
- arm_left_lower
- arm_right_upper
- arm_right_lower
- leg_left
- leg_right
- eye_left
- eye_right
- brow_left
- brow_right
- mouth
- cheek_left
- cheek_right

## Required Zumu rig
- root
- body
- cheek_left
- cheek_right
- eye_left
- eye_right
- mouth
- star_mark
- stub_arm_left
- stub_arm_right
- tail_01
- tail_02
- tail_03
- tail_sparkles

## Rule for every shot
- No character movement can be created by animating a circular crop of a rendered image.
- Camera motion is secondary. Character life must come from bones, pivots, squash, face shapes, and secondary motion.
- Every shot needs a rig pass before a beauty/render pass.
- Temporary robot voices are banned. Until professional voices are available, validation videos stay silent with subtitles or use approved scratch voices only.

## Episode 001 rig blocking goals
- Mochi breathing: body scale from pelvis/chest, belly star pulsing separately.
- Mochi looking: head rotation, eye target, brow angle, mouth shape.
- Mochi reaching: shoulder, elbow, wrist/hand positions driven by separate bones.
- Mochi walking: left/right leg counter-motion, body bob, horns delayed after head.
- Zumu flying: body bob, tail chain delay, comet sparkles trailing.
- Emotional beat: body drops, head tilts down, brows sad, mouth sad, belly star dims.
