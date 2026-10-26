// Archivum Buczkovianum — Figma → repository design export.
//
// Run in the browser devtools console of the Figma file "archiwum buczkowski model"
// (any page; the script switches to PAGE_NAME). Requires edit or view access.
// Output: a single design-export.zip download with tokens, component and screen
// specs, design rules, image/icon assets and PNG previews. Re-run after every
// round of design changes and commit the diff.

// Filled in only when the script embeds itself into the export; null when run from the repo copy.
const SELF = null;
const PAGE_NAME = 'po korekcie';
const SCREEN_SECTIONS = /^0[45]\b/;
const COMPONENT_SECTIONS = /^0[23]\b/;
const RULES_FRAME = 'Zasady i słownik';

const files = [];
const add = (path, data) => files.push({ path, data });
const enc = new TextEncoder();

const slug = (s) => s.replace(/ł/g, 'l').replace(/Ł/g, 'L').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const hex2 = (x) => Math.round(x * 255).toString(16).padStart(2, '0');
const hex = (c, a = 1) => '#' + hex2(c.r) + hex2(c.g) + hex2(c.b) + (a < 1 ? hex2(a) : '');
const px = (v) => `${Math.round(v * 100) / 100}px`;

const page = figma.root.children.find((p) => p.name === PAGE_NAME);
await figma.setCurrentPageAsync(page);

// ---------------------------------------------------------------- tokens
const collections = await figma.variables.getLocalVariableCollectionsAsync();
const variables = await figma.variables.getLocalVariablesAsync();
const varById = Object.fromEntries(variables.map((v) => [v.id, v]));
const cssName = (v) => {
  const web = v.codeSyntax && v.codeSyntax.WEB;
  const m = web && web.match(/var\((--[^)]+)\)/);
  return m ? m[1] : '--' + slug(v.name);
};
const varRef = (id) => (varById[id] ? `var(${cssName(varById[id])})` : `?${id}`);

const textStyles = await figma.getLocalTextStylesAsync();
const effectStyles = await figma.getLocalEffectStylesAsync();
const textClass = (s) => 'text-' + slug(s.name);
const shadowVar = (s) => '--shadow-' + slug(s.name.split('/').pop());
const styleById = {};
textStyles.forEach((s) => { styleById[s.id] = s; });
effectStyles.forEach((s) => { styleById[s.id] = s; });

const fontWeight = (style) => (/Bold/.test(style) ? (/Semi/.test(style) ? 600 : 700) : /Medium/.test(style) ? 500 : 400);
const fontStack = (family) => (family === 'Cousine'
  ? "'Cousine', ui-monospace, 'Courier New', monospace"
  : "'Lora', Georgia, 'Times New Roman', serif");
const lineHeight = (l) => (l.unit === 'AUTO' ? 'normal' : l.unit === 'PERCENT' ? String(+(l.value / 100).toFixed(3)) : px(l.value));
const letterSpacing = (l, size) => (l.value === 0 ? 'normal'
  : l.unit === 'PERCENT' ? `${+(l.value / 100).toFixed(4)}em` : `${+(l.value / size).toFixed(4)}em`);

let css = `/* Generated from Figma ("${figma.root.name}", page "${PAGE_NAME}") by design/tools/export-figma.js.\n   Do not edit by hand: change Figma and re-export. */\n:root {\n`;
const dtcg = {};
const setPath = (obj, path, val) => {
  const parts = path.split('/');
  let o = obj;
  parts.slice(0, -1).forEach((k) => { o[k] = o[k] || {}; o = o[k]; });
  o[parts[parts.length - 1]] = val;
};
for (const c of collections) {
  css += `\n  /* ${c.name} */\n`;
  for (const id of c.variableIds) {
    const v = varById[id];
    const val = v.valuesByMode[c.modes[0].modeId];
    let cssValue;
    let jsonValue;
    if (val && val.type === 'VARIABLE_ALIAS') {
      cssValue = varRef(val.id);
      jsonValue = `{${varById[val.id].name.replace(/\//g, '.')}}`;
    } else if (v.resolvedType === 'COLOR') {
      cssValue = jsonValue = hex(val, val.a === undefined ? 1 : val.a);
    } else if (v.resolvedType === 'FLOAT') {
      cssValue = jsonValue = px(val);
    } else {
      cssValue = JSON.stringify(val);
      jsonValue = val;
    }
    css += `  ${cssName(v)}: ${cssValue};\n`;
    setPath(dtcg, v.name, {
      $type: v.resolvedType === 'COLOR' ? 'color' : 'dimension',
      $value: jsonValue,
      $extensions: { figma: { collection: c.name, cssVariable: cssName(v) } },
    });
  }
}
css += '\n  /* Shadows (effect styles) */\n';
for (const s of effectStyles) {
  const shadows = s.effects.filter((e) => e.type === 'DROP_SHADOW');
  if (!shadows.length) continue;
  css += `  ${shadowVar(s)}: ${shadows.map((e) => `${px(e.offset.x)} ${px(e.offset.y)} ${px(e.radius)} ${px(e.spread || 0)} rgba(${Math.round(e.color.r * 255)}, ${Math.round(e.color.g * 255)}, ${Math.round(e.color.b * 255)}, ${+e.color.a.toFixed(3)})`).join(', ')};\n`;
  setPath(dtcg, `shadow/${slug(s.name.split('/').pop())}`, {
    $type: 'shadow',
    $value: shadows.map((e) => ({ color: hex(e.color, e.color.a), offsetX: px(e.offset.x), offsetY: px(e.offset.y), blur: px(e.radius), spread: px(e.spread || 0) })),
    $description: s.description,
  });
}
css += '}\n\n/* Text styles: one class per Figma text style */\n';
for (const s of textStyles) {
  const italic = /Italic/.test(s.fontName.style);
  css += `.${textClass(s)} {\n  font-family: ${fontStack(s.fontName.family)};\n  font-weight: ${fontWeight(s.fontName.style)};\n  font-style: ${italic ? 'italic' : 'normal'};\n  font-size: ${px(s.fontSize)};\n  line-height: ${lineHeight(s.lineHeight)};\n  letter-spacing: ${letterSpacing(s.letterSpacing, s.fontSize)};\n${s.textCase === 'UPPER' ? '  text-transform: uppercase;\n' : ''}}\n`;
  setPath(dtcg, `typography/${s.name}`, {
    $type: 'typography',
    $value: {
      fontFamily: s.fontName.family, fontWeight: fontWeight(s.fontName.style), fontStyle: italic ? 'italic' : 'normal',
      fontSize: px(s.fontSize), lineHeight: lineHeight(s.lineHeight), letterSpacing: letterSpacing(s.letterSpacing, s.fontSize),
      textTransform: s.textCase === 'UPPER' ? 'uppercase' : 'none',
    },
    ...(s.description ? { $description: s.description } : {}),
    $extensions: { figma: { cssClass: textClass(s) } },
  });
}
add('design/tokens/tokens.css', css);
add('design/tokens/tokens.json', JSON.stringify(dtcg, null, 2) + '\n');

// ---------------------------------------------------------------- node specs
const images = new Map(); // imageHash -> asset file name
const imageName = (hash, hint) => {
  if (!images.has(hash)) images.set(hash, `${slug(hint) || 'image'}-${hash.slice(0, 8)}`);
  return images.get(hash);
};
const paint = (p, node) => {
  if (p.visible === false) return null;
  if (p.type === 'SOLID') {
    const id = p.boundVariables && p.boundVariables.color && p.boundVariables.color.id;
    const base = id ? varRef(id) : hex(p.color);
    return p.opacity !== undefined && p.opacity < 1 ? `${base} @${Math.round(p.opacity * 100)}%` : base;
  }
  if (p.type === 'IMAGE') return `image(assets/images/${imageName(p.imageHash, node.name)}.*, ${p.scaleMode.toLowerCase()})`;
  if (p.type.startsWith('GRADIENT')) {
    return `${p.type.toLowerCase().replace('gradient_', '')}-gradient(${p.gradientStops.map((s) => `${hex(s.color, s.color.a)} ${Math.round(s.position * 100)}%`).join(', ')})`;
  }
  return p.type.toLowerCase();
};
const bound = (n, key, raw) => {
  const b = n.boundVariables && n.boundVariables[key];
  return b && b.id ? varRef(b.id) : px(raw);
};
const justify = { MIN: 'start', CENTER: 'center', MAX: 'end', SPACE_BETWEEN: 'space-between', BASELINE: 'baseline' };

const nodeProps = (n) => {
  const a = [];
  const parentAuto = n.parent && 'layoutMode' in n.parent && n.parent.layoutMode && n.parent.layoutMode !== 'NONE';
  if ('layoutMode' in n && n.layoutMode && n.layoutMode !== 'NONE') {
    a.push(`flex-${n.layoutMode === 'HORIZONTAL' ? 'row' : 'column'}${n.layoutWrap === 'WRAP' ? ' wrap' : ''}`);
    if (n.primaryAxisAlignItems !== 'SPACE_BETWEEN' || n.children.length < 2) a.push(`gap ${bound(n, 'itemSpacing', n.itemSpacing)}`);
    const pads = ['paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft'].map((k) => bound(n, k, n[k]));
    if (pads.some((p) => p !== '0px')) a.push(`padding ${pads.every((p) => p === pads[0]) ? pads[0] : pads.join(' ')}`);
    if (n.primaryAxisAlignItems !== 'MIN') a.push(`justify ${justify[n.primaryAxisAlignItems]}`);
    if (n.counterAxisAlignItems !== 'MIN') a.push(`align ${justify[n.counterAxisAlignItems]}`);
  } else if ('children' in n && n.type !== 'INSTANCE' && n.type !== 'BOOLEAN_OPERATION' && n.children.length) {
    a.push('free layout (children positioned)');
  }
  if (n.parent && n.parent.type !== 'SECTION' && n.parent.type !== 'PAGE') {
    const sizing = (axis, size) => {
      const s = n[`layoutSizing${axis}`];
      return !s || s === 'FIXED' ? px(size) : s.toLowerCase();
    };
    if (n.type !== 'TEXT' || n.textAutoResize !== 'WIDTH_AND_HEIGHT') a.push(`w ${sizing('Horizontal', n.width)}, h ${sizing('Vertical', n.height)}`);
    if (n.layoutPositioning === 'ABSOLUTE') a.push(`position absolute at (${Math.round(n.x)}, ${Math.round(n.y)})`);
    else if (!parentAuto) a.push(`at (${Math.round(n.x)}, ${Math.round(n.y)})`);
  } else {
    a.push(`${px(n.width)} × ${px(n.height)}`);
  }
  if ('minWidth' in n && n.minWidth) a.push(`min-w ${px(n.minWidth)}`);
  if ('maxWidth' in n && n.maxWidth) a.push(`max-w ${px(n.maxWidth)}`);
  if (n.type !== 'TEXT' && 'fills' in n && Array.isArray(n.fills)) {
    const f = n.fills.map((p) => paint(p, n)).filter(Boolean);
    if (f.length) a.push(`bg ${f.reverse().join(' over ')}`);
  }
  if ('strokes' in n && n.strokes.length && n.strokes.some((s) => s.visible !== false)) {
    const color = n.strokes.map((p) => paint(p, n)).filter(Boolean).join(', ');
    if (n.strokeWeight === figma.mixed || n.strokeTopWeight !== n.strokeBottomWeight || n.strokeLeftWeight !== n.strokeTopWeight) {
      const sides = [['top', n.strokeTopWeight], ['right', n.strokeRightWeight], ['bottom', n.strokeBottomWeight], ['left', n.strokeLeftWeight]]
        .filter(([, w]) => w > 0).map(([s, w]) => `${s} ${px(w)}`);
      if (sides.length) a.push(`border-${sides.join(', ')} ${color}`);
    } else if (n.strokeWeight > 0) {
      a.push(`border ${px(n.strokeWeight)} ${color}${n.dashPattern && n.dashPattern.length ? ' dashed' : ''}`);
    }
  }
  if ('cornerRadius' in n) {
    if (n.boundVariables && n.boundVariables.topLeftRadius) a.push(`radius ${varRef(n.boundVariables.topLeftRadius.id)}`);
    else if (n.cornerRadius === figma.mixed) a.push(`radius ${[n.topLeftRadius, n.topRightRadius, n.bottomRightRadius, n.bottomLeftRadius].map(px).join(' ')}`);
    else if (n.cornerRadius > 0) a.push(`radius ${px(n.cornerRadius)}`);
  }
  if ('effects' in n && n.effects.length) {
    if (n.effectStyleId && styleById[n.effectStyleId]) a.push(`shadow var(${shadowVar(styleById[n.effectStyleId])})`);
    else n.effects.filter((e) => e.visible !== false).forEach((e) => a.push(e.type === 'NOISE' ? `paper grain (noise, white @${Math.round(e.color.a * 100)}%)` : e.type.toLowerCase()));
  }
  if ('opacity' in n && n.opacity < 1) a.push(`opacity ${Math.round(n.opacity * 100)}%`);
  if ('clipsContent' in n && n.clipsContent && n.type !== 'INSTANCE') a.push('overflow hidden');
  if (n.type === 'TEXT') {
    const st = n.textStyleId === figma.mixed ? 'mixed styles' : styleById[n.textStyleId] ? `.${textClass(styleById[n.textStyleId])}` : `${n.fontName.family} ${n.fontName.style} ${n.fontSize}px (no style!)`;
    a.push(st);
    const f = Array.isArray(n.fills) ? n.fills.map((p) => paint(p, n)).filter(Boolean) : [];
    if (f.length) a.push(`color ${f.join(', ')}`);
    if (n.textDecoration && n.textDecoration !== 'NONE' && n.textDecoration !== figma.mixed) a.push(n.textDecoration.toLowerCase());
    if (n.textAlignHorizontal !== 'LEFT') a.push(`text-align ${n.textAlignHorizontal.toLowerCase()}`);
    if (n.textTruncation === 'ENDING') a.push(`truncate${n.maxLines ? ` after ${n.maxLines} lines` : ''}`);
  }
  return a;
};

const reactionText = async (n) => {
  const out = [];
  for (const r of n.reactions || []) {
    for (const act of r.actions || []) {
      if (act.type !== 'NODE' || !act.destinationId) continue;
      const dest = await figma.getNodeByIdAsync(act.destinationId);
      const t = act.transition;
      const trig = r.trigger.type === 'ON_HOVER' ? 'on hover' : r.trigger.type === 'AFTER_TIMEOUT' ? `after ${Math.round(r.trigger.timeout * 1000)} ms` : r.trigger.type.toLowerCase();
      out.push(`${trig} → ${dest ? dest.name : act.destinationId}${t ? ` (${t.type.toLowerCase().replace('_', ' ')} ${Math.round(t.duration * 1000)} ms, ${t.easing.type.toLowerCase().replace(/_/g, '-')})` : ''}`);
    }
  }
  return out;
};

const componentLabel = (mc) => (mc.parent && mc.parent.type === 'COMPONENT_SET' ? `${mc.parent.name} [${mc.name}]` : mc.name);
const propKey = (k) => k.replace(/#[^#]*$/, '');

const describe = async (n, depth, lines) => {
  if (n.visible === false) return;
  const ind = '  '.repeat(depth);
  const props = nodeProps(n);
  if (n.type === 'TEXT') {
    lines.push(`${ind}- text "${n.name}" · ${props.join(' · ')} · “${n.characters.replace(/\n/g, '⏎')}”`);
    return;
  }
  if (n.type === 'INSTANCE') {
    const mc = await n.getMainComponentAsync();
    const cp = Object.entries(n.componentProperties || {}).map(([k, v]) => {
      if (v.type === 'INSTANCE_SWAP') return null;
      return `${propKey(k)}=${typeof v.value === 'string' ? `“${v.value}”` : v.value}`;
    }).filter(Boolean);
    lines.push(`${ind}- **${mc ? componentLabel(mc) : n.name}**${cp.length ? ` {${cp.join(', ')}}` : ''} · ${props.join(' · ')}`);
    // Surface overrides that are not exposed as component properties (texts, images, colors).
    for (const o of n.overrides || []) {
      if (o.id === n.id) continue;
      const on = await figma.getNodeByIdAsync(o.id);
      if (!on || on.visible === false) continue;
      const fields = o.overriddenFields.filter((f) => ['characters', 'fills', 'visible', 'opacity', 'textStyleId'].includes(f));
      if (!fields.length) continue;
      const detail = fields.map((f) => {
        if (f === 'characters' && on.type === 'TEXT') return `text “${on.characters.replace(/\n/g, '⏎')}”`;
        if (f === 'fills' && Array.isArray(on.fills)) return `fill ${on.fills.map((p) => paint(p, on)).filter(Boolean).join(' over ')}`;
        if (f === 'opacity') return `opacity ${Math.round(on.opacity * 100)}%`;
        if (f === 'textStyleId' && styleById[on.textStyleId]) return `.${textClass(styleById[on.textStyleId])}`;
        return f;
      });
      lines.push(`${ind}  - override "${on.name}": ${detail.join(', ')}`);
    }
    return;
  }
  if (n.type === 'VECTOR' || n.type === 'BOOLEAN_OPERATION' || n.type === 'ELLIPSE' || n.type === 'LINE' || n.type === 'STAR' || n.type === 'POLYGON') {
    lines.push(`${ind}- ${n.type.toLowerCase()} "${n.name}" · ${props.join(' · ')}`);
    return;
  }
  lines.push(`${ind}- ${n.type === 'RECTANGLE' ? 'rect' : 'box'} "${n.name}" · ${props.join(' · ')}`);
  const react = await reactionText(n);
  react.forEach((r) => lines.push(`${ind}  - interaction: ${r}`));
  if ('children' in n) for (const c of n.children) await describe(c, depth + 1, lines);
};

const sections = page.children.filter((n) => n.type === 'SECTION');
const pngs = []; // { path, node, scale }

// ---------------------------------------------------------------- components
const componentIndex = [];
const icons = [];
for (const sec of sections.filter((s) => COMPONENT_SECTIONS.test(s.name))) {
  for (const c of sec.children.filter((n) => n.type === 'COMPONENT' || n.type === 'COMPONENT_SET')) {
    if (c.name.startsWith('Ikona/')) { icons.push(c); continue; }
    const file = slug(c.name);
    const md = [`# ${c.name}`, ''];
    if (c.description) md.push(c.description, '');
    const defs = c.componentPropertyDefinitions;
    const defLines = Object.entries(defs).map(([k, d]) => {
      if (d.type === 'VARIANT') return `- \`${propKey(k)}\` (variant): ${d.variantOptions.join(' | ')} — default ${d.defaultValue}`;
      if (d.type === 'TEXT') return `- \`${propKey(k)}\` (text) — default “${d.defaultValue}”`;
      if (d.type === 'BOOLEAN') return `- \`${propKey(k)}\` (boolean) — default ${d.defaultValue}`;
      return `- \`${propKey(k)}\` (${d.type.toLowerCase()})`;
    });
    if (defLines.length) md.push('## Properties', '', ...defLines, '');
    const variants = c.type === 'COMPONENT_SET' ? c.children : [c];
    md.push(`## ${c.type === 'COMPONENT_SET' ? 'Variants' : 'Structure'}`, '');
    for (const v of variants) {
      if (c.type === 'COMPONENT_SET') md.push(`### ${v.name}`, '');
      const lines = [];
      await describe(v, 0, lines);
      md.push(...lines, '');
    }
    md.push(`Preview: \`../previews/components/${file}.png\``, '');
    add(`design/components/${file}.md`, md.join('\n'));
    pngs.push({ path: `design/previews/components/${file}.png`, node: c, scale: 2 });
    componentIndex.push({ name: c.name, file, section: sec.name });
  }
}
for (const ic of icons) {
  const svg = await ic.exportAsync({ format: 'SVG_STRING', svgOutlineText: false, svgIdAttribute: false });
  add(`design/assets/icons/${slug(ic.name.replace('Ikona/', ''))}.svg`, svg.replace(/stroke="#[0-9A-Fa-f]{6}"/g, 'stroke="currentColor"').replace(/fill="#[0-9A-Fa-f]{6}"/g, (m) => (m === 'fill="#FFFFFF"' ? m : 'fill="currentColor"')));
}

// ---------------------------------------------------------------- screens
const screenIndex = [];
for (const sec of sections.filter((s) => SCREEN_SECTIONS.test(s.name))) {
  const mobile = /mobile/i.test(sec.name);
  for (const s of sec.children.filter((n) => n.type === 'FRAME')) {
    const file = slug(s.name);
    const lines = [];
    await describe(s, 0, lines);
    add(`design/screens/${file}.md`, [`# ${s.name}`, '', `Viewport: ${mobile ? 'mobile' : 'desktop'}, ${px(s.width)} wide. Preview: \`../previews/screens/${file}.png\``, '', ...lines, ''].join('\n'));
    pngs.push({ path: `design/previews/screens/${file}.png`, node: s, scale: mobile ? 2 : 1 });
    screenIndex.push({ name: s.name, file, mobile });
  }
}

// ---------------------------------------------------------------- rules
const rules = page.findOne((n) => n.type === 'FRAME' && n.name === RULES_FRAME);
if (rules) {
  const md = [];
  for (const t of rules.findAll((n) => n.type === 'TEXT')) {
    const st = styleById[t.textStyleId] ? styleById[t.textStyleId].name : '';
    if (/Tytuł strony/.test(st)) md.push(`# ${t.characters}`, '');
    else if (/Tytuł sekcji/.test(st)) md.push(`## ${t.characters}`, '');
    else md.push(t.characters, '');
  }
  add('design/rules.md', md.join('\n'));
}

// ---------------------------------------------------------------- binary assets
const sniff = (b) => (b[0] === 0x89 ? 'png' : b[0] === 0xff ? 'jpg' : b[0] === 0x47 ? 'gif' : b[0] === 0x52 ? 'webp' : 'bin');
for (const [hash, name] of images) {
  const img = figma.getImageByHash(hash);
  if (!img) continue;
  const bytes = await img.getBytesAsync();
  add(`design/assets/images/${name}.${sniff(bytes)}`, bytes);
}
for (const p of pngs) add(p.path, await p.node.exportAsync({ format: 'PNG', constraint: { type: 'SCALE', value: p.scale } }));

// ---------------------------------------------------------------- readme + manifest
const readme = `# Design export

Generated from the Figma file "${figma.root.name}" (page "${PAGE_NAME}") by \`tools/export-figma.js\`.
**Figma is the source of truth.** Never edit files in \`design/\` by hand: change Figma, re-export, commit the diff.

## How to build from this

1. Read \`rules.md\` first: object dictionary, call-number format, navigation, typography, hover and loading states.
2. Import \`tokens/tokens.css\` once, globally. Use only its custom properties and \`.text-*\` classes.
   Never hard-code a color, spacing, radius, shadow or font value that exists as a token.
3. Build components from \`components/*.md\` before screens. Screens are composed only of those components.
4. Screens: \`screens/*.md\` is the spec; \`previews/**/*.png\` is for visual verification only.
   If a preview and a spec disagree, the spec wins.

## Spec notation

- \`box\` = container, \`text\` = text node, **bold name** = component instance with \`{property=value}\`.
- \`flex-row\` / \`flex-column\` = auto layout; \`gap\`, \`padding\`, \`justify\`, \`align\` map 1:1 to flexbox.
- \`w fill\` = stretch on that axis (\`flex: 1\` / \`align-self: stretch\`), \`hug\` = fit content, a px value = fixed.
- \`var(--…)\` = token from \`tokens.css\`; a raw hex or px value means the design does not use a token there.
- \`.text-…\` = text style class from \`tokens.css\`; text in “…” is the real copy (UI language: Polish).
- \`override\` = instance content that differs from the component default.
- \`interaction\` = prototype behaviour; implement as CSS transitions (respect \`prefers-reduced-motion\`).
- \`image(assets/images/…)\` = placeholder or real image asset; icons are in \`assets/icons/\` (stroke uses \`currentColor\`).

## Components

${componentIndex.map((c) => `- [${c.name}](components/${c.file}.md)`).join('\n')}

## Screens

${screenIndex.map((s) => `- [${s.name}](screens/${s.file}.md)${s.mobile ? ' (mobile)' : ''}`).join('\n')}
`;
add('design/README.md', readme);
if (SELF) add('design/tools/export-figma.js', SELF);
add('design/manifest.json', JSON.stringify({
  figmaFile: figma.root.name, page: PAGE_NAME, exportedAt: new Date().toISOString(),
  counts: { components: componentIndex.length, icons: icons.length, screens: screenIndex.length, images: images.size, variables: variables.length, textStyles: textStyles.length, effectStyles: effectStyles.length },
}, null, 2) + '\n');

// ---------------------------------------------------------------- zip (store, no compression)
const crcTable = new Uint32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
const crc32 = (b) => {
  let c = 0xffffffff;
  for (let i = 0; i < b.length; i++) c = crcTable[(c ^ b[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const now = new Date();
const dosTime = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
const dosDate = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
const chunks = [];
const central = [];
let offset = 0;
for (const f of files) {
  const name = enc.encode(f.path);
  const data = typeof f.data === 'string' ? enc.encode(f.data) : f.data;
  const crc = crc32(data);
  const local = new DataView(new ArrayBuffer(30));
  [[0, 0x04034b50, 4], [4, 20, 2], [6, 0x0800, 2], [8, 0, 2], [10, dosTime, 2], [12, dosDate, 2], [14, crc, 4], [18, data.length, 4], [22, data.length, 4], [26, name.length, 2], [28, 0, 2]]
    .forEach(([o, v, s]) => (s === 4 ? local.setUint32(o, v, true) : local.setUint16(o, v, true)));
  chunks.push(new Uint8Array(local.buffer), name, data);
  const cd = new DataView(new ArrayBuffer(46));
  [[0, 0x02014b50, 4], [4, 20, 2], [6, 20, 2], [8, 0x0800, 2], [10, 0, 2], [12, dosTime, 2], [14, dosDate, 2], [16, crc, 4], [20, data.length, 4], [24, data.length, 4], [28, name.length, 2], [30, 0, 2], [32, 0, 2], [34, 0, 2], [36, 0, 2], [38, 0, 4], [42, offset, 4]]
    .forEach(([o, v, s]) => (s === 4 ? cd.setUint32(o, v, true) : cd.setUint16(o, v, true)));
  central.push(new Uint8Array(cd.buffer), name);
  offset += 30 + name.length + data.length;
}
const cdSize = central.reduce((s, c) => s + c.length, 0);
const end = new DataView(new ArrayBuffer(22));
[[0, 0x06054b50, 4], [8, files.length, 2], [10, files.length, 2], [12, cdSize, 4], [16, offset, 4]]
  .forEach(([o, v, s]) => (s === 4 ? end.setUint32(o, v, true) : end.setUint16(o, v, true)));
const blob = new Blob([...chunks, ...central, new Uint8Array(end.buffer)], { type: 'application/zip' });
window.__designExport = { blob, files: files.map((f) => ({ path: f.path, size: typeof f.data === 'string' ? enc.encode(f.data).length : f.data.length })) };
window.__designExportText = Object.fromEntries(files.filter((f) => typeof f.data === 'string').map((f) => [f.path, f.data]));
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = 'design-export.zip';
document.body.appendChild(a);
a.click();
a.remove();
({ files: files.length, zipBytes: blob.size, counts: { components: componentIndex.length, icons: icons.length, screens: screenIndex.length, images: images.size } });