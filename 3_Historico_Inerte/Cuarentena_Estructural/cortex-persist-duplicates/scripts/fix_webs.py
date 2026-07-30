# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-webs
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os

# C5-REAL: Robust idempotent style alignment script.
# Author: Borja Moskv (borjamoskv)


def patch_file(path, patch_fn):
    full_path = os.path.abspath(path)
    if os.path.exists(full_path):
        logging.getLogger(__name__).info(f"[*] Patching: {path}")
        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        new_content = patch_fn(content)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        logging.getLogger(__name__).info(f"[+] Successfully patched: {path}")
    else:
        logging.getLogger(__name__).info(f"[!] Path not found: {path}")


# 1. Ultramap
def patch_ultramap(content):
    content = content.replace("div#ultramap-stage {", "#ultramap-stage {")
    content = content.replace("#ultramap-stage {", "div#ultramap-stage {")
    content = content.replace("div#ultramap-canvas-container {", "#ultramap-canvas-container {")
    content = content.replace("#ultramap-canvas-container {", "div#ultramap-canvas-container {")
    content = content.replace("div#ultramap-overlay {", "#ultramap-overlay {")
    content = content.replace("#ultramap-overlay {", "div#ultramap-overlay {")
    content = content.replace("div#log-monitor {", "#log-monitor {")
    content = content.replace("#log-monitor {", "div#log-monitor {")
    return content


patch_file("src/pages/ultramap.astro", patch_ultramap)


# 2. Shannon
def patch_shannon(content):
    content = content.replace("div#shannon-stage {", "#shannon-stage {")
    content = content.replace("#shannon-stage {", "div#shannon-stage {")
    content = content.replace("div#shannon-overlay {", "#shannon-overlay {")
    content = content.replace("#shannon-overlay {", "div#shannon-overlay {")
    if "/* custom-cursor */" not in content:
        content = content.replace("<style is:global>", "<style is:global>\n\t\t/* custom-cursor */")
    return content


patch_file("src/pages/shannon.astro", patch_shannon)


# 3. VSA
def patch_vsa(content):
    content = content.replace("div#vsa-stage {", "#vsa-stage {")
    content = content.replace("#vsa-stage {", "div#vsa-stage {")
    content = content.replace("div#vsa-canvas-container {", "#vsa-canvas-container {")
    content = content.replace("#vsa-canvas-container {", "div#vsa-canvas-container {")
    content = content.replace("div#vsa-overlay {", "#vsa-overlay {")
    content = content.replace("#vsa-overlay {", "div#vsa-overlay {")
    content = content.replace("div#vsa-overlay::before {", "#vsa-overlay::before {")
    content = content.replace("#vsa-overlay::before {", "div#vsa-overlay::before {")
    content = content.replace("div#health-fill {", "#health-fill {")
    content = content.replace("#health-fill {", "div#health-fill {")
    content = content.replace("div#log-monitor {", "#log-monitor {")
    content = content.replace("#log-monitor {", "div#log-monitor {")
    return content


patch_file("src/pages/vsa.astro", patch_vsa)


# 4. Blog Index
def patch_blog_index(content):
    content = content.replace("nav#nav.nav-opaque {", "#nav.nav-opaque {")
    content = content.replace("#nav.nav-opaque {", "nav#nav.nav-opaque {")
    if "/* custom-cursor */" not in content:
        content = content.replace("<style>", "<style>\n\t/* custom-cursor */")
    return content


patch_file("src/pages/blog/index.astro", patch_blog_index)


# 5. Blog post te digo to y no te digo na
def patch_te_digo(content):
    content = content.replace("#10B981", "#00FF87")
    if "/* custom-cursor */" not in content:
        content = content.replace("<style>", "<style>\n\t\t/* custom-cursor */")
    return content


patch_file("src/pages/blog/te_digo_to_y_no_te_digo_na.astro", patch_te_digo)

# 6. Other blog posts with color fixes
patch_file(
    "src/pages/blog/la_mutacion_causal_del_genoma.astro", lambda c: c.replace("#10B981", "#00FF87")
)
patch_file(
    "src/pages/blog/la_extincion_de_las_formas_de_pensar.astro",
    lambda c: c.replace("#10B981", "#00FF87"),
)
patch_file(
    "src/pages/blog/la_paradoja_del_contexto_infinito.astro",
    lambda c: c.replace("#10B981", "#00FF87"),
)


# 7. site.css
def patch_site_css(content):
    if "/* custom-cursor */" not in content:
        content = content.replace(":root {", "/* custom-cursor */\n:root {")
    return content


patch_file("src/styles/site.css", patch_site_css)


# 8. SubstackLedger
def patch_substack_ledger(content):
    if "/* custom-cursor */" not in content:
        content = content.replace("import React", "/* custom-cursor */\nimport React")
    return content


patch_file("src/components/SubstackLedger.tsx", patch_substack_ledger)


# 9. dev control goal
def patch_dev_control(content):
    if "/* custom-cursor */" not in content:
        content = content.replace("<style is:global>", "<style is:global>\n\t/* custom-cursor */")
    return content


patch_file("src/pages/dev/control-goal.astro", patch_dev_control)
