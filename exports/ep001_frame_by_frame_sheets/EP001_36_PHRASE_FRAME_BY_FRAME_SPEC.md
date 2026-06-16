# EP001 - 36 phrase frame-by-frame production spec

Correct target:

- 3 minutes total.
- 36 spoken phrases.
- 1 different camera plan per phrase.
- 10 progressive poses per phrase.
- 360 generated/drawn poses before interpolation.
- 1800 final frames at 10fps.
- No text burned into any source sheet, pose, or frame. Dialogue/subtitles are added only as a final animated overlay layer after the visual animation is approved.

This is the required production model. The previous 5-scene and 18-scene structures are not enough.

## Phrase plans

1. Mochi notices the store from the rainy street. 10 poses: far look -> step -> chest glow -> curious face. Korea refs: wet residential alley, 24시 convenience-store sign, umbrella stand, streetlamp reflections.
2. Zumu points at the hidden star on the sign. 10 poses: Zumu enters frame -> looks up -> excited bounce. Korea refs: glowing store fascia inspired by Korean 편의점, small hanging 24시 sign, apartment windows in background.
3. Mochi smells rain and warm milk. 10 poses: sniff -> soft smile -> tiny lights appear. Korea refs: banana milk bottles, warm drink shelf, glass door condensation, floor mat at entrance.
4. Zumu promises to dim his tail. 10 poses: tail bright -> tail dims -> Zumu gestures carefully. Korea refs: automatic sliding glass doors, T-money/card payment sticker near entrance, rainy sidewalk.
5. Mochi sees sparkle above the door. 10 poses: glance -> head tilt -> paw points upward. Korea refs: automatic door sensor, CCTV notice sticker, recycle etiquette sticker, umbrella drops on glass.
6. Zumu inspects the sensor. 10 poses: float up -> circle sensor -> star dust reacts. Korea refs: door sensor unit, convenience-store security camera, warm fluorescent ceiling lights.
7. Mochi asks the door not to scare them. 10 poses: step closer -> gentle paw -> worried eyes. Korea refs: floor entrance mat, wet shoe prints, row of triangle kimbap visible through glass.
8. Zumu goes first. 10 poses: reassuring smile -> small flight -> look back at Mochi. Korea refs: sliding door rail, poster for 따뜻한 라면 without readable copy, night bus stop blur outside.
9. Mochi reacts as stars escape toward ramyeon. 10 poses: surprise -> body turn -> small run start. Korea refs: cup ramyeon aisle, triangle kimbap warmer, banana milk fridge.
10. Zumu leads the chase carefully. 10 poses: point -> fly low -> avoid shelves. Korea refs: snack shelf, honey butter chips style bags without brand text, price tags as blurred shapes.
11. Mochi slows on slippery floor. 10 poses: foot slide -> arms out -> regain balance. Korea refs: polished convenience-store tile, reflected neon, wet umbrella basket near entrance.
12. Zumu slows his blue trail. 10 poses: fast trail -> dim trail -> guiding gesture. Korea refs: refrigerated drinks, canned coffee, soju-green bottle silhouettes kept child-safe/background only.
13. Mochi notices the trembling tiny star. 10 poses: look down -> sad eyes -> kneel-like softness. Korea refs: low shelf with rice balls, small trash/recycle sorting bins.
14. Zumu realizes the star is afraid of bright lights. 10 poses: look at star -> tail dims -> concern. Korea refs: fluorescent ceiling light panels, hot-water machine glow in background.
15. Mochi says they can wait. 10 poses: sad star -> Mochi breathes -> warm lights gather. Korea refs: quiet corner by window, rainy street outside, soft reflection on tile.
16. Zumu makes his tail smaller. 10 poses: tail glow shrinks -> soft blue halo. Korea refs: glass door reflection, counter edge, payment terminal silhouette.
17. Mochi sees the tiny star glow again. 10 poses: star flicker -> Mochi smiles carefully. Korea refs: cup-noodle hot water area, paper cup dispenser, steam glow.
18. Zumu explains lining up at the door. 10 poses: point to door -> stars begin forming line. Korea refs: automatic door arrows as icons only, entrance mat, 24-hour sign outside.
19. Mochi observes the door wind. 10 poses: door opens -> cheek fur moves -> Mochi notices rhythm. Korea refs: sliding door, rain gust, plastic umbrella sleeve stand.
20. Zumu turns the wind into a rhythm game. 10 poses: count one -> two -> sparkle beat. Korea refs: door chime speaker, floor reflection, star-shaped store decoration.
21. Mochi tells the stars not to hurry. 10 poses: stars jitter -> Mochi calming paw. Korea refs: aisle endcap, small basket, neat product rows.
22. Zumu invites them onto the blue path. 10 poses: path appears -> stars step on light. Korea refs: storefront threshold, rain outside, delivery scooter blur in distance.
23. Mochi contrasts cold outside and warm inside. 10 poses: look outside -> look inside -> warm smile. Korea refs: rainy Korean street, apartment building, warm convenience-store interior.
24. Zumu says the light helps stars not get lost. 10 poses: sign reflection -> Zumu nods. Korea refs: 24시 hanging sign reflected in puddle, store star icon.
25. Mochi spots the last star near the ramyeon machine. 10 poses: search -> find -> careful point. Korea refs: hot-water ramyeon machine, cup noodle stack, steam, chopstick dispenser.
26. Zumu says the hot-water sound scared it. 10 poses: listen -> understand -> soft concern. Korea refs: hot-water dispenser, red temperature light, steam, paper cup area.
27. Mochi offers his hand. 10 poses: paw extends slowly -> tiny star approaches. Korea refs: quiet corner near door, wet glass, warm reflection.
28. Zumu reassures beside Mochi. 10 poses: floats close -> places hand/comforting presence. Korea refs: convenience-store interior corner, gentle glass reflections, star dust.
29. Mochi asks if everyone is ready. 10 poses: looks at star group -> nods. Korea refs: stars lined on entrance mat, automatic door frame, street rain outside.
30. Zumu creates the blue path. 10 poses: tail arc -> path grows -> stars follow. Korea refs: blue light path toward sidewalk, puddles, night street sign.
31. Mochi counts them through the door. 10 poses: door opens -> one-by-one guiding. Korea refs: sliding door threshold, umbrella stand, wet pavement.
32. Zumu watches them rise into the night. 10 poses: stars exit -> Zumu looks upward. Korea refs: Korean residential street, apartment windows, power lines, rain.
33. Mochi sees the store sign brighter. 10 poses: glance sign -> relieved smile. Korea refs: glowing 24시 star sign, puddle reflection, store facade.
34. Zumu calls the store a star stop. 10 poses: wide store view -> Zumu jokes softly. Korea refs: convenience-store exterior, street bench, delivery scooter silhouette, warm storefront.
35. Mochi asks about tomorrow's adventure. 10 poses: Mochi turns to Zumu -> hopeful smile. Korea refs: outside entrance under awning, soft rain, lights fading.
36. Zumu answers the road is not scary with Mochi. 10 poses: Zumu smiles -> both together -> fade star dust. Korea refs: rainy alley, glowing store behind them, final warm puddle reflection.

## Implementation rule

Do not stretch one still image across multiple phrases. A final valid episode must use either:

- 36 generated contact sheets, one per phrase, each with 10 clear progressive poses, or
- 360 individual generated frames/poses with the same phrase mapping.

The current next step is to generate these 36 phrase sheets and rebuild the 1800-frame MP4 from them.

## Text rule

All image generation prompts must include:

> no text, no captions, no Korean dialogue, no labels, no panel numbers, no watermark

The Korean dialogue exists only in the timing manifest and final subtitle/overlay files. It must not appear inside the generated images.
