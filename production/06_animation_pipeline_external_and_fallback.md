# Animation pipeline after rig test failure

## What failed
The circular-crop animation and the geometric blocking test are not acceptable as final production. A real production path must either:
- build a proper layered 2D/3D rig, or
- produce many high-quality key images and animate them with light/camera/AI video tools shot by shot.

## Research-backed options

### Option A - Proper 2D rig
Use Live2D or Spine.
- Prepare PSD layers: head, body, horns, arms, legs, eyes, brows, mouth, cheeks, belly star, Zumu tail pieces.
- Bind layers/meshes to bones and weights.
- Test maximum poses before beauty animation.
- Export short clips per shot.

Why: Spine official docs describe weights as binding attachment vertices to bones, so vertices follow bone transforms. Live2D uses ArtMeshes and deformers for this same production idea.

### Option B - 3D plush rig
Use Blender or a studio tool.
- Model Mochi and Zumu as plush 3D characters.
- Add armature, skin weights, shape keys for face/mouth.
- Render with soft fur/plush materials and Korean convenience-store sets.

Why: this is the closest to Octonauts-style quality, but it requires actual modeling work, not just HTML animation.

### Option C - High-quality image sequence + AI video
Use Runway Gen-4, Kling, Luma, or similar image-to-video tools shot by shot.
- Generate 8-14 key images per 3-minute episode.
- For each shot, provide start image, optional end image, character reference, and exact motion prompt.
- Use only short clips, then edit together.
- Keep voices separate until casting is approved.

Why: Runway Gen-4 officially emphasizes consistent characters, objects, locations and visual references across scenes. Luma presents production workflows around storyboards, clips and deliverables. Kling should be tested in-account because public crawling is restricted, but it remains a candidate for image-to-video generation.

### Option C1 - ElevenLabs Image & Video package
The user's ElevenLabs account has access to Image & Video. The UI shows Google Veo 3.1 Fast in video mode with:
- start image
- end image
- image references
- 16:9
- 720p
- 4s
- sound toggle
- credit count visible before generation

Official ElevenLabs documentation confirms Image & Video can create videos from prompts and reference images, supports start frames for video, supports MP4 export, and shows cost before generating. It lists Google Veo 3.1 / Veo 3.1 Fast as supporting start frames, end frames, fixed durations and negative prompts.

Source: https://elevenlabs.io/docs/eleven-creative/playground/image-video

Prepared local package:
- `exports/elevenlabs_ep001_image_video/PROMPTS.md`
- `exports/elevenlabs_ep001_image_video/01_convenience_store_establishing.png`
- `exports/elevenlabs_ep001_image_video/02_door_incident.png`
- `exports/elevenlabs_ep001_image_video/03_zumu_attempt.png`
- `exports/elevenlabs_ep001_image_video/04_emotional_pause.png`
- `exports/elevenlabs_ep001_image_video/05_resolution.png`
- `exports/elevenlabs_ep001_image_video/character_reference_mochi.png`
- `exports/elevenlabs_ep001_image_video/character_reference_zumu.png`

Automation status:
- Chrome can open the user's logged-in ElevenLabs workspace.
- The generator can be switched to Video mode.
- Automatic file upload through the Chrome extension timed out on the hidden file inputs. If this persists, the user must manually drop the prepared start image into the "Image de départ" slot, while Codex can continue preparing prompts/settings and assembling exported MP4 clips.

## Immediate project rule
Until a proper rig exists, the acceptable preview is:
- high-quality stills,
- camera/light/particle motion only,
- no fake limb animation from circular crops,
- no robot voices,
- clear label: "image-sequence animatic, not final rigged animation."

## Episode 001 image-sequence fallback
Minimum key images:
1. Night convenience store establishing.
2. Mochi notices trapped starlight.
3. Zumu rushes in.
4. Automatic door sensor reacts.
5. Mochi attempts to help and slips.
6. Starlight hides in reflection.
7. Mochi stops and breathes.
8. Emotional close-up.
9. Zumu dims tail to help.
10. Mochi waits with open palm.
11. Starlight moves out by itself.
12. Sign gains a new small star.
13. Ending smile.

## External prompt template
Use the same character reference images for every shot.

Prompt:
Korean children's animated series, 3D soft plush render, Octonauts-like gentle quality, Mochi white plush moon creature with crescent horns, glowing belly star, brown-orange eyes, rosy cheeks; Zumu blue plush comet creature with orange eyes and glowing comet tail; Korean night convenience store, wet street reflections, warm neon, no real brand logos. Animate only the described action. Preserve character identity, proportions, face, plush texture and lighting. No morphing, no extra limbs, no adult human characters, no text artifacts.

Shot action:
<specific 5-8 second action>

Camera:
<locked / slow push / close-up>

Avoid:
warped face, floating limbs, disconnected legs, rubber body, logo text, unreadable Korean text, scary mood, realistic humans.
