"""
icons_def.py — the brand-neutral ICON DEFINITION LIBRARY (single source of truth).

Every icon is geometry on the 24 x 24 grid built from iconkit primitives — never fixed SVG artwork — so each
brand gets its own family: stroke width, caps and joins from dna.stroke, container corners from dna.corner
(cut → chamfer at dna.angles.cut on the bottom-right container corner · round/soft → fillets · square → sharp),
faceted brands get polygonal curves, organic brands eased joints. See lib/iconkit.py for the tag grammar.

Rules: centre-lines inside 3…21 (circle r ≤ 9 around 12,12) → ink inside the 2 px padding (live area 20);
author on the 0.25 grid, horizontals/verticals on whole or half units; one idea per icon; ≤ 3 levels of detail.

icon(name, set, prims, keywords, aliases)  — `set` is the theme set the profile lists (assets/profiles → icons).
"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from iconkit import (PL, PG, L, R, C, E, D, A, P, FO, SOLID, T, pin, drop, heart, star_pts, reg_pts, gear, capsule,
                     link, arrowhead, arc_arrow, chain, wave, bumps, tangent_pts, D2R)

ICONS = []

SETS = {
    'ui': 'Interface & navigation', 'core': 'Core', 'education': 'Education', 'culture': 'Culture & arts',
    'people': 'People', 'time': 'Time', 'location': 'Location', 'accessibility': 'Accessibility',
    'health': 'Health', 'body': 'Body & movement', 'care': 'Care', 'communication': 'Communication',
    'food': 'Food', 'drink': 'Drink', 'dietary': 'Dietary', 'hospitality': 'Hospitality',
    'industry': 'Industry', 'energy': 'Energy', 'logistics': 'Logistics', 'safety': 'Safety',
    'data': 'Data', 'environment': 'Environment', 'community': 'Community', 'business': 'Business',
    'finance': 'Finance', 'legal': 'Legal', 'commerce': 'Commerce', 'delivery': 'Delivery',
    'social': 'Social', 'product-care': 'Product care', 'product': 'Product', 'devices': 'Devices',
    'security': 'Security',
}


def icon(name, set_, prims, kw='', aliases=(), label=None):
    flat = []
    for p in prims:
        if isinstance(p, list): flat.extend(p)
        else: flat.append(p)
    ICONS.append({'name': name, 'set': set_, 'prims': flat, 'keywords': kw.split() if isinstance(kw, str) else list(kw),
                  'aliases': list(aliases), 'label': label})


def bust(cx, hy, hr, x0, x1, top, bottom, s=4):
    """Head + shoulders (person). Head and body are the tint."""
    body = [(x0, bottom), (x0, top, 's%g' % s), (x1, top, 's%g' % s), (x1, bottom)]
    return [C(cx, hy, hr, fill=True), PL(*body), FO(PG(*body))]


def doc(x0=5, y0=3, x1=19, y1=21, f=5):
    """Document with a folded corner."""
    return [PG((x0, y0, 'c'), (x1 - f, y0), (x1, y0 + f), (x1, y1, 'c'), (x0, y1, 'c')), PL((x1 - f, y0), (x1 - f, y0 + f, 'm'), (x1, y0 + f))]


def shield(cx=12, top=3, w=15, h=18, **kw):
    x0, x1 = cx - w / 2, cx + w / 2
    sh = top + h * 0.15; mid = top + h * 0.47; bot = top + h
    return P(('M', cx, top, 'm'), ('L', x1, sh, 'm'), ('L', x1, mid), ('Q', x1, top + h * 0.83, cx, bot), ('Q', x0, top + h * 0.83, x0, mid),
             ('L', x0, sh, 'm'), closed=True, **kw)


def house(x0=3.5, x1=20.5, eave=10.5, apex=3.5, base=20.5):
    cx = (x0 + x1) / 2
    return PG((x0, eave, 'm'), (cx, apex, 'm'), (x1, eave, 'm'), (x1, base, 'c'), (x0, base, 'c'))


def bubble(x0, y0, x1, y1, tail_x=8.5, tail_tip=20):
    """Speech bubble with a tail running down the left edge."""
    return PG((x0, y0, 'c'), (x1, y0, 'c'), (x1, y1, 'c'), (tail_x, y1, 'm'), (x0, tail_tip, 'm'))


def calendar_frame():
    return [R(3.5, 5, 17, 15.5), L(3.5, 10, 20.5, 10), L(8, 3, 8, 7), L(16, 3, 16, 7)]


def cart_lines():
    return [PL((3, 3.5), (5, 3.5, 'm'), (7.5, 15.5, 'm'), (18, 15.5, 'm'), (20.5, 7.5, 'm'), (5.83, 7.5)),
            FO(PG((5.83, 7.5), (20.5, 7.5), (18, 15.5), (7.5, 15.5))), C(9, 19.5, 1.5, fill=False), C(17, 19.5, 1.5, fill=False)]


def hand_pg():
    return PG((6, 13.5, 'm'), (10, 13.5, 'm'), (13.5, 16.5, 'm'), (15.5, 16.5, 'm'), (19.25, 12.75, 's1'), (21, 14.5, 's1'), (15, 20.5, 'm'), (6, 20.5))


def leaf_shape(bx, by, tx, ty, bulge=0.42, **kw):
    """Leaf from base (bx,by) to tip (tx,ty): two quadratic sides."""
    mx, my = (bx + tx) / 2, (by + ty) / 2
    dx, dy = tx - bx, ty - by
    nx, ny = -dy * bulge, dx * bulge
    return P(('M', bx, by, 'x'), ('Q', mx + nx, my + ny, tx, ty, 'x'), ('Q', mx - nx, my - ny, bx, by), closed=True, **kw)


def wheat_stalk(cx=12, base=21, top=3):
    """Ear of wheat: a stem with open grains (V strokes) and a top grain — legible down to 16 px."""
    prims = [L(cx, base, cx, top + 3.5)]
    for y in (top + 7, top + 11.5):
        prims.append(P(('M', cx - 4, y - 2.5), ('Q', cx - 3.25, y + 1.25, cx, y + 2.25, 'x'), ('Q', cx + 3.25, y + 1.25, cx + 4, y - 2.5)))
    prims.append(P(('M', cx, top + 4.75, 'x'), ('Q', cx - 2.25, top + 2.5, cx, top, 'x'), ('Q', cx + 2.25, top + 2.5, cx, top + 4.75), closed=True))
    return prims


# =====================================================================================================
#  UI — interface & navigation
# =====================================================================================================
icon('menu', 'ui', [L(4, 6, 20, 6), L(4, 12, 20, 12), L(4, 18, 20, 18)], 'navigation hamburger bars', ['hamburger', 'bars'])
icon('close', 'ui', [L(6, 6, 18, 18), L(18, 6, 6, 18)], 'x dismiss cancel', ['x', 'dismiss', 'cancel'])
icon('search', 'ui', [C(10.5, 10.5, 6.5), L(15.25, 15.25, 20, 20)], 'find magnifier lookup', ['find', 'magnifier'])
ARROW = [L(4, 12, 19, 12), PL((13.5, 6.5), (19.5, 12, 'x'), (13.5, 17.5))]
icon('arrow-right', 'ui', ARROW, 'next forward go', ['next', 'forward'])
icon('arrow-left', 'ui', T(ARROW, 180), 'back previous', ['back', 'previous'])
icon('arrow-up', 'ui', T(ARROW, -90), 'up top', [])
icon('arrow-down', 'ui', T(ARROW, 90), 'down scroll', [])
icon('arrow-up-right', 'ui', [L(6, 18, 17.5, 6.5), PL((8.5, 6.5), (17.5, 6.5, 'x'), (17.5, 15.5))], 'diagonal outbound', ['arrow-diagonal'])
CHEV = [PL((9, 5.5), (15.5, 12, 'x'), (9, 18.5))]
icon('chevron-right', 'ui', CHEV, 'next more', [])
icon('chevron-left', 'ui', T(CHEV, 180), 'back previous', [])
icon('chevron-up', 'ui', T(CHEV, -90), 'collapse less', [])
icon('chevron-down', 'ui', T(CHEV, 90), 'expand dropdown open', ['dropdown', 'expand'])
icon('plus', 'ui', [L(12, 5, 12, 19), L(5, 12, 19, 12)], 'add new create', ['add', 'new'])
icon('minus', 'ui', [L(5, 12, 19, 12)], 'remove subtract collapse', ['subtract'])
icon('check', 'ui', [PL((4.5, 12.5), (9.5, 17.5), (19.5, 7))], 'done ok confirm tick yes honest quality', ['tick', 'done', 'ok'])
icon('more-horizontal', 'ui', [D(5.5, 12, 1.2), D(12, 12, 1.2), D(18.5, 12, 1.2)], 'more options ellipsis', ['more', 'ellipsis', 'dots'])
icon('more-vertical', 'ui', [D(12, 5.5, 1.2), D(12, 12, 1.2), D(12, 18.5, 1.2)], 'more options kebab', ['kebab', 'dots-vertical'])
icon('external', 'ui', [PL((11, 4.5), (4.5, 4.5, 'c'), (4.5, 19.5, 'c'), (19.5, 19.5, 'c'), (19.5, 13)), L(11.5, 12.5, 19.5, 4.5), PL((14, 4.5), (19.5, 4.5, 'x'), (19.5, 10)),
                        FO(PG((4.5, 4.5), (11, 4.5), (11, 12.5), (19.5, 13), (19.5, 19.5), (4.5, 19.5)))], 'external link open new window outbound', ['external-link', 'open-external'])
TRAY = PL((4, 14.5), (4, 19.5, 'c'), (20, 19.5, 'c'), (20, 14.5))
icon('download', 'ui', [L(12, 3.5, 12, 14.5), PL((7, 9.5), (12, 14.5, 'x'), (17, 9.5)), TRAY], 'save get file', ['save'])
icon('upload', 'ui', [L(12, 14.5, 12, 3.5), PL((7, 8.5), (12, 3.5, 'x'), (17, 8.5)), TRAY], 'send file attach', [])
SH = [(17.5, 5.5), (6.5, 12), (17.5, 18.5)]
icon('share', 'ui', [C(*SH[0], 2.75, fill=True), C(*SH[1], 2.75, fill=True), C(*SH[2], 2.75, fill=True), link(SH[1], SH[0], 2.75, 2.75), link(SH[1], SH[2], 2.75, 2.75)], 'share send network', ['share-nodes'])
icon('link', 'ui', T([P(('M', 10.5, 8), ('L', 6.5, 8), ('A', 6.5, 12, 4, 270, 90), ('L', 10.5, 16)),
                       P(('M', 13.5, 8), ('L', 17.5, 8), ('A', 17.5, 12, 4, -90, 90), ('L', 13.5, 16)), L(8.5, 12, 15.5, 12)], -45), 'chain url hyperlink together partnership', ['chain', 'url', 'hyperlink'])
icon('copy', 'ui', [R(9, 9, 11.5, 11.5), PL((15, 9), (15, 4, 'm'), (4, 4, 'm'), (4, 15, 'm'), (9, 15))], 'duplicate clone', ['duplicate', 'clone'])
icon('edit', 'ui', [PG((4, 20, 'x'), (5, 15.5), (15.5, 5, 'm'), (19, 8.5, 'm'), (8.5, 19)), L(13, 7.5, 16.5, 11)], 'pencil write modify', ['pencil', 'write'])
icon('trash', 'ui', [L(4, 6.5, 20, 6.5), PL((9, 6.5), (9, 4, 'm'), (15, 4, 'm'), (15, 6.5)), PL((6, 6.5), (7, 20.5, 'c'), (17, 20.5, 'c'), (18, 6.5)),
                     L(10, 10.5, 10, 16.5), L(14, 10.5, 14, 16.5), FO(PG((6, 6.5), (7, 20.5, 'c'), (17, 20.5, 'c'), (18, 6.5)))], 'delete remove bin', ['delete', 'bin', 'remove'])
EYE = P(('M', 3, 12), ('C', 6.5, 6, 17.5, 6, 21, 12), ('C', 17.5, 18, 6.5, 18, 3, 12), closed=True)
icon('eye', 'ui', [EYE, C(12, 12, 3)], 'view visible show clarity candour honest look', ['view', 'show', 'visible'])
icon('eye-off', 'ui', [EYE, C(12, 12, 3, fill=False), L(4, 4, 20, 20)], 'hide hidden invisible', ['hide', 'hidden'])
icon('lock', 'ui', [R(5, 11, 14, 10), P(('M', 8, 11), ('L', 8, 8), ('A', 12, 8, 4, 180, 360), ('L', 16, 11)), L(12, 14.5, 12, 17.5)], 'secure private password closed', ['locked', 'private'])
icon('unlock', 'ui', [R(5, 11, 14, 10), P(('M', 8, 11), ('L', 8, 7.5), ('A', 12, 7.5, 4, 180, 335)), L(12, 14.5, 12, 17.5)], 'open unlocked access transparent', ['open', 'unlocked'])
icon('settings', 'ui', [gear(12, 12, 9, 6.75, 8, 3.0, fill=True), C(12, 12, 2.75)], 'gear cog preferences options operations', ['gear', 'cog', 'preferences'])
icon('filter', 'ui', [PG((4.5, 4.5, 'm'), (19.5, 4.5, 'm'), (14, 12, 'm'), (14, 20, 'm'), (10, 18, 'm'), (10, 12, 'm'))], 'funnel refine', ['funnel'])
icon('sort', 'ui', [L(7.5, 4, 7.5, 20), PL((4, 16.5), (7.5, 20, 'x'), (11, 16.5)), L(16.5, 20, 16.5, 4), PL((13, 7.5), (16.5, 4, 'x'), (20, 7.5))], 'order arrange arrows', ['arrows-up-down', 'order'])
icon('grid', 'ui', [R(4, 4, 6.5, 6.5, fill=True), R(13.5, 4, 6.5, 6.5, fill=True), R(4, 13.5, 6.5, 6.5, fill=True), R(13.5, 13.5, 6.5, 6.5, fill=True)], 'tiles layout cards view', ['grid-view', 'tiles'])
icon('list', 'ui', [L(9, 6, 20, 6), L(9, 12, 20, 12), L(9, 18, 20, 18), D(4.75, 6), D(4.75, 12), D(4.75, 18)], 'rows bullets layout', ['list-view', 'bullets'])
icon('refresh', 'ui', [P(('A', 12, 12, 8.5, 5, 292), ('L', 19.5, 7.5)), PL((19.5, 3), (19.5, 7.5, 'x'), (15, 7.5))], 'reload sync rotate update', ['reload', 'sync', 'rotate'])
icon('log-in', 'ui', [PL((14, 4), (19, 4, 'c'), (19, 20, 'c'), (14, 20)), L(4, 12, 14, 12), PL((10, 8), (14, 12, 'x'), (10, 16))], 'sign in enter login', ['login', 'sign-in'])
icon('log-out', 'ui', [PL((10, 4), (5, 4, 'c'), (5, 20, 'c'), (10, 20)), L(10, 12, 20, 12), PL((16, 8), (20, 12, 'x'), (16, 16))], 'sign out exit logout', ['logout', 'sign-out'])
icon('play', 'ui', [PG((7, 4.5, 'm'), (19.5, 12, 'm'), (7, 19.5, 'm'))], 'start video media', ['start'])
icon('pause', 'ui', [R(6, 4.5, 4, 15, fill=True), R(14, 4.5, 4, 15, fill=True)], 'hold media', [])
icon('info', 'ui', [C(12, 12, 9), L(12, 11, 12, 16.5), D(12, 7.75)], 'information about details help', ['information'])
icon('warning', 'ui', [PG((12, 4.5, 'm'), (20.5, 19.5, 'm'), (3.5, 19.5, 'm')), L(12, 10, 12, 14), D(12, 16.75)], 'alert caution attention', ['alert', 'caution', 'alert-triangle'])
icon('error', 'ui', [C(12, 12, 9), L(12, 7.5, 12, 12.5), D(12, 16.25)], 'danger failed invalid stop', ['danger', 'alert-circle'])
icon('success', 'ui', [C(12, 12, 9), PL((8, 12.5), (11, 15.5), (16.5, 9))], 'done complete verified ok', ['check-circle', 'verified'])
icon('help', 'ui', [C(12, 12, 9), P(('A', 12, 9.5, 2.75, 180, 400), ('L', 12, 12.75), ('L', 12, 14)), D(12, 17)], 'question faq support', ['question', 'faq'])
icon('bell', 'ui', [P(('M', 5, 17.5, 'm'), ('L', 6.5, 15.5, 'm'), ('L', 6.5, 10.5), ('A', 12, 10.5, 5.5, 180, 360), ('L', 17.5, 15.5, 'm'), ('L', 19, 17.5, 'm'), closed=True),
                    A(12, 18.5, 2.25, 25, 155)], 'notification alert reminder', ['notification', 'notifications'])
def _moon():
    O, R_ = (12.0, 12.0), 8.5; I, r = (16.5, 7.5), 6.5
    dx, dy = I[0] - O[0], I[1] - O[1]; d = math.hypot(dx, dy)
    a = (R_ * R_ - r * r + d * d) / (2 * d); h = math.sqrt(R_ * R_ - a * a)
    bx, by = O[0] + a * dx / d, O[1] + a * dy / d
    pa = (bx - h * dy / d, by + h * dx / d); pb = (bx + h * dy / d, by - h * dx / d)
    ang = lambda c, p: math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))
    a0, a1 = ang(O, pa), ang(O, pb)
    if a1 < a0: a1 += 360
    i0, i1 = ang(I, pb), ang(I, pa)
    if i1 > i0: i1 -= 360
    return P(('A', O[0], O[1], R_, a0, a1), ('A', I[0], I[1], r, i0, i1), closed=True)
icon('sun', 'ui', [C(12, 12, 4)] + [L(12 + 6.5 * math.cos(a * D2R), 12 + 6.5 * math.sin(a * D2R), 12 + 9 * math.cos(a * D2R), 12 + 9 * math.sin(a * D2R)) for a in range(0, 360, 45)],
     'light mode day summer terrace weather daylight', ['light-mode', 'summer', 'terrace', 'weather', 'daylight', 'day'])
icon('moon', 'ui', [_moon()], 'dark mode night evening', ['dark-mode', 'night'])
icon('home', 'ui', [house(), PL((9.5, 20.5), (9.5, 15, 'm'), (14.5, 15, 'm'), (14.5, 20.5))], 'house start main', ['house'])

# =====================================================================================================
#  CORE — the shared vocabulary every brand gets
# =====================================================================================================
icon('mail', 'core', [R(3, 5, 18, 14), PL((3.5, 6.5), (12, 13), (20.5, 6.5))], 'email envelope message newsletter contact', ['email', 'envelope', 'newsletter'])
icon('phone', 'core', [P(('M', 6.5, 3.5, 's1.5'), ('L', 10.5, 7.5, 's1.2'), ('L', 8.25, 9.75, 'm'), ('Q', 10.5, 13.5, 14.25, 15.75, 'm'), ('L', 16.5, 13.5, 's1.2'),
                            ('L', 20.5, 17.5, 's1.5'), ('L', 17.5, 20.5, 's1.5'), ('L', 14, 20.5, 'm'), ('Q', 6.25, 18, 3.5, 10, 'm'), ('L', 3.5, 6.5, 's1.5'), closed=True)],
     'call telephone contact', ['call', 'telephone', 'tel'])
icon('pin', 'core', [pin(12, 9.5, 6.5, 20.5), C(12, 9.5, 2.5)], 'location place map address venue local', ['location', 'map-pin', 'place', 'address'])
icon('calendar', 'core', calendar_frame(), 'date schedule day event', ['date', 'event', 'schedule'])
icon('clock', 'core', [C(12, 12, 9), PL((12, 7), (12, 12), (15.5, 14))], 'time hour opening hours access', ['time', 'hours'])
icon('user', 'core', bust(12, 7.5, 4, 5, 19, 15.5, 20.5), 'person account profile member', ['person', 'account', 'profile'])
icon('users', 'core', [bust(9, 8, 3.25, 3, 15, 16.5, 20.5, 3.5), C(16.5, 7, 2.75, fill=False), PL((16, 13.5), (21, 13.5, 's3'), (21, 20.5))], 'people team group members collaboration family',
     ['people', 'team', 'group'])
icon('globe', 'core', [C(12, 12, 9), E(12, 12, 4, 9), L(3, 12, 21, 12)], 'world web international website', ['world', 'web', 'website'])
icon('language', 'core', [L(3.5, 5.5, 13.5, 5.5), L(8.5, 3, 8.5, 5.5), P(('M', 11.5, 5.5), ('Q', 10.5, 11.5, 4.5, 14.5)), L(6.5, 9, 12, 14), PL((12.5, 20.5), (16.5, 11.5, 'x'), (20.5, 20.5)), L(14, 17.5, 19, 17.5)],
     'translate languages multilingual', ['translate', 'languages'])
icon('chat', 'core', [bubble(3.5, 4.5, 20.5, 16.5)], 'message conversation speech talk', ['chat-bubble', 'speech'])
icon('heart', 'core', [heart(12, 4, 17, 20.25)], 'love like favourite kindness generous care', ['love', 'favourite', 'favorite'])
icon('star', 'core', [PG(*star_pts(12, 12.75, 9.25, 4, 5))], 'favourite rating highlight limited featured', ['rating', 'featured'])
icon('bookmark', 'core', [PG((6, 3.5, 'c'), (18, 3.5, 'c'), (18, 20.5, 'm'), (12, 16, 'm'), (6, 20.5, 'm'))], 'save keep later', ['saved'])
icon('cart', 'core', cart_lines(), 'shopping cart basket checkout', ['shopping-cart'])
icon('bag', 'core', [R(4, 8, 16, 12.5), P(('M', 8.5, 8), ('L', 8.5, 7), ('A', 12, 7, 3.5, 180, 360), ('L', 15.5, 8))], 'shopping bag shop essentials', ['shopping-bag', 'shop'])
icon('image', 'core', [R(3, 4, 18, 16), C(8.5, 9.5, 2, fill=False), PL((21, 14.5), (16.5, 10.5, 'm'), (7, 20))], 'photo picture gallery media', ['photo', 'picture', 'gallery'])
icon('file', 'core', doc() + [L(8.5, 12.5, 15.5, 12.5), L(8.5, 16, 13.5, 16)], 'document page paper text', ['document', 'doc', 'page'])
icon('folder', 'core', [PG((3, 5, 'c'), (9.5, 5, 'm'), (11.5, 7.5, 'm'), (21, 7.5, 'c'), (21, 19, 'c'), (3, 19, 'c'))], 'directory projects files', ['directory'])
icon('spark', 'core', [P(('M', 10.5, 6, 'x'), ('Q', 11.5, 12.5, 18, 13.5, 'x'), ('Q', 11.5, 14.5, 10.5, 21, 'x'), ('Q', 9.5, 14.5, 3, 13.5, 'x'), ('Q', 9.5, 12.5, 10.5, 6, 'x'), closed=True),
                      L(18.5, 3, 18.5, 8), L(16, 5.5, 21, 5.5)], 'sparkle magic new craft joy curiosity ai', ['sparkle', 'sparkles', 'magic'])
icon('award', 'core', [C(12, 9, 6), PL((8.5, 13.75), (7.25, 20.25, 'm'), (12, 18, 'm'), (16.75, 20.25, 'm'), (15.5, 13.75))], 'medal badge quality expertise prize', ['medal', 'badge'])
icon('bolt', 'core', [PG((13, 3, 'm'), (5, 13.5, 'm'), (11.5, 13.5, 'm'), (10.5, 21, 'm'), (19, 10.5, 'm'), (12.5, 10.5, 'm'))], 'lightning energy power speed fast flash', ['lightning', 'flash', 'energy'])
icon('shield', 'core', [shield()], 'protection safety trust secure', ['protection', 'trust'])
icon('compass', 'core', [C(12, 12, 9), PG((15.5, 8.5, 'm'), (13.6, 13.6, 'm'), (8.5, 15.5, 'm'), (10.4, 10.4, 'm'), fill=True)], 'direction strategy explore navigate', ['direction', 'explore'])
icon('flag', 'core', [L(5, 3.5, 5, 21), PG((5, 4, 'm'), (19, 4, 'm'), (15.5, 9, 'm'), (19, 14, 'm'), (5, 14))], 'milestone goal report country', ['milestone'])
icon('target', 'core', [C(12, 12, 9), C(12, 12, 5.25), D(12, 12, 1.25)], 'goal aim focus objective', ['goal', 'aim'])
icon('idea', 'core', [P(('M', 9.25, 17, 'm'), ('L', 7.2, 13.5), ('A', 12, 9.5, 6.25, 140, 400), ('L', 14.75, 17, 'm'), closed=True), L(9.5, 20.25, 14.5, 20.25)],
     'lightbulb innovation insight inspiration', ['lightbulb', 'bulb', 'innovation'])
icon('quote', 'core', [R(4, 6, 6.5, 6, fill=True), P(('M', 10.5, 11), ('Q', 10.5, 17, 5.5, 18.5)), R(13.5, 6, 6.5, 6, fill=True), P(('M', 20, 11), ('Q', 20, 17, 15, 18.5))],
     'testimonial citation blockquote', ['testimonial', 'blockquote'])

# =====================================================================================================
#  EDUCATION
# =====================================================================================================
icon('education', 'education', [PG((12, 4.25, 'm'), (20.25, 8.5, 'm'), (12, 12.75, 'm'), (3.75, 8.5, 'm')), P(('M', 7, 10.25), ('L', 7, 15), ('Q', 12, 18.5, 17, 15), ('L', 17, 10.25)),
                                 L(20.25, 8.5, 20.25, 14)], 'graduation learning school course training educators', ['graduation', 'learning', 'mortarboard'])
icon('book-open', 'education', [P(('M', 12, 6.5), ('Q', 8, 4, 3, 4.5, 'm'), ('L', 3, 18, 'm'), ('Q', 8, 17.5, 12, 20), closed=True),
                                P(('M', 12, 6.5), ('Q', 16, 4, 21, 4.5, 'm'), ('L', 21, 18, 'm'), ('Q', 16, 17.5, 12, 20), closed=True)], 'reading read library knowledge', ['reading', 'read'])
icon('book', 'education', [R(5, 3, 14, 18), L(8.5, 3, 8.5, 21), L(11.5, 7.5, 16, 7.5), L(11.5, 10.5, 14.5, 10.5)], 'notebook manual guide journal', ['notebook', 'manual'])
icon('backpack', 'education', [PG((5, 7, 's3.5'), (19, 7, 's3.5'), (19, 21, 'c'), (5, 21, 'c')), PL((9.5, 7), (9.5, 4, 'm'), (14.5, 4, 'm'), (14.5, 7)),
                               PL((8, 21), (8, 14.5, 'm'), (16, 14.5, 'm'), (16, 21)), L(10.5, 17.5, 13.5, 17.5)], 'school bag student kids juniors', ['schoolbag'])
icon('school', 'education', [PG((7, 20.5, 'c'), (7, 9, 'm'), (12, 5, 'm'), (17, 9, 'm'), (17, 20.5, 'c')), PL((7, 12), (3.5, 12, 'm'), (3.5, 20.5, 'c'), (20.5, 20.5, 'c'), (20.5, 12, 'm'), (17, 12)),
                             PL((10.5, 20.5), (10.5, 16.5, 'm'), (13.5, 16.5, 'm'), (13.5, 20.5)), C(12, 11, 1.5, fill=False)], 'building campus college', ['campus'])
icon('certificate', 'education', [PL((13, 17), (3, 17, 'c'), (3, 4, 'c'), (21, 4, 'c'), (21, 12)), L(6.5, 8, 17.5, 8), L(6.5, 11.5, 12, 11.5), C(16.5, 15, 2.75, fill=True),
                                  PL((15, 17.4), (14.75, 20.5, 'm'), (16.5, 19.5, 'm'), (18.25, 20.5, 'm'), (18, 17.4))], 'diploma credential accreditation', ['diploma'])
icon('atom', 'education', [E(12, 12, 9, 3.5, 0, fill=False), E(12, 12, 9, 3.5, 60, fill=False), E(12, 12, 9, 3.5, 120, fill=False), D(12, 12, 1.2)], 'science stem physics', ['science-atom', 'stem'])

# =====================================================================================================
#  CULTURE
# =====================================================================================================
icon('palette', 'culture', [P(('A', 12, 12, 9, 75, 382), ('Q', 17, 14.25, 16.75, 16.75), ('Q', 16.25, 19.25, 14.33, 20.69), closed=True),
                            D(7.5, 11.5, 1.1), D(9.5, 7, 1.1), D(14.25, 6.5, 1.1), D(17.25, 9.75, 1.1)], 'art paint colour creativity design', ['paint', 'art'])
icon('music', 'culture', [C(6.5, 17.5, 2.5, fill=True), C(17, 15.5, 2.5, fill=True), PL((9, 17.5), (9, 5.5, 'm'), (19.5, 3.5, 'm'), (19.5, 15.5))], 'note song concert sound', ['note', 'concert'])
icon('ticket', 'culture', [P(('M', 3, 6, 'c'), ('L', 21, 6, 'c'), ('L', 21, 10), ('A', 21, 12, 2, 270, 90), ('L', 21, 18, 'c'), ('L', 3, 18, 'c'), ('L', 3, 14), ('A', 3, 12, 2, 90, -90), closed=True),
                           L(15, 7.75, 15, 9), L(15, 11.4, 15, 12.6), L(15, 15, 15, 16.25)], 'event admission entry show', ['admission', 'tickets'])
icon('film', 'culture', [R(3, 4, 18, 16), L(7, 4, 7, 20), L(17, 4, 17, 20), L(3, 9, 7, 9), L(3, 15, 7, 15), L(17, 9, 21, 9), L(17, 15, 21, 15)], 'movie cinema video screening', ['movie', 'cinema'])
icon('brush', 'culture', [L(20, 4, 14, 10), PG((12.25, 8.25, 'm'), (15.75, 11.75, 'm'), (13.25, 14.25), (9.75, 10.75)),
                          P(('M', 9.75, 10.75), ('Q', 5.5, 13, 4.75, 16.5), ('L', 3.5, 20.5, 'x'), ('L', 7.5, 19.25), ('Q', 11, 18.5, 13.25, 14.25), closed=True)], 'paintbrush art create design', ['paintbrush'])
_drape = [P(('M', 3.5, 4), ('L', 3.5, 20.5, 'm'), ('L', 7, 20.5, 'm'), ('L', 6, 13.5), ('Q', 9.5, 10, 10.5, 4), closed=True, fill=True), L(3.5, 13.5, 6, 13.5)]
icon('theater', 'culture', [L(3, 4, 21, 4)] + _drape + T(_drape, flipx=True) + [P(*bumps(10.5, 13.5, 4, 1, up=False))], 'stage curtain performance drama', ['stage', 'theatre'])
icon('puzzle', 'culture', [P(('M', 4, 7.5, 'c'), ('L', 8.21, 7.5), ('A', 10.5, 6.5, 2.5, 156.4, 383.6), ('L', 17, 7.5, 'c'), ('L', 17, 11.71), ('A', 18, 14, 2.5, 246.4, 473.6),
                            ('L', 17, 20.5, 'c'), ('L', 4, 20.5, 'c'), closed=True)], 'game play piece logic', ['game', 'jigsaw'])

# =====================================================================================================
#  PEOPLE
# =====================================================================================================
icon('user-plus', 'people', [bust(9.5, 8, 3.75, 3, 16, 16, 20.5, 3.5), L(18.5, 6, 18.5, 11), L(16, 8.5, 21, 8.5)], 'add person invite join', ['add-user', 'invite'])
icon('user-check', 'people', [bust(9.5, 8, 3.75, 3, 16, 16, 20.5, 3.5), PL((16, 8.5), (18, 10.5), (21, 7))], 'verified member approved', ['verified-user'])
icon('user-circle', 'people', [C(12, 12, 9), C(12, 10, 3.25, fill=True), PL((6.75, 19.25), (6.75, 17.5, 's2'), (17.25, 17.5, 's2'), (17.25, 19.25))], 'profile avatar account', ['avatar'])
_hs = [P(('M', 11, 17), ('L', 13, 19), ('A', 14.5, 17.5, 2.121, 135, -45)),
       P(('M', 14, 14), ('L', 16.5, 16.5), ('A', 18, 15, 2.121, 135, -45), ('L', 15.62, 9.62), ('A', 13.5, 11.74, 3, -45, -135), ('L', 10.5, 10.5), ('A', 9, 9, 2.121, 45, -135),
         ('L', 10.31, 4.69), ('A', 14.4, 8.79, 5.79, -135, -59), ('L', 21, 4.25)),
       PL((21, 3), (22, 14, 'm'), (20, 14)), P(('M', 3, 3), ('L', 2, 14, 'm'), ('L', 8.5, 20.5), ('A', 10, 19, 2.121, 135, -45)), L(3, 4, 11, 4)]
icon('handshake', 'people', T(_hs, s=0.88), 'agreement partnership deal together', ['agreement', 'deal'])
icon('hand-raised', 'people', [P(('M', 7, 13), ('L', 7, 16), ('Q', 7, 21, 12, 21), ('L', 13, 21), ('Q', 18, 21, 18, 16), ('L', 18, 9.5)), L(9.5, 12, 9.5, 5.5), L(12.5, 11.5, 12.5, 3.5),
                               L(15.5, 12, 15.5, 5), L(18, 12, 18, 9), PL((7, 16), (4.5, 12.5, 'm'), (4.5, 11.5))], 'volunteer hand join vote stop', ['volunteer', 'hand'])
icon('id-card', 'people', [R(3, 5, 18, 14), C(8.5, 10.5, 2.25, fill=True), PL((5.5, 16), (5.5, 15, 's1.5'), (11.5, 15, 's1.5'), (11.5, 16)), L(14, 10, 18, 10), L(14, 13.5, 17, 13.5)],
     'identity badge member card', ['badge-id', 'identity'])
icon('smile', 'people', [C(12, 12, 9), A(12, 12, 5, 25, 155), D(9, 9.5), D(15, 9.5)], 'happy joy play fun friendly', ['happy', 'face'])

# =====================================================================================================
#  TIME
# =====================================================================================================
icon('hourglass', 'time', [L(6, 3.5, 18, 3.5), L(6, 20.5, 18, 20.5), PL((7.5, 3.5), (7.5, 7, 'm'), (12, 12, 'm'), (7.5, 17, 'm'), (7.5, 20.5)),
                           PL((16.5, 3.5), (16.5, 7, 'm'), (12, 12, 'm'), (16.5, 17, 'm'), (16.5, 20.5)), FO(PG((9, 20.5), (12, 17), (15, 20.5)))], 'wait duration timer', ['wait'])
icon('timer', 'time', [C(12, 13.5, 7.5), L(10, 3, 14, 3), L(12, 3, 12, 6), PL((12, 13.5), (14.75, 10.75)), L(18, 6.5, 19.5, 5)], 'stopwatch countdown duration', ['stopwatch'])
icon('alarm', 'time', [C(12, 13, 7.5), PL((12, 9.5), (12, 13), (14.5, 14.5)), L(3.5, 6, 6.5, 3), L(17.5, 3, 20.5, 6), L(7, 18.5, 5.5, 20.5), L(17, 18.5, 18.5, 20.5)], 'alarm clock wake reminder', ['alarm-clock'])
icon('history', 'time', [P(('A', 12, 12, 8.75, 180, -135), ('L', 3.5, 8)), PL((3.5, 3.5), (3.5, 8, 'x'), (8, 8)), PL((12, 7.5), (12, 12), (15, 13.75))], 'past recent archive undo', ['recent', 'archive'])
icon('calendar-check', 'time', calendar_frame() + [PL((8.5, 15), (11, 17.5), (15.5, 13))], 'booked confirmed appointment reservation', ['booked', 'appointment', 'reservation'])
icon('calendar-clock', 'time', [PL((10.5, 20.5), (3.5, 20.5, 'c'), (3.5, 5, 'c'), (20.5, 5, 'c'), (20.5, 11)), L(3.5, 10, 20.5, 10), L(8, 3, 8, 7), L(16, 3, 16, 7),
                                C(17, 17, 4, fill=True), PL((17, 15), (17, 17), (18.5, 18))], 'schedule timetable opening', ['timetable', 'schedule-time'])
icon('repeat', 'time', [PL((3.5, 11.5), (3.5, 7, 's3'), (20, 7)), PL((16.5, 3.5), (20, 7, 'x'), (16.5, 10.5)), PL((20.5, 12.5), (20.5, 17, 's3'), (4, 17)), PL((7.5, 13.5), (4, 17, 'x'), (7.5, 20.5))],
     'recurring loop again weekly', ['recurring', 'loop'])

# =====================================================================================================
#  LOCATION
# =====================================================================================================
icon('map', 'location', [PG((3, 6, 'm'), (9, 3.5, 'm'), (15, 6, 'm'), (21, 3.5, 'm'), (21, 18, 'm'), (15, 20.5, 'm'), (9, 18, 'm'), (3, 20.5, 'm')), L(9, 3.5, 9, 18), L(15, 6, 15, 20.5)],
     'map area region directions', ['area'])
icon('navigation', 'location', [PG((12, 3, 'm'), (19.5, 20, 'm'), (12, 16, 'm'), (4.5, 20, 'm'))], 'direction pointer gps arrow', ['gps', 'nav-arrow'])
icon('route', 'location', [C(5.5, 18.5, 2.5, fill=True), C(18.5, 5.5, 2.5, fill=True), P(('M', 8, 18.5), ('L', 16.5, 18.5), ('A', 16.5, 15.25, 3.25, 90, -90), ('L', 7.5, 12), ('A', 7.5, 8.75, 3.25, 90, 270), ('L', 16, 5.5))],
     'path journey trip itinerary', ['journey', 'path'])
icon('signpost', 'location', [L(12, 3, 12, 5), L(12, 9.5, 12, 12), L(12, 16.5, 12, 21), PG((5, 5, 'c'), (17, 5), (19.5, 7.25, 'm'), (17, 9.5), (5, 9.5, 'c')),
                              PG((19, 12, 'c'), (7, 12), (4.5, 14.25, 'm'), (7, 16.5), (19, 16.5, 'c'))], 'directions wayfinding sign', ['wayfinding', 'directions'])
icon('building', 'location', [R(5, 3, 14, 18), D(9.5, 7), D(14.5, 7), D(9.5, 10.5), D(14.5, 10.5), D(9.5, 14), D(14.5, 14), PL((10.25, 21), (10.25, 17.5, 'm'), (13.75, 17.5, 'm'), (13.75, 21))],
     'office company headquarters', ['office', 'company'])
icon('parking', 'location', [R(3.5, 3.5, 17, 17), P(('M', 9.5, 17), ('L', 9.5, 7), ('L', 13, 7), ('A', 13, 10.25, 3.25, 270, 450), ('L', 9.5, 13.5))], 'car park parking lot', ['car-park'])
icon('crosshair', 'location', [C(12, 12, 7), C(12, 12, 2.5, fill=False), L(12, 3, 12, 5), L(12, 19, 12, 21), L(3, 12, 5, 12), L(19, 12, 21, 12)], 'locate current position gps', ['locate', 'my-location'])

# =====================================================================================================
#  ACCESSIBILITY
# =====================================================================================================
icon('accessibility', 'accessibility', [C(12, 12, 9), D(12, 7, 1.35), L(7.5, 10, 16.5, 10), L(12, 10, 12, 14), PL((9, 18), (12, 14), (15, 18))], 'access inclusive universal a11y', ['a11y', 'universal-access'])
icon('wheelchair', 'accessibility', [C(10, 5, 1.75, fill=True), PL((10.5, 8.5), (11, 14, 'm'), (16, 14, 'm'), (18.5, 19.5, 'm'), (20.5, 19.5)), L(11, 11, 15.5, 11), A(10, 15.5, 5.5, -15, 255)],
     'accessible step-free mobility', ['accessible', 'step-free'])
icon('ear', 'accessibility', [P(('M', 6.5, 9), ('A', 12.5, 9, 6, 180, 360), ('C', 18.5, 14.5, 13, 14.5, 13, 18), ('A', 10, 18, 3, 0, 180)),
                              P(('M', 15, 9), ('A', 12.5, 9, 2.5, 0, -180), ('L', 10, 10), ('A', 10, 12, 2, 270, 450))], 'hearing listen audio loop', ['hearing', 'listen'])
icon('contrast', 'accessibility', [C(12, 12, 9, fill=False), SOLID(P(('M', 12, 6), ('A', 12, 12, 6, 270, 450), closed=True))], 'high contrast display theme', ['high-contrast'])
icon('text-size', 'accessibility', [L(3.5, 5, 13.5, 5), L(8.5, 5, 8.5, 19), L(13.5, 11, 20.5, 11), L(17, 11, 17, 19)], 'font size typography larger text', ['font-size', 'type-size'])
icon('captions', 'accessibility', [R(3, 5, 18, 14), L(7, 10.5, 9, 10.5), L(12, 10.5, 17, 10.5), L(7, 14, 12, 14), L(15, 14, 17, 14)], 'subtitles closed captions cc', ['subtitles', 'cc'])
icon('volume', 'accessibility', [PG((4, 9, 'm'), (8, 9, 'm'), (13, 4.5, 'm'), (13, 19.5, 'm'), (8, 15, 'm'), (4, 15, 'm')), A(14, 12, 3.5, -50, 50), A(14, 12, 7, -50, 50)],
     'sound audio speaker listen', ['sound', 'audio', 'speaker'])
icon('braille', 'accessibility', [D(9, 6, 1.4), C(15, 6, 1.5, fill=False), C(9, 12, 1.5, fill=False), D(15, 12, 1.4), D(9, 18, 1.4), C(15, 18, 1.5, fill=False)], 'tactile blind low vision', ['tactile'])

# =====================================================================================================
#  HEALTH
# =====================================================================================================
icon('medical', 'health', [R(3.5, 3.5, 17, 17), L(12, 8, 12, 16), L(8, 12, 16, 12)], 'health clinic medicine cross first aid', ['health', 'clinic', 'medicine'])
icon('stethoscope', 'health', [P(('M', 7, 3.5), ('L', 5, 3.5, 'm'), ('L', 5, 9), ('A', 9, 9, 4, 180, 0), ('L', 13, 3.5, 'm'), ('L', 11, 3.5)),
                               P(('M', 9, 13), ('L', 9, 14.5), ('A', 13.5, 14.5, 4.5, 180, 0), ('L', 18, 12.5)), C(18, 10, 2.5, fill=True)], 'doctor physician checkup family medicine', ['doctor', 'checkup'])
icon('pill', 'health', [capsule(12, 12, 19, 8, -45), L(9.17, 9.17, 14.83, 14.83)], 'medication capsule pharmacy', ['medication', 'capsule', 'pharmacy'])
icon('activity', 'health', [PL((3, 12), (6.5, 12, 'm'), (9, 5, 'm'), (14, 19, 'm'), (16.5, 12, 'm'), (21, 12))], 'pulse heartbeat vitals monitor', ['pulse', 'heartbeat', 'vitals'])
icon('syringe', 'health', [PG((15, 5, 'm'), (19, 9, 'm'), (9, 19, 's1.5'), (5, 15, 's1.5')), L(17, 7, 19.5, 4.5), L(18, 3, 21, 6), L(7, 17, 3.5, 20.5), L(12, 8, 13.5, 9.5), L(10, 10, 11.5, 11.5)],
     'vaccine injection shot', ['vaccine', 'injection'])
icon('thermometer', 'health', [P(('M', 10, 14.38), ('L', 10, 5), ('A', 12, 5, 2, 180, 360), ('L', 14, 14.38), ('A', 12, 17.25, 3.5, -55.1, 235.1), closed=True), L(12, 8.5, 12, 15.5)],
     'temperature fever', ['temperature', 'fever'])
icon('hospital', 'health', [PL((7, 21), (7, 3, 'c'), (17, 3, 'c'), (17, 21)), PL((7, 11), (3.5, 11, 'm'), (3.5, 21, 'c'), (20.5, 21, 'c'), (20.5, 11, 'm'), (17, 11)),
                            L(12, 5.5, 12, 10.5), L(9.5, 8, 14.5, 8), PL((10.5, 21), (10.5, 17, 'm'), (13.5, 17, 'm'), (13.5, 21))], 'clinic building emergency', ['clinic-building'])
icon('tooth', 'health', [P(('M', 7.5, 3.5), ('C', 4, 3.5, 3.75, 7, 4.75, 10), ('C', 5.5, 12.25, 6.25, 13.5, 6.75, 15), ('L', 7.75, 19.5), ('Q', 8.5, 21, 9.5, 19.5, 'm'), ('L', 10.25, 15.5),
                               ('Q', 12, 13.75, 13.75, 15.5), ('L', 14.5, 19.5), ('Q', 15.5, 21, 16.25, 19.5, 'm'), ('L', 17.25, 15), ('C', 17.75, 13.5, 18.5, 12.25, 19.25, 10),
                               ('C', 20.25, 7, 20, 3.5, 16.5, 3.5), ('Q', 14, 3.5, 12, 5), ('Q', 10, 3.5, 7.5, 3.5), closed=True)], 'dental dentist smile teeth', ['dental', 'dentist'])
icon('flask', 'health', [L(8.5, 3, 15.5, 3), PL((10, 3), (10, 9, 'm'), (4.5, 20, 's1.5'), (19.5, 20, 's1.5'), (14, 9, 'm'), (14, 3)), L(7.5, 15, 16.5, 15),
                         FO(PG((7.5, 15), (16.5, 15), (19.5, 20), (4.5, 20)))], 'lab laboratory test science experiment results', ['lab', 'laboratory', 'science', 'experiment'])
icon('bandage', 'health', [capsule(12, 12, 20, 8.5, -45), PG((12, 8.5, 'm'), (15.5, 12, 'm'), (12, 15.5, 'm'), (8.5, 12, 'm'))], 'plaster wound first aid', ['plaster'])

# =====================================================================================================
#  BODY & MOVEMENT
# =====================================================================================================
icon('run', 'body', T([C(14.5, 4.5, 2, fill=True), PL((13.25, 8.25), (10.5, 13.5)), PL((7, 10.5), (9.5, 8.5, 'm'), (13.25, 8.25, 'm'), (15.5, 11, 'm'), (18.5, 11.5)),
                     PL((10.5, 13.5), (14, 15.5, 'm'), (13, 20.5)), PL((10.5, 13.5), (8.5, 17.5, 'm'), (4.5, 18))], dy=0.5, s=0.96), 'move movement exercise physio recovery sport fitness', ['move', 'movement', 'exercise', 'running'])
icon('dumbbell', 'body', [L(7.5, 12, 16.5, 12), R(4.5, 7, 3, 10, 'm', fill=True), R(16.5, 7, 3, 10, 'm', fill=True), L(3, 12, 4.5, 12), L(19.5, 12, 21, 12)], 'gym weights strength training', ['gym', 'weights'])
_bone = P(('M', 7.89, 10.75), ('L', 16.11, 10.75), ('A', 18.5, 9.75, 2.5, 156.4, 424.1), ('A', 18.5, 14.25, 2.5, -64.1, 203.6), ('L', 7.89, 13.25),
          ('A', 5.5, 14.25, 2.5, -23.6, 244.1), ('A', 5.5, 9.75, 2.5, 115.9, 383.6), closed=True)
icon('bone', 'body', [T(_bone, -45, s=0.92)], 'orthopaedic skeleton joint', ['skeleton', 'orthopaedic'])
_foot = [P(('M', 5, 14.5), ('Q', 3, 10, 3.5, 6.75), ('Q', 4.25, 2.5, 7.25, 2.5), ('Q', 10, 2.5, 10, 6), ('Q', 10, 9.5, 8.5, 14.5), closed=True, fill=True), A(6.75, 16.5, 2, -15, 195)]
icon('footprint', 'body', T(_foot + T(_foot, 0, dx=10.5, dy=2.5, flipx=True, cx=6.75), dy=0.25), 'steps walk podiatry gait', ['footprints', 'steps'])
icon('meditation', 'body', [C(12, 5, 2, fill=True), L(12, 9, 12, 13.5), PL((5.5, 14.5), (8.5, 10, 'm'), (15.5, 10, 'm'), (18.5, 14.5)),
                            P(('M', 4, 18.5), ('Q', 8, 14.5, 12, 15.5), ('Q', 16, 14.5, 20, 18.5)), L(6.5, 20, 17.5, 20)], 'yoga mindfulness calm wellbeing', ['yoga', 'mindfulness'])
icon('weight', 'body', [R(3.5, 3.5, 17, 17), A(12, 11.5, 4.5, 200, 340), L(12, 11.5, 13.5, 8.5)], 'scale bodyweight measure', ['scale', 'bodyweight'])
icon('dna', 'body', [P(('M', 7, 3), ('C', 7, 8.5, 17, 7, 17, 12), ('C', 17, 17, 7, 15.5, 7, 21)), P(('M', 17, 3), ('C', 17, 8.5, 7, 7, 7, 12), ('C', 7, 17, 17, 15.5, 17, 21)),
                     L(8.5, 5, 15.5, 5), L(9, 12, 15, 12), L(8.5, 19, 15.5, 19)], 'genetics helix biology', ['genetics', 'helix'])

# =====================================================================================================
#  CARE
# =====================================================================================================
icon('hand-heart', 'care', [heart(14, 3, 9, 10.75), hand_pg(), L(3, 13.5, 3, 20.5)], 'care support compassion donate', ['care', 'support', 'compassion'])
icon('house-heart', 'care', [house(), heart(12, 11, 8.5, 17.5, fill=False)], 'home care shelter family', ['home-care', 'shelter'])
icon('bed', 'care', [L(3, 4, 3, 20.5), PL((3, 11), (21, 11, 'c'), (21, 20.5)), L(3, 17, 21, 17), R(5.5, 7, 5, 4, 'm', fill=True)], 'rest sleep ward stay room', ['sleep', 'rest'])
icon('clipboard', 'care', [PL((8.5, 4.5), (4.5, 4.5, 'c'), (4.5, 21, 'c'), (19.5, 21, 'c'), (19.5, 4.5, 'c'), (15.5, 4.5)), R(8.5, 3, 7, 3.5, 'm', fill=True),
                           L(8, 11, 16, 11), L(8, 14.5, 16, 14.5), L(8, 18, 13, 18)], 'care plan checklist notes record', ['checklist', 'notes'])
icon('first-aid', 'care', [R(3, 6.5, 18, 14), PL((8.5, 6.5), (8.5, 4, 'm'), (15.5, 4, 'm'), (15.5, 6.5)), L(12, 10.5, 12, 16.5), L(9, 13.5, 15, 13.5)], 'kit emergency medical bag', ['first-aid-kit', 'emergency'])
icon('lifebuoy', 'care', [C(12, 12, 9), C(12, 12, 4, fill=False)] + [L(12 + 4 * math.cos(a * D2R), 12 + 4 * math.sin(a * D2R), 12 + 9 * math.cos(a * D2R), 12 + 9 * math.sin(a * D2R)) for a in (45, 135, 225, 315)],
     'support help rescue', ['lifesaver', 'rescue'])
icon('shield-heart', 'care', [shield(), heart(12, 8.5, 8, 15, fill=False)], 'protection wellbeing insurance', ['insurance', 'wellbeing'])

# =====================================================================================================
#  COMMUNICATION
# =====================================================================================================
icon('message', 'communication', [bubble(3.5, 4.5, 20.5, 16.5), L(7.5, 9, 16.5, 9), L(7.5, 12.5, 13.5, 12.5)], 'messages comment text sms', ['messages', 'sms'])
icon('send', 'communication', [PG((21, 3, 'm'), (14.5, 21, 'm'), (11, 13, 'm'), (3, 9.5, 'm')), L(11, 13, 21, 3)], 'paper plane submit send message', ['paper-plane', 'submit'])
icon('megaphone', 'communication', [PG((3.5, 9, 'm'), (8, 9, 'm'), (17, 4.5, 'm'), (17, 19.5, 'm'), (8, 15, 'm'), (3.5, 15, 'm')), PL((5.5, 15), (7, 20.5, 'm'), (10, 20.5, 'm'), (9.5, 16)),
                                    A(17, 12, 4, -35, 35)], 'announce campaign broadcast voice awareness', ['announce', 'campaign', 'loudspeaker'])
icon('at', 'communication', [C(12, 12, 3.75, fill=False), P(('M', 15.75, 8), ('L', 15.75, 13), ('A', 18.25, 13, 2.5, 180, 0), ('L', 20.75, 12), ('A', 12, 12, 8.75, 0, -307))],
     'mention email address handle', ['mention', 'at-sign'])
icon('microphone', 'communication', [capsule(12, 8.5, 11, 6.5, 90), A(12, 10.5, 6.5, 0, 180), L(12, 17, 12, 20.5), L(8.5, 20.5, 15.5, 20.5)], 'mic podcast voice record speak', ['mic', 'podcast'])
icon('video', 'communication', [R(3, 6, 12.5, 12), PG((15.5, 10.5, 'm'), (21, 7, 'm'), (21, 17, 'm'), (15.5, 13.5, 'm'))], 'camera call meeting stream', ['video-call', 'camera-video'])
icon('inbox', 'communication', [PG((3, 13, 'm'), (6, 5, 'm'), (18, 5, 'm'), (21, 13, 'm'), (21, 19, 'c'), (3, 19, 'c')), PL((3, 13), (8, 13), (9.5, 15.5, 'm'), (14.5, 15.5, 'm'), (16, 13), (21, 13))],
     'messages tray received mailbox', ['tray'])
icon('broadcast', 'communication', [D(12, 12, 1.4), A(12, 12, 4, -40, 40), A(12, 12, 4, 140, 220), A(12, 12, 8, -40, 40), A(12, 12, 8, 140, 220)], 'radio signal live stream podcast', ['radio', 'signal', 'live'])

# =====================================================================================================
#  FOOD
# =====================================================================================================
icon('cutlery', 'food', [P(('M', 4.5, 3), ('L', 4.5, 8), ('Q', 4.5, 10.5, 7, 10.5), ('Q', 9.5, 10.5, 9.5, 8), ('L', 9.5, 3)), L(7, 3, 7, 21),
                         P(('M', 18.5, 21), ('L', 18.5, 3.75), ('Q', 14.5, 5.5, 14.5, 10), ('L', 14.5, 13.5, 'm'), ('L', 18.5, 13.5))], 'fork knife dining restaurant eat meal', ['fork', 'utensils', 'dining', 'restaurant'])
icon('bread', 'food', [P(('M', 3.5, 18.5, 'c'), ('L', 3.5, 12.5), ('Q', 3.5, 7, 12, 7), ('Q', 20.5, 7, 20.5, 12.5), ('L', 20.5, 18.5, 'c'), closed=True),
                       L(7.5, 11, 9, 13.5), L(11.25, 10, 12.75, 12.5), L(15, 11, 16.5, 13.5)], 'bakery loaf baked', ['bakery', 'loaf'])
icon('apple', 'food', [P(('M', 12, 7.5), ('C', 9, 5, 4, 5.5, 4, 11.5), ('C', 4, 17, 7.5, 21, 10, 20.5), ('Q', 12, 20, 14, 20.5), ('C', 16.5, 21, 20, 17, 20, 11.5),
                              ('C', 20, 5.5, 15, 5, 12, 7.5), closed=True), PL((12, 7.5), (12.75, 4)), leaf_shape(13.25, 5, 17.5, 3.25, 0.35, fill=False)], 'fruit fresh healthy', ['fruit'])
icon('carrot', 'food', [PG((3.5, 20.5, 'x'), (10.5, 8.5, 's2'), (15.5, 13.5, 's2')), L(7.75, 14.75, 9.75, 16.75), L(9.75, 11.5, 11.25, 13), L(13, 8.5, 13.5, 3.5),
                        L(13.75, 10, 18, 6), L(15.5, 11, 20.5, 10.5)], 'vegetable produce fresh', ['vegetable', 'produce'])
icon('fish', 'food', [P(('M', 7, 12), ('Q', 10, 6, 15, 6), ('Q', 19.5, 6, 21, 12), ('Q', 19.5, 18, 15, 18), ('Q', 10, 18, 7, 12), closed=True),
                      PG((7, 12), (3, 8, 'm'), (3, 16, 'm'), fill=False), D(16.75, 10.5), P(('M', 12.5, 7), ('Q', 11, 12, 12.5, 17))], 'seafood fishmonger catch', ['seafood'])
icon('chef-hat', 'food', [P(('M', 6, 20.5, 'c'), ('L', 6, 14.75), *chain([(6.75, 11.25, 3.5), (12, 8, 4.5), (17.25, 11.25, 3.5)], 110, 70), ('L', 18, 20.5, 'c'), closed=True),
                          L(6, 17, 18, 17)], 'cook kitchen chef menu', ['chef', 'cook', 'kitchen'])
icon('egg', 'food', [P(('M', 12, 3), ('C', 16.5, 3, 19, 10, 19, 14), ('C', 19, 18.5, 16, 21, 12, 21), ('C', 8, 21, 5, 18.5, 5, 14), ('C', 5, 10, 7.5, 3, 12, 3), closed=True)], 'breakfast eggs', ['eggs'])
icon('bowl', 'food', [P(('M', 3, 10.5, 'm'), ('L', 21, 10.5, 'm'), ('Q', 20.5, 18.5, 12, 18.5), ('Q', 3.5, 18.5, 3, 10.5), closed=True), L(9, 20.5, 15, 20.5),
                      P(('M', 9.5, 7.5), ('Q', 8, 5.75, 9.5, 4)), P(('M', 14.5, 7.5), ('Q', 13, 5.75, 14.5, 4))], 'soup salad meal dish', ['soup', 'dish'])

# =====================================================================================================
#  DRINK
# =====================================================================================================
icon('wine-glass', 'drink', [P(('M', 7, 3, 'm'), ('L', 17, 3, 'm'), ('L', 17, 8.5), ('Q', 17, 14, 12, 14), ('Q', 7, 14, 7, 8.5), closed=True), L(7.25, 8, 16.75, 8),
                             L(12, 14, 12, 20.5), L(8, 20.5, 16, 20.5)], 'wine bar glass natural drink', ['glass', 'wine', 'bar'])
icon('coffee', 'drink', [PG((3.5, 9, 'm'), (16.5, 9, 'm'), (16.5, 20.5, 's3.5'), (3.5, 20.5, 's3.5')), P(('M', 16.5, 11), ('L', 17.5, 11), ('A', 17.5, 13.5, 2.5, 270, 450), ('L', 16.5, 16)),
                         L(7, 3, 7, 6), L(10, 3, 10, 6), L(13, 3, 13, 6)], 'cafe cup espresso tea hot', ['cafe', 'cup', 'espresso'])
icon('cocktail', 'drink', [PG((4, 4, 'm'), (20, 4, 'm'), (12, 13, 'm')), L(12, 13, 12, 20.5), L(8, 20.5, 16, 20.5), C(9.5, 6.75, 1.25, fill=False), L(13.5, 8.5, 17.5, 3.5)], 'martini bar aperitif', ['martini', 'aperitif'])
icon('beer', 'drink', [PG((4, 7.5, 'm'), (15, 7.5, 'm'), (15, 20.5, 'c'), (4, 20.5, 'c')), PL((15, 10), (18.5, 10, 's2'), (18.5, 17, 's2'), (15, 17)), P(*bumps(4, 15, 7.5, 3)),
                       L(7.67, 11, 7.67, 17), L(11.33, 11, 11.33, 17)], 'pint mug brewery pub', ['pint', 'mug', 'pub'])
icon('bottle', 'drink', [P(('M', 10.5, 3, 'm'), ('L', 13.5, 3, 'm'), ('L', 13.5, 7.5), ('Q', 16.5, 8.5, 16.5, 11.5), ('L', 16.5, 20.5, 'c'), ('L', 7.5, 20.5, 'c'), ('L', 7.5, 11.5), ('Q', 7.5, 8.5, 10.5, 7.5), closed=True),
                         L(7.5, 13, 16.5, 13), L(7.5, 17, 16.5, 17)], 'wine bottle cellar', ['wine-bottle'])
icon('cup-straw', 'drink', [PG((5.5, 8, 'm'), (18.5, 8, 'm'), (17, 21, 'c'), (7, 21, 'c')), PL((12.5, 8), (14.5, 3.5, 'm'), (18, 3.5)), L(6.2, 12, 17.8, 12)], 'juice smoothie soft drink takeaway', ['juice', 'smoothie'])
icon('tumbler', 'drink', [PG((5.5, 3.5, 'm'), (18.5, 3.5, 'm'), (17, 20.5, 'c'), (7, 20.5, 'c')), wave(6.1, 17.9, 9.5, 2, 0.6)], 'water glass still sparkling', ['water', 'water-glass'])

# =====================================================================================================
#  DIETARY
# =====================================================================================================
icon('wheat', 'dietary', wheat_stalk(), 'grain cereal gluten', ['grain', 'cereal'])
icon('gluten-free', 'dietary', [C(12, 12, 9, fill=False)] + T(wheat_stalk(), s=0.62) + [L(5.64, 5.64, 18.36, 18.36)], 'no gluten coeliac allergen', ['no-gluten'])
icon('milk', 'dietary', [PG((6.5, 9, 'm'), (9, 4.5, 'm'), (15, 4.5, 'm'), (17.5, 9, 'm'), (17.5, 20.5, 'c'), (6.5, 20.5, 'c')), L(6.5, 9, 17.5, 9), L(10, 4.5, 10, 3), L(14, 4.5, 14, 3),
                         L(9.5, 13.5, 14.5, 13.5)], 'dairy lactose allergen', ['dairy', 'lactose'])
icon('nuts', 'dietary', [P(('M', 4.5, 10), ('Q', 4.5, 5.5, 12, 5.5), ('Q', 19.5, 5.5, 19.5, 10), closed=True), P(('M', 6, 10), ('Q', 6, 17.5, 12, 21), ('Q', 18, 17.5, 18, 10)), L(12, 5.5, 12.75, 3)],
     'nut allergen acorn tree nuts', ['nut', 'acorn', 'tree-nuts'])
icon('chili', 'dietary', [P(('M', 18, 6.5), ('Q', 20, 13, 13, 18), ('Q', 8, 21.5, 3.5, 20.5, 'x'), ('Q', 8, 18.5, 9.75, 14), ('Q', 12, 7.5, 18, 6.5), closed=True), PL((18, 6.5), (17.5, 4.5, 'm'), (19.5, 3))],
     'spicy hot pepper', ['spicy', 'pepper'])
icon('vegan', 'dietary', [C(12, 12, 9, fill=False), leaf_shape(8, 16, 16.5, 7.5, 0.38), L(8, 16, 12.5, 11.5)], 'plant based vegan', ['plant-based'])
icon('vegetarian', 'dietary', [L(12, 21, 12, 10.5), leaf_shape(12, 13, 4.5, 6.5, 0.36), leaf_shape(12, 10.5, 19.5, 4, 0.36), L(8, 21, 16, 21)], 'sprout veggie plant', ['veggie', 'sprout'])

# =====================================================================================================
#  HOSPITALITY
# =====================================================================================================
icon('cloche', 'hospitality', [P(('M', 4.5, 16), ('Q', 4.5, 7.5, 12, 7.5), ('Q', 19.5, 7.5, 19.5, 16), closed=True), C(12, 5.75, 1.5, fill=False), L(3, 16, 21, 16), PL((5, 16), (6.5, 19, 'm'), (17.5, 19, 'm'), (19, 16))],
     'room service dish dining serve', ['room-service', 'serve'])
icon('service-bell', 'hospitality', [R(3, 17, 18, 3.5, 'm'), P(('M', 5, 17), ('A', 12, 17, 7, 180, 360), closed=False, fill=True), FO(P(('M', 5, 17), ('A', 12, 17, 7, 180, 360), closed=True)),
                                     L(12, 10, 12, 6.5), L(10, 6.5, 14, 6.5)], 'reception concierge desk check-in', ['concierge', 'reception'])
icon('key', 'hospitality', [C(7.5, 16.5, 4), L(10.33, 13.67, 20, 4), L(17, 7, 19.5, 9.5), L(14.5, 9.5, 16.5, 11.5)], 'room access key card', ['room-key'])
icon('door', 'hospitality', [PL((5.5, 20.5), (5.5, 3.5, 'c'), (18.5, 3.5, 'c'), (18.5, 20.5)), L(3, 20.5, 21, 20.5), D(15, 12.5), FO(PG((5.5, 3.5), (18.5, 3.5), (18.5, 20.5), (5.5, 20.5)))],
     'entrance entry room', ['entrance', 'entry'])
icon('suitcase', 'hospitality', [R(3.5, 7, 17, 13.5), PL((9, 7), (9, 4, 'm'), (15, 4, 'm'), (15, 7)), L(7.5, 7, 7.5, 20.5), L(16.5, 7, 16.5, 20.5)], 'luggage travel stay', ['luggage', 'travel'])
icon('wifi', 'hospitality', [D(12, 19.5, 1.3), A(12, 19.5, 4, 225, 315), A(12, 19.5, 7.75, 225, 315), A(12, 19.5, 11.5, 225, 315)], 'internet wireless connection', ['wireless', 'internet'])
icon('armchair', 'hospitality', [PL((5, 10), (5, 5, 'c'), (19, 5, 'c'), (19, 10)), P(('M', 3, 17.5, 'c'), ('L', 3, 12), ('A', 5, 12, 2, 180, 360), ('L', 7, 14.5, 'm'), ('L', 17, 14.5, 'm'), ('L', 17, 12),
                                                                                   ('A', 19, 12, 2, 180, 360), ('L', 21, 17.5, 'c'), closed=True), L(5.5, 17.5, 5.5, 20.5), L(18.5, 17.5, 18.5, 20.5)],
     'lounge seating comfort', ['lounge', 'seating'])
icon('candle', 'hospitality', [R(9, 11, 6, 10, 'm'), P(('M', 12, 3, 'x'), ('Q', 15, 6.25, 12, 8.25), ('Q', 9, 6.25, 12, 3), closed=True, fill=False), L(12, 8.25, 12, 11)], 'ambience dinner evening', ['ambience'])

# =====================================================================================================
#  INDUSTRY
# =====================================================================================================
icon('factory', 'industry', [PG((3, 20.5, 'c'), (3, 10, 'm'), (8, 13, 'm'), (8, 10, 'm'), (13, 13, 'm'), (15, 13, 'm'), (15, 3.5, 'm'), (19, 3.5, 'm'), (19, 13, 'm'), (21, 13, 'm'), (21, 20.5, 'c')),
                             L(6.5, 17, 8.5, 17), L(11, 17, 13, 17), L(15.5, 17, 17.5, 17)], 'industrial plant manufacturing facility', ['industrial', 'plant', 'manufacturing'])
_wr = P(('M', 3.5, 13.75, 's1.75'), ('L', 11.82, 13.75), ('A', 16.5, 12, 5, 159.5, 20.5), ('L', 16.5, 13.75), ('L', 16.5, 10.25), ('L', 21.18, 10.25),
        ('A', 16.5, 12, 5, -20.5, -159.5), ('L', 3.5, 10.25, 's1.75'), closed=True)
icon('tool', 'industry', [T(_wr, -45, s=0.92)], 'wrench repair maintenance making spanner service', ['wrench', 'spanner', 'repair'])
icon('hammer', 'industry', [PG((12.88, 3.34, 'm'), (20.66, 11.12, 'm'), (17.12, 14.66, 'm'), (9.34, 6.88, 'm'), fill=True), L(13.23, 10.77, 4.5, 19.5)], 'build construction make tool', ['build', 'construction'])
icon('crane', 'industry', [L(6, 20.5, 6, 6), L(9, 20.5, 9, 6), PL((6, 9), (9, 12), (6, 15), (9, 18)), L(3, 6, 21, 6), PL((6, 6), (7.5, 3.5, 'm'), (9, 6)), L(7.5, 3.5, 20.5, 6), L(7.5, 3.5, 3.5, 6),
                           L(17, 6, 17, 12.5), P(('M', 17, 12.5), ('L', 17, 14.5), ('A', 15.5, 14.5, 1.5, 0, 180)), L(4, 20.5, 11, 20.5)], 'construction site lifting', ['construction-crane', 'tower-crane'])
icon('bridge', 'industry', [L(3, 9, 21, 9), L(4.5, 9, 4.5, 20), L(19.5, 9, 19.5, 20), A(12, 20, 7.5, 180, 360), L(8, 9, 8, 13.66), L(12, 9, 12, 12.5), L(16, 9, 16, 13.66)],
     'infrastructure roads utilities civil', ['infrastructure'])
_rul = [R(2, 8.5, 20, 7, 'c')] + [L(x, 8.5, x, 8.5 + (3.5 if i % 2 == 0 else 2)) for i, x in enumerate([6, 9, 12, 15, 18])]
icon('ruler', 'industry', T(_rul, -45, s=0.9), 'precision measure dimension engineering', ['precision', 'measure'])
icon('cogs', 'industry', [gear(9, 9, 6, 4.5, 6, 2.5, fill=True), C(9, 9, 1.75), gear(16.5, 16.5, 4.25, 3, 5, 2, rot=-54), D(16.5, 16.5, 0.9)], 'gears mechanism engineering process', ['gears', 'mechanism'])
icon('hex-nut', 'industry', [PG(*reg_pts(12, 12, 9, 6, 0)), C(12, 12, 3.75, fill=False)], 'nut bolt hardware fastener', ['fastener', 'hardware'])

# =====================================================================================================
#  ENERGY
# =====================================================================================================
icon('battery', 'energy', [R(3, 7, 15, 10), L(20.5, 10.5, 20.5, 13.5), L(7, 10.5, 7, 13.5), L(10.5, 10.5, 10.5, 13.5)], 'charge power storage level', ['power-level'])
icon('battery-charging', 'energy', [R(3, 7, 15, 10), L(20.5, 10.5, 20.5, 13.5), PL((11.5, 9), (8.5, 12.5, 'x'), (12.5, 11.5), (9.5, 15, 'x'))], 'charging electric ev', ['charging'])
icon('plug', 'energy', [L(9, 3, 9, 7.5), L(15, 3, 15, 7.5), PG((5.5, 7.5, 'm'), (18.5, 7.5, 'm'), (18.5, 12, 's4.5'), (12, 16.5, 'm'), (5.5, 12, 's4.5')), L(12, 16.5, 12, 21)],
     'electric power socket connect', ['power-plug', 'electric'])
icon('solar', 'energy', [PG((5, 4, 'm'), (19, 4, 'm'), (21, 15, 'm'), (3, 15, 'm')), L(12, 4, 12, 15), L(4, 9.5, 20, 9.5), L(12, 15, 12, 20.5), L(8, 20.5, 16, 20.5)], 'solar panel renewable photovoltaic', ['solar-panel', 'renewable'])
_blade = lambda a: P(('M', 12, 10), ('Q', 12 + 3 * math.cos((a - 22) * D2R), 10 + 3 * math.sin((a - 22) * D2R), 12 + 7 * math.cos(a * D2R), 10 + 7 * math.sin(a * D2R), 'x'),
                     ('Q', 12 + 3.5 * math.cos((a + 10) * D2R), 10 + 3.5 * math.sin((a + 10) * D2R), 12, 10), closed=True, fill=False)
icon('wind-turbine', 'energy', [L(12, 10, 12, 20.5), L(9, 20.5, 15, 20.5), _blade(-90), _blade(30), _blade(150), D(12, 10, 1.1)], 'wind power renewable turbine', ['wind-power'])
icon('flame', 'energy', [P(('M', 12, 21), ('C', 7.5, 21, 5, 18, 5, 14.5), ('C', 5, 10.5, 8.5, 8.5, 10, 3, 'x'), ('C', 13.5, 6, 19, 9.5, 19, 14.5), ('C', 19, 18, 16.5, 21, 12, 21), closed=True),
                         P(('M', 12, 21), ('C', 10, 21, 9, 19.5, 9, 18), ('C', 9, 16, 11, 15, 12, 13, 'x'), ('C', 13, 15, 15, 16, 15, 18), ('C', 15, 19.5, 14, 21, 12, 21), fill=False)],
     'fire gas heat heating', ['fire', 'gas', 'heat'])
icon('power', 'energy', [A(12, 12.5, 8, -50, 230), L(12, 3, 12, 11.5)], 'on off switch shutdown', ['on-off', 'switch-power'])
icon('gauge', 'energy', [A(12, 14, 9, 150, 390), L(12, 14, 16.5, 9.5), D(12, 14, 1.25)], 'meter speed performance dashboard', ['meter', 'speedometer'])

# =====================================================================================================
#  LOGISTICS
# =====================================================================================================
icon('truck', 'logistics', [PL((5, 17), (3, 17, 'c'), (3, 5.5, 'c'), (15, 5.5, 'c'), (15, 17)), L(9, 17, 15, 17), PL((15, 9), (18.5, 9, 'm'), (21, 12.5, 'm'), (21, 17, 'c'), (19, 17)),
                            C(7, 17.5, 2, fill=False), C(17, 17.5, 2, fill=False), FO(PG((3, 5.5), (15, 5.5), (15, 17), (3, 17)))], 'logistics shipping transport delivery haulage', ['shipping', 'transport', 'delivery-truck'])
icon('container', 'logistics', [R(3, 6, 18, 12)] + [L(x, 8.75, x, 15.25) for x in (7, 10.33, 13.67, 17)], 'shipping container cargo freight', ['cargo', 'freight'])
icon('forklift', 'logistics', [PG((3, 11, 'm'), (12, 11, 'm'), (12, 17, 'c'), (3, 17, 'c')), PL((4.5, 11), (6, 5, 'm'), (10, 5, 'm'), (11, 11)), L(15, 3.5, 15, 19), L(15, 19, 21, 19),
                               C(6, 19, 1.75, fill=False), C(11, 19, 1.75, fill=False)], 'warehouse lifting pallet', ['lift-truck'])
icon('ship', 'logistics', [PG((3.5, 14, 'm'), (20.5, 14, 'm'), (17.5, 20, 'm'), (6.5, 20, 'm')), PL((7, 14), (7, 9, 'c'), (15, 9, 'c'), (15, 14)), PL((10, 9), (10, 5.5, 'm'), (13, 5.5, 'm'), (13, 9))],
     'boat port freight maritime', ['boat', 'maritime'])
icon('plane', 'logistics', T([PG((12, 2.5, 'm'), (13.5, 4.5, 'm'), (13.5, 9.5), (21, 14, 'm'), (21, 16, 'm'), (13.5, 13.5), (13.5, 18), (16, 19.75, 'm'), (16, 21, 'm'), (12, 20), (8, 21, 'm'), (8, 19.75, 'm'),
                               (10.5, 18), (10.5, 13.5), (3, 16, 'm'), (3, 14, 'm'), (10.5, 9.5), (10.5, 4.5, 'm'))], 45, s=0.92), 'air freight flight travel', ['flight', 'airplane'])
icon('warehouse', 'logistics', [PG((3, 20.5, 'c'), (3, 8.5, 'm'), (12, 4, 'm'), (21, 8.5, 'm'), (21, 20.5, 'c')), PL((7, 20.5), (7, 11, 'm'), (17, 11, 'm'), (17, 20.5)), L(7, 14, 17, 14), L(7, 17, 17, 17)],
     'storage depot distribution', ['storage', 'depot'])
icon('pallet', 'logistics', [L(3, 17, 21, 17), L(3, 20.5, 21, 20.5), L(4.5, 17, 4.5, 20.5), L(12, 17, 12, 20.5), L(19.5, 17, 19.5, 20.5), R(4.5, 10, 7, 7, fill=True), R(12.5, 10, 7, 7, fill=True),
                             R(8.5, 3.5, 7, 6.5, fill=True)], 'stock boxes inventory', ['stock', 'inventory'])

# =====================================================================================================
#  DELIVERY
# =====================================================================================================
BOX = [PG((12, 3, 'm'), (20, 7.5, 'm'), (20, 16.5, 'm'), (12, 21, 'm'), (4, 16.5, 'm'), (4, 7.5, 'm')), PL((4, 7.5), (12, 12), (20, 7.5)), L(12, 12, 12, 21), L(8, 5.25, 16, 9.75)]
icon('package', 'delivery', BOX, 'parcel box shipment order', ['parcel', 'box'])
FLATBOX = [PG((3.5, 8, 'c'), (20.5, 8, 'c'), (20.5, 20.5, 'c'), (3.5, 20.5, 'c')), PL((3.5, 8), (5.5, 4, 'm'), (18.5, 4, 'm'), (20.5, 8))]
icon('package-check', 'delivery', FLATBOX + [PL((8.5, 14), (11, 16.5), (15.5, 12))], 'delivered received order complete', ['delivered'])
icon('package-return', 'delivery', FLATBOX + [PL((16, 17.5), (16, 13.5, 's2'), (8, 13.5)), PL((10.5, 11), (8, 13.5, 'x'), (10.5, 16))], 'returns refund exchange', ['returns', 'refund'])
icon('express', 'delivery', [C(14, 12, 7), PL((14, 8.5), (14, 12), (16.5, 13.5)), L(3, 8.5, 5.5, 8.5), L(3, 12, 5, 12), L(3, 15.5, 5.5, 15.5)], 'fast same day quick delivery', ['fast-delivery', 'same-day'])
icon('tracking', 'delivery', [pin(16, 8.25, 4.5, 16.5), C(16, 8.25, 1.5, fill=False), D(4.5, 19.5, 1.1), D(7.75, 17.75, 1.1), D(11, 16, 1.1)], 'track order status location', ['track', 'order-status'])
icon('mailbox', 'delivery', [P(('M', 4, 15, 'c'), ('L', 4, 9), ('A', 9, 9, 5, 180, 360), ('L', 14, 15, 'c'), closed=True), L(6.5, 9.5, 11.5, 9.5), L(9, 15, 9, 20.5), L(6, 20.5, 12, 20.5),
                             PL((14, 12.5), (18.5, 12.5, 'm'), (18.5, 7.5, 'm'), (15.5, 7.5, 'm'), (15.5, 10))], 'letterbox post mail', ['letterbox', 'post'])
icon('scooter', 'delivery', [C(5.5, 17.5, 2.5, fill=False), C(18.5, 17.5, 2.5, fill=False), L(8, 17.5, 16, 17.5), PL((18.5, 17.5), (15.5, 6.5, 'm'), (13, 6.5)), R(3.5, 8.5, 6.5, 6, fill=True)],
     'courier rider last mile', ['courier', 'rider'])

# =====================================================================================================
#  SAFETY
# =====================================================================================================
icon('hard-hat', 'safety', [P(('M', 4.5, 15), ('A', 12, 15, 7.5, 180, 360), closed=True), R(3, 15, 18, 3.5, 'm', fill=False), PL((10, 7.75), (10, 5, 'm'), (14, 5, 'm'), (14, 7.75))],
     'helmet ppe construction site safety', ['helmet', 'ppe'])
icon('shield-check', 'safety', [shield(), PL((8.5, 12), (11, 14.5), (15.5, 10))], 'protected verified compliance safe', ['protected', 'compliance', 'safe'])
icon('cone', 'safety', [PL((5.5, 20), (10, 5.5, 'm'), (14, 5.5, 'm'), (18.5, 20)), L(3, 20, 21, 20), L(8.45, 10.5, 15.55, 10.5), L(7.05, 15, 16.95, 15), FO(PG((5.5, 20), (10, 5.5), (14, 5.5), (18.5, 20)))],
     'traffic roadworks caution works', ['traffic-cone', 'roadworks'])
icon('extinguisher', 'safety', [P(('M', 9, 21, 'c'), ('L', 9, 11), ('A', 13, 11, 4, 180, 360), ('L', 17, 21, 'c'), closed=True), PL((11, 7.5), (11, 4, 'm'), (15, 4, 'm'), (15, 7.5)),
                                L(15, 4.5, 18.5, 4.5), P(('M', 11, 5), ('Q', 5, 5, 5, 12), ('L', 5, 17)), L(9, 15, 17, 15)], 'fire safety emergency', ['fire-extinguisher'])
icon('goggles', 'safety', [PG((3, 8, 's3'), (21, 8, 's3'), (21, 15.5, 's2'), (15, 15.5, 'm'), (13.25, 13, 'm'), (10.75, 13, 'm'), (9, 15.5, 'm'), (3, 15.5, 's2')), L(12, 8, 12, 10.5)],
     'eye protection ppe glasses', ['safety-glasses', 'eye-protection'])
icon('siren', 'safety', [P(('M', 7, 18), ('L', 7, 12.5), ('A', 12, 12.5, 5, 180, 360), ('L', 17, 18)), R(5, 18, 14, 3, 'm', fill=False), FO(P(('M', 7, 18), ('L', 7, 12.5), ('A', 12, 12.5, 5, 180, 360), ('L', 17, 18), closed=True)),
                         L(12, 3, 12, 4.5), L(5, 5.5, 6.25, 6.75), L(19, 5.5, 17.75, 6.75), L(3, 12.5, 4.5, 12.5), L(19.5, 12.5, 21, 12.5), L(12, 12.5, 12, 18)], 'alarm emergency alert beacon', ['beacon', 'emergency-light'])
icon('barrier', 'safety', [R(3, 7, 18, 5), L(9, 7, 6.5, 12), L(14, 7, 11.5, 12), L(19, 7, 16.5, 12), L(6, 12, 6, 20.5), L(18, 12, 18, 20.5), L(4, 20.5, 8, 20.5), L(16, 20.5, 20, 20.5)],
     'roadblock closed works restricted', ['roadblock'])

# =====================================================================================================
#  DATA
# =====================================================================================================
AXIS = PL((3.5, 3.5), (3.5, 20.5, 'c'), (20.5, 20.5))
icon('chart', 'data', [AXIS, L(8.5, 16.5, 8.5, 12.5), L(13, 16.5, 13, 7.5), L(17.5, 16.5, 17.5, 10.5)], 'bar chart analytics statistics graph stats report', ['bar-chart', 'analytics', 'statistics', 'stats', 'graph'])
icon('chart-line', 'data', [AXIS, PL((7.5, 15.5), (11, 11, 'm'), (14.5, 13.5, 'm'), (19.5, 7.5))], 'line chart trend performance', ['line-chart'])
icon('chart-pie', 'data', [P(('M', 11, 13, 'm'), ('L', 19, 13), ('A', 11, 13, 8, 0, 270), closed=True), P(('M', 13, 11, 'm'), ('L', 13, 3), ('A', 13, 11, 8, 270, 360), closed=True, fill=True)],
     'pie chart share breakdown', ['pie-chart'])
icon('database', 'data', [E(12, 5.5, 8, 2.75, fill=True), P(('M', 4, 5.5), ('L', 4, 18.5), ('EA', 12, 18.5, 8, 2.75, 180, 0), ('L', 20, 5.5)), P(('M', 4, 12), ('EA', 12, 12, 8, 2.75, 180, 0))],
     'storage data server records', ['storage-data', 'records'])
icon('table', 'data', [R(3.5, 4, 17, 16), L(3.5, 9, 20.5, 9), L(3.5, 14.5, 20.5, 14.5), L(10, 4, 10, 20)], 'spreadsheet grid rows columns', ['spreadsheet'])
TREND = [PL((3, 17), (9, 11, 'm'), (13, 15, 'm'), (21, 7)), PL((15.5, 7), (21, 7, 'x'), (21, 12.5))]
icon('trend-up', 'data', TREND, 'growth increase rise results', ['growth', 'increase'])
icon('trend-down', 'data', T(TREND, flipy=True), 'decline decrease fall', ['decline', 'decrease'])
icon('layers', 'data', [PG((12, 3.5, 'm'), (20, 7.5, 'm'), (12, 11.5, 'm'), (4, 7.5, 'm')), PL((4, 12), (12, 16, 'm'), (20, 12)), PL((4, 16.5), (12, 20.5, 'm'), (20, 16.5))], 'stack levels tiers', ['stack'])
icon('presentation', 'data', [L(3, 4, 21, 4), PL((4.5, 4), (4.5, 15, 'c'), (19.5, 15, 'c'), (19.5, 4)), L(12, 15, 12, 17.5), PL((8, 21), (12, 17.5, 'm'), (16, 21)), PL((8, 11.5), (10.5, 9, 'm'), (13, 11, 'm'), (16, 8))],
     'slides talk pitch board', ['slides', 'pitch'])
icon('research', 'data', [PL((11.5, 20.5), (4.5, 20.5, 'c'), (4.5, 3.5, 'c'), (13.5, 3.5), (17.5, 7.5), (17.5, 10)), L(7.5, 8, 12, 8), L(7.5, 11.5, 10.5, 11.5), C(15, 15, 3.5, fill=True), L(17.5, 17.5, 20.5, 20.5)],
     'study analysis evidence investigate policy', ['study', 'analysis', 'evidence'])

# =====================================================================================================
#  ENVIRONMENT
# =====================================================================================================
icon('leaf', 'environment', [leaf_shape(5.5, 18.5, 19.5, 4.5, 0.4), L(3.5, 20.5, 13, 11)], 'nature sustainability eco seasonal green responsibility', ['nature', 'eco', 'sustainability', 'seasonal'])
icon('tree', 'environment', [P(*chain([(7.5, 11.25, 4), (12, 8, 5), (16.5, 11.25, 4)], 120, 60), closed=True), L(12, 14.75, 12, 21), PL((12, 17.75), (9.25, 15))], 'park nature forest outdoors', ['forest', 'park'])
_tri = [(12, 4), (20.5, 18.75), (3.5, 18.75)]
_g = (12, (4 + 18.75 * 2) / 3)
def _recy():
    A_, B_, C_ = _tri
    p1 = (C_[0] + 0.42 * (A_[0] - C_[0]), C_[1] + 0.42 * (A_[1] - C_[1]))
    p2 = (A_[0] + 0.46 * (B_[0] - A_[0]), A_[1] + 0.46 * (B_[1] - A_[1]))
    ang = math.degrees(math.atan2(B_[1] - A_[1], B_[0] - A_[0]))
    return [PL(p1, (A_[0], A_[1], 's2'), p2), arrowhead(p2[0], p2[1], ang, 3.2, 42)]
icon('recycle', 'environment', _recy() + T(_recy(), 120, cx=_g[0], cy=_g[1]) + T(_recy(), 240, cx=_g[0], cy=_g[1]), 'recycling circular reuse waste', ['recycling', 'circular'])
icon('drop', 'environment', [drop(12, 14.5, 6.5, 3)], 'water liquid utilities rain', ['water-drop', 'droplet'])
icon('cloud', 'environment', [P(('M', 7, 18.5), *chain([(7, 14.5, 4), (12.5, 10.5, 5.5), (17, 14.5, 4)], 90, 90), closed=True)], 'weather cloud computing sky', ['weather-cloud'])
icon('mountain', 'environment', [PG((4, 19.5, 'm'), (9, 7.5, 'm'), (12.5, 13, 'm'), (15.5, 9.5, 'm'), (20, 19.5, 'm')), PL((6.75, 12), (8.25, 13.25, 'm'), (9.5, 11.75, 'm'), (11.86, 12))],
     'landscape outdoors terrain', ['landscape', 'terrain'])
icon('wind', 'environment', [P(('M', 3, 12), ('L', 17.5, 12), ('A', 17.5, 9.5, 2.5, 90, -200)), P(('M', 3, 8), ('L', 10, 8), ('A', 10, 6, 2, 90, -200)), P(('M', 3, 16), ('L', 13, 16), ('A', 13, 18, 2, 270, 520))],
     'air breeze ventilation', ['breeze', 'air'])
icon('wave', 'environment', [wave(3, 21, 9.5, 2, 1.25), wave(3, 21, 14.5, 2, 1.25)], 'water sea ocean river', ['sea', 'ocean', 'river'])

# =====================================================================================================
#  COMMUNITY
# =====================================================================================================
icon('community', 'community', [bust(12, 8.25, 3, 6.5, 17.5, 17, 20.5, 3), C(5.25, 9.5, 2.25, fill=False), PL((3, 18.5), (3, 15, 's2'), (6.5, 15)), C(18.75, 9.5, 2.25, fill=False),
                                PL((21, 18.5), (21, 15, 's2'), (17.5, 15))], 'neighbourhood local residents civic society group', ['neighbourhood', 'neighborhood', 'society', 'residents'])
icon('houses', 'community', [PG((3, 20.5, 'c'), (3, 12, 'm'), (7, 8.5, 'm'), (11, 12, 'm'), (11, 20.5, 'c')), PG((13, 20.5, 'c'), (13, 10, 'm'), (17, 6, 'm'), (21, 10, 'm'), (21, 20.5, 'c')),
                             PL((6, 20.5), (6, 17, 'm'), (8, 17, 'm'), (8, 20.5)), D(17, 13), PL((16, 20.5), (16, 17, 'm'), (18, 17, 'm'), (18, 20.5))], 'housing neighbourhood homes street', ['housing', 'homes'])
icon('donate', 'community', [C(14.5, 6.5, 3.5, fill=True), L(14.5, 5, 14.5, 8), hand_pg(), L(3, 13.5, 3, 20.5)], 'donation give coin charity fundraising', ['donation', 'give', 'charity'])
icon('conversation', 'community', [PG((3, 3.5, 'c'), (14.5, 3.5, 'c'), (14.5, 11.5, 'c'), (7, 11.5, 'm'), (3, 15, 'm')), PL((17.5, 8.5), (21, 8.5, 'c'), (21, 20.5, 'm'), (17, 17, 'm'), (10.5, 17, 'c'), (10.5, 14.5))],
     'dialogue discussion forum consultation', ['dialogue', 'discussion', 'forum'])
_hub = (12, 12.75); _nodes = [(12, 5), (5, 17.5), (19, 17.5)]
icon('network', 'community', [C(*_hub, 2.5, fill=True)] + [C(*n, 2, fill=True) for n in _nodes] + [link(_hub, n, 2.5, 2) for n in _nodes], 'connections partners nodes alliance', ['connections', 'nodes'])
icon('placard', 'community', [R(4, 3.5, 16, 10), L(12, 13.5, 12, 21), L(7.5, 7.5, 16.5, 7.5), L(7.5, 10, 13, 10)], 'campaign protest advocacy sign', ['protest', 'advocacy'])
icon('ballot', 'community', [PL((8, 11), (4, 11, 'c'), (4, 20.5, 'c'), (20, 20.5, 'c'), (20, 11, 'c'), (16, 11)), PL((8, 13), (8, 4, 'm'), (16, 4, 'm'), (16, 13)), PL((10, 7.5), (11.5, 9), (14, 6))],
     'vote election poll democracy', ['vote', 'election', 'poll'])

# =====================================================================================================
#  BUSINESS
# =====================================================================================================
icon('briefcase', 'business', [R(3, 7, 18, 13), PL((9, 7), (9, 4.5, 'm'), (15, 4.5, 'm'), (15, 7)), L(3, 12.5, 10.5, 12.5), L(13.5, 12.5, 21, 12.5), R(10.5, 11, 3, 3, 'm', fill=False)],
     'work business job career portfolio', ['work', 'job', 'career'])
icon('org-chart', 'business', [R(9, 3, 6, 5, fill=True), R(3, 16, 6, 5, fill=True), R(15, 16, 6, 5, fill=True), L(12, 8, 12, 12), PL((6, 16), (6, 12, 'm'), (18, 12, 'm'), (18, 16))],
     'organisation structure hierarchy team leadership', ['organisation', 'hierarchy', 'structure'])
icon('meeting', 'business', [C(7, 7.5, 2.25, fill=True), A(7, 14, 3, 180, 360), C(17, 7.5, 2.25, fill=True), A(17, 14, 3, 180, 360), L(3, 14, 21, 14), L(6, 14, 6, 20.5), L(18, 14, 18, 20.5)],
     'consultation workshop session table', ['workshop', 'consultation'])
_rocket = [P(('M', 12, 3, 'x'), ('Q', 15.5, 5.5, 15.5, 10), ('L', 15.5, 16.5, 'm'), ('L', 8.5, 16.5, 'm'), ('L', 8.5, 10), ('Q', 8.5, 5.5, 12, 3), closed=True),
           PL((8.5, 12.5), (5.5, 15.5, 'm'), (5.5, 19, 'm'), (8.5, 16.5)), PL((15.5, 12.5), (18.5, 15.5, 'm'), (18.5, 19, 'm'), (15.5, 16.5)), C(12, 10, 1.75, fill=False), PL((10.5, 16.5), (12, 20, 'm'), (13.5, 16.5))]
icon('rocket', 'business', T(_rocket, 45, s=0.86), 'launch startup growth go', ['launch', 'startup'])
icon('pawn', 'business', [C(12, 6.5, 3, fill=True), L(9.5, 10.75, 14.5, 10.75), P(('M', 10.25, 10.75), ('Q', 10.25, 15, 7.5, 18), ('L', 16.5, 18), ('Q', 13.75, 15, 13.75, 10.75)), R(5.5, 18, 13, 3, 'm')],
     'strategy chess tactics plan', ['strategy', 'chess'])
icon('timeline', 'business', [C(6, 12, 2, fill=True), C(12, 12, 2, fill=True), C(18, 12, 2, fill=True), L(3, 12, 4, 12), L(8, 12, 10, 12), L(14, 12, 16, 12), L(20, 12, 21, 12),
                              L(6, 10, 6, 5.5), L(12, 14, 12, 18.5), L(18, 10, 18, 5.5)], 'roadmap milestones plan schedule history', ['roadmap', 'milestones'])
icon('kanban', 'business', [R(3, 3.5, 18, 17), L(7.5, 7.5, 7.5, 15.5), L(12, 7.5, 12, 11.5), L(16.5, 7.5, 16.5, 17)], 'board tasks project workflow', ['board', 'tasks'])

# =====================================================================================================
#  FINANCE
# =====================================================================================================
icon('wallet', 'finance', [PG((3.5, 6.5, 'c'), (20, 6.5, 'c'), (20, 20, 'c'), (3.5, 20, 'c')), PL((5.5, 6.5), (16, 3.5, 'm'), (17, 6.5)), PL((20, 10.5), (15.5, 10.5, 's2'), (15.5, 15.5, 's2'), (20, 15.5)), D(17.75, 13)],
     'payment money pocket budget', ['payment', 'money'])
icon('coins', 'finance', [C(9, 9, 6), A(15, 15, 6, 270, 540), L(9, 6.5, 9, 11.5)], 'money cash savings currency', ['cash', 'savings'])
icon('bank', 'finance', [PG((3, 9, 'm'), (12, 3.5, 'm'), (21, 9, 'm')), L(6, 11.5, 6, 17.5), L(10, 11.5, 10, 17.5), L(14, 11.5, 14, 17.5), L(18, 11.5, 18, 17.5), L(3, 20.5, 21, 20.5)],
     'banking institution finance', ['banking', 'institution'])
icon('credit-card', 'finance', [R(3, 5.5, 18, 13), L(3, 10, 21, 10), L(6.5, 14.5, 10, 14.5)], 'payment card debit pay', ['card', 'payment-card'])
icon('receipt', 'finance', [PG((5, 3.5, 'm'), (19, 3.5, 'm'), (19, 20.5), (16.67, 19.25), (14.33, 20.5), (12, 19.25), (9.67, 20.5), (7.33, 19.25), (5, 20.5)), L(8.5, 8, 15.5, 8), L(8.5, 11.5, 15.5, 11.5), L(8.5, 15, 12.5, 15)],
     'invoice bill purchase', ['invoice', 'bill'])
icon('calculator', 'finance', [R(5, 3, 14, 18), R(8, 6, 8, 3.5, 'm', fill=False), D(9, 13), D(12, 13), D(15, 13), D(9, 16.75), D(12, 16.75), D(15, 16.75)], 'accounting calculate budget tax', ['accounting'])
icon('percent', 'finance', [L(18.5, 5.5, 5.5, 18.5), C(7, 7, 2.25), C(17, 17, 2.25, fill=True)], 'rate interest discount ratio', ['rate', 'interest'])
icon('banknote', 'finance', [R(3, 6, 18, 12), C(12, 12, 2.5, fill=False), D(6.5, 12), D(17.5, 12)], 'cash money bill payment', ['money-bill', 'bill-note'])

# =====================================================================================================
#  LEGAL
# =====================================================================================================
_pan = lambda cx: [PL((cx - 2.5, 14.5), (cx, 6.5, 'x'), (cx + 2.5, 14.5)), P(('M', cx - 2.5, 14.5), ('L', cx + 2.5, 14.5), ('Q', cx, 18, cx - 2.5, 14.5), closed=True, fill=True)]
icon('scales', 'legal', [L(12, 3.5, 12, 20.5), L(7.5, 20.5, 16.5, 20.5), L(5.5, 6.5, 18.5, 6.5)] + _pan(5.5) + _pan(18.5), 'justice law balance fair', ['justice', 'law', 'balance'])
icon('gavel', 'legal', [PG((8.5, 8, 'm'), (13, 3.5, 'm'), (20.5, 11, 'm'), (16, 15.5, 'm')), L(12.25, 11.75, 4, 20), L(13, 20.5, 21, 20.5)], 'court judge ruling auction', ['court', 'judge'])
icon('contract', 'legal', doc() + [L(8.5, 11, 15.5, 11), P(('M', 8, 17.5), ('Q', 9.5, 14, 11, 16.5), ('Q', 12.5, 19, 14.5, 16))], 'agreement document terms sign', ['agreement-doc', 'terms'])
icon('stamp', 'legal', [R(4, 13, 16, 4.5, 'm'), L(5, 20.5, 19, 20.5), C(12, 5.5, 2.5, fill=False), PL((10.5, 7.75), (10, 13)), PL((13.5, 7.75), (14, 13))], 'approval seal certify notary', ['seal', 'approval', 'notary'])
icon('signature', 'legal', [L(3, 19.5, 21, 19.5), P(('M', 4, 14.5), ('C', 6, 8, 8.5, 8, 8.5, 12), ('C', 8.5, 16, 11, 16, 12.5, 12.5), ('C', 13.5, 10, 15, 10, 15.5, 13), ('L', 16, 14.5), ('L', 20, 10))],
     'sign autograph authorise', ['sign', 'autograph'])
icon('document-lock', 'legal', [PL((11, 21), (5, 21, 'c'), (5, 3, 'c'), (14, 3), (19, 8), (19, 10.5)), PL((14, 3), (14, 8, 'm'), (19, 8)), R(13, 15, 7, 6, 'm', fill=True),
                                P(('M', 14.5, 15), ('L', 14.5, 13.5), ('A', 16.5, 13.5, 2, 180, 360), ('L', 18.5, 15))], 'privacy confidential gdpr policy', ['privacy', 'confidential'])

# =====================================================================================================
#  COMMERCE
# =====================================================================================================
icon('tag', 'commerce', [PG((3.5, 3.5, 'c'), (11.5, 3.5, 'm'), (20.5, 12.5, 's2'), (12.5, 20.5, 's2'), (3.5, 11.5, 'm')), C(8, 8, 1.5, fill=False)], 'price label sale', ['price', 'label'])
icon('store', 'commerce', [PL((3, 8), (5.5, 3.5, 'm'), (18.5, 3.5, 'm'), (21, 8)), P(*bumps(3, 21, 8, 4, up=False)), L(3, 8, 21, 8), PL((4.5, 11.5), (4.5, 20.5, 'c'), (19.5, 20.5, 'c'), (19.5, 11.5)),
                           PL((10, 20.5), (10, 15.5, 'm'), (14, 15.5, 'm'), (14, 20.5))], 'shop storefront retail boutique', ['shop-front', 'retail', 'boutique'])
icon('gift', 'commerce', [R(3, 7.5, 18, 4.5), PL((5, 12), (5, 21, 'c'), (19, 21, 'c'), (19, 12)), L(12, 7.5, 12, 21), P(('M', 12, 7.5), ('Q', 7, 2, 6.5, 5.5), ('Q', 7, 7.5, 12, 7.5)),
                          P(('M', 12, 7.5), ('Q', 17, 2, 17.5, 5.5), ('Q', 17, 7.5, 12, 7.5))], 'present gifts reward voucher', ['present', 'gifts', 'voucher'])
icon('discount', 'commerce', [PG(*star_pts(12, 12, 9, 7.25, 12, -90, 'm')), L(14.75, 9.25, 9.25, 14.75), D(9.25, 9.5), D(14.75, 14.5)], 'sale offer promotion deal', ['sale', 'offer', 'promotion'])
icon('barcode', 'commerce', [L(x, 6, x, 18) for x in (4.5, 7, 9, 12.5, 15, 17, 19.5)], 'scan product sku code', ['scan', 'sku'])
icon('basket', 'commerce', [L(3, 10.5, 21, 10.5), PL((4, 10.5), (5.5, 19.5, 'c'), (18.5, 19.5, 'c'), (20, 10.5)), L(8, 10.5, 10.5, 4.5), L(16, 10.5, 13.5, 4.5), L(9.5, 13.5, 10, 16.5), L(12, 13.5, 12, 16.5), L(14.5, 13.5, 14, 16.5),
                            FO(PG((4, 10.5), (5.5, 19.5), (18.5, 19.5), (20, 10.5)))], 'shopping basket groceries market', ['shopping-basket', 'groceries'])
icon('cart-plus', 'commerce', cart_lines() + [L(13, 9.5, 13, 13.5), L(11, 11.5, 15, 11.5)], 'add to cart buy', ['add-to-cart'])

# =====================================================================================================
#  SOCIAL
# =====================================================================================================
icon('thumbs-up', 'social', [PG((3, 10.5, 'm'), (7, 10.5), (7, 20.5), (3, 20.5, 'm')), PG((7, 10.5, 'm'), (10.5, 3.5, 's1.5'), (12.5, 3.5, 's1.5'), (13.5, 5.5, 'm'), (13, 9.5, 'm'), (19, 9.5, 's1.5'),
                                                                                        (20.75, 11.75, 'm'), (18.75, 19, 's1.5'), (17, 20.5, 'm'), (7, 20.5), fill=True)], 'like approve recommend', ['like', 'approve'])
icon('comment', 'social', [P(('M', 3.5, 20.5, 'm'), ('L', 5.04, 16.38), ('A', 12, 11.5, 8.5, 145, 475), closed=True)], 'reply discussion feedback', ['reply', 'feedback'])
icon('repost', 'social', [PL((3.5, 8.5), (7, 5, 'x'), (10.5, 8.5)), PL((7, 5), (7, 17.5, 's3'), (14, 17.5)), PL((17, 19), (17, 6.5, 's3'), (10, 6.5)), PL((13.5, 15.5), (17, 19, 'x'), (20.5, 15.5))],
     'share retweet reshare', ['reshare', 'retweet'])
icon('hashtag', 'social', [L(9.5, 3.5, 7.5, 20.5), L(16.5, 3.5, 14.5, 20.5), L(4, 8.5, 20.5, 8.5), L(3.5, 15.5, 20, 15.5)], 'hash topic trend tag', ['hash', 'topic'])
icon('camera', 'social', [PG((3, 7, 'c'), (7.5, 7, 'm'), (9.5, 4.5, 'm'), (14.5, 4.5, 'm'), (16.5, 7, 'm'), (21, 7, 'c'), (21, 19.5, 'c'), (3, 19.5, 'c')), C(12, 13, 4)], 'photo photography picture post', ['photography'])
icon('story', 'social', [A(12, 12, 9, -80, -10), A(12, 12, 9, 10, 80), A(12, 12, 9, 100, 170), A(12, 12, 9, 190, 260), L(12, 8, 12, 16), L(8, 12, 16, 12)], 'stories status reel add', ['stories', 'status'])
icon('share-up', 'social', [PL((8, 9), (5, 9, 'c'), (5, 20.5, 'c'), (19, 20.5, 'c'), (19, 9, 'c'), (16, 9)), L(12, 3.5, 12, 14), PL((8.5, 7), (12, 3.5, 'x'), (15.5, 7)),
                            FO(PG((5, 9), (19, 9), (19, 20.5), (5, 20.5)))], 'share export send out', ['share-box', 'export'])

# =====================================================================================================
#  PRODUCT CARE
# =====================================================================================================
icon('wash', 'product-care', [PL((3, 8), (5.5, 19.5, 'c'), (18.5, 19.5, 'c'), (21, 8)), wave(3.6, 20.4, 10.5, 2, 0.7)], 'washing machine wash laundry care label', ['machine-wash', 'laundry'])
icon('iron', 'product-care', [P(('M', 3, 17.5, 'm'), ('Q', 3, 10.5, 10, 10.5), ('L', 21, 10.5, 'c'), ('L', 21, 17.5, 'c'), closed=True), PL((12, 10.5), (13.5, 6, 'm'), (21, 6, 'm'), (21, 10.5)), D(10.5, 14.25), D(14.5, 14.25)],
     'ironing press care label', ['ironing'])
icon('tumble-dry', 'product-care', [R(3.5, 3.5, 17, 17), C(12, 12, 6, fill=False)], 'dryer drying care label', ['dryer'])
icon('no-bleach', 'product-care', [PG((12, 4, 'm'), (20.5, 19, 'm'), (3.5, 19, 'm')), L(6.5, 7.5, 17.5, 20.5), L(17.5, 7.5, 6.5, 20.5)], 'do not bleach care label', ['do-not-bleach'])
icon('hang-dry', 'product-care', [R(3.5, 3.5, 17, 17), P(('M', 7.5, 3.5), ('Q', 12, 9.5, 16.5, 3.5))], 'line dry air dry care label', ['line-dry'])
icon('sewing', 'product-care', [L(4, 20, 15.5, 8.5), E(17.25, 6.75, 1.25, 2.6, 45, fill=False), P(('M', 18.25, 5.75), ('Q', 21.5, 9.5, 17, 12.5), ('Q', 12, 15.5, 14.5, 19.5))], 'repair mend needle thread tailoring', ['repair-clothing', 'needle', 'mend'])
icon('warranty', 'product-care', [shield(), PG(*star_pts(12, 11.75, 4.25, 1.9, 5), fill=False)], 'guarantee quality promise', ['guarantee'])

# =====================================================================================================
#  PRODUCT (software)
# =====================================================================================================
icon('code', 'product', [PL((8, 7), (3.5, 12), (8, 17)), PL((16, 7), (20.5, 12), (16, 17)), L(13.5, 5, 10.5, 19)], 'developer programming html api', ['programming', 'developer'])
icon('terminal', 'product', [R(3, 4, 18, 16), PL((7, 9), (10, 12), (7, 15)), L(12, 15, 17, 15)], 'console command line shell', ['console', 'command-line'])
icon('dashboard', 'product', [R(3.5, 3.5, 7, 9, fill=True), R(13.5, 3.5, 7, 5, fill=True), R(13.5, 11.5, 7, 9, fill=True), R(3.5, 15.5, 7, 5, fill=True)], 'layout overview panels app', ['overview', 'layout'])
icon('component', 'product', [PG((12, 3.5, 'm'), (14.5, 6, 'm'), (12, 8.5, 'm'), (9.5, 6, 'm'), fill=True), PG((18, 9.5, 'm'), (20.5, 12, 'm'), (18, 14.5, 'm'), (15.5, 12, 'm')),
                              PG((12, 15.5, 'm'), (14.5, 18, 'm'), (12, 20.5, 'm'), (9.5, 18, 'm')), PG((6, 9.5, 'm'), (8.5, 12, 'm'), (6, 14.5, 'm'), (3.5, 12, 'm'))], 'module block design system', ['module', 'block'])
icon('toggle', 'product', [capsule(12, 12, 18, 10, 0, fill=False), C(16, 12, 3, fill=True)], 'switch setting on off feature', ['switch'])
icon('cursor', 'product', [PG((5, 3.5, 'm'), (19, 10.5, 'm'), (12.5, 12.5, 'm'), (10, 19, 'm')), L(13, 13, 18.5, 18.5)], 'pointer click select mouse', ['pointer', 'click'])
icon('bug', 'product', [R(7.5, 8.5, 9, 12, 's4.5'), P(('M', 9, 8.5), ('A', 12, 8.5, 3, 180, 360)), L(9.75, 6.25, 8, 4), L(14.25, 6.25, 16, 4), L(7.5, 11.5, 4.5, 9.5), L(7.5, 14.5, 3.5, 14.5),
                        L(7.5, 17.5, 4.5, 19.5), L(16.5, 11.5, 19.5, 9.5), L(16.5, 14.5, 20.5, 14.5), L(16.5, 17.5, 19.5, 19.5), L(12, 11.5, 12, 20.5)], 'issue defect debug error', ['issue', 'debug'])
icon('window', 'product', [R(3, 4, 18, 16), L(3, 8.5, 21, 8.5), D(6, 6.25, 0.75), D(8.5, 6.25, 0.75)], 'browser app web page', ['browser', 'app-window'])
icon('flow', 'product', [R(3, 3.5, 7, 7, fill=True), R(14, 13.5, 7, 7, fill=True), PL((6.5, 10.5), (6.5, 17, 'c'), (14, 17))], 'workflow automation process pipeline', ['workflow', 'automation', 'process'])

# =====================================================================================================
#  DEVICES
# =====================================================================================================
icon('laptop', 'devices', [PL((4.5, 15.5), (4.5, 5, 'c'), (19.5, 5, 'c'), (19.5, 15.5)), PG((4.5, 15.5), (19.5, 15.5), (20.5, 19, 'm'), (3.5, 19, 'm')), FO(PG((4.5, 5), (19.5, 5), (19.5, 15.5), (4.5, 15.5)))],
     'computer notebook online digital', ['computer', 'notebook-computer'])
icon('smartphone', 'devices', [R(6.5, 3, 11, 18), L(11, 17.5, 13, 17.5)], 'mobile phone app cell', ['mobile', 'cellphone'])
icon('tablet', 'devices', [R(4.5, 3, 15, 18), L(10.5, 17.5, 13.5, 17.5)], 'ipad device screen', ['ipad'])
icon('monitor', 'devices', [R(3, 4, 18, 12.5), L(12, 16.5, 12, 20.5), L(8, 20.5, 16, 20.5)], 'desktop screen display', ['desktop', 'display'])
icon('watch', 'devices', [R(6.5, 6.5, 11, 11), PL((8.5, 6.5), (9, 3.5, 'm'), (15, 3.5, 'm'), (15.5, 6.5)), PL((8.5, 17.5), (9, 20.5, 'm'), (15, 20.5, 'm'), (15.5, 17.5)), PL((12, 9.5), (12, 12), (13.5, 13))],
     'smartwatch wearable time', ['smartwatch', 'wearable'])
icon('server', 'devices', [R(3.5, 3.5, 17, 7, fill=True), R(3.5, 13.5, 17, 7, fill=True), D(7, 7), D(7, 17), L(11, 7, 17, 7), L(11, 17, 17, 17)], 'hosting infrastructure cloud backend', ['hosting'])
icon('printer', 'devices', [PL((6.5, 17.5), (3, 17.5, 'c'), (3, 9, 'c'), (21, 9, 'c'), (21, 17.5, 'c'), (17.5, 17.5)), PL((6.5, 9), (6.5, 3.5, 'm'), (17.5, 3.5, 'm'), (17.5, 9)), R(6.5, 13.5, 11, 7.5, 'm', fill=True)],
     'print document office', ['print'])
icon('headphones', 'devices', [A(12, 13, 8.5, 180, 360), R(3.5, 13, 4.5, 7, 's2', fill=True), R(16, 13, 4.5, 7, 's2', fill=True)], 'audio listen music support', ['headset', 'audio-support'])
icon('chip', 'devices', [R(6, 6, 12, 12), R(9.5, 9.5, 5, 5, 'm', fill=False)] + [L(x, 3, x, 6) for x in (9.5, 14.5)] + [L(x, 18, x, 21) for x in (9.5, 14.5)] + [L(3, y, 6, y) for y in (9.5, 14.5)] + [L(18, y, 21, y) for y in (9.5, 14.5)],
     'cpu processor digital technology hardware platform', ['cpu', 'processor', 'digital', 'technology'])

# =====================================================================================================
#  SECURITY
# =====================================================================================================
icon('shield-lock', 'security', [shield(), R(9, 11.5, 6, 5, 'm', fill=False), P(('M', 10.25, 11.5), ('L', 10.25, 10), ('A', 12, 10, 1.75, 180, 360), ('L', 13.75, 11.5))], 'secure protected encryption', ['secure', 'encryption'])
icon('fingerprint', 'security', [P(('M', 9.5, 20), ('L', 9.5, 12.5), ('A', 12, 12.5, 2.5, 180, 360), ('L', 14.5, 15.5)), P(('M', 6.5, 18.5), ('L', 6.5, 12.5), ('A', 12, 12.5, 5.5, 180, 360), ('L', 17.5, 16.5)),
                                 P(('M', 3.5, 15), ('L', 3.5, 12.5), ('A', 12, 12.5, 8.5, 180, 320)), L(12, 14.5, 12, 20.5)], 'biometric identity touch id', ['biometric', 'touch-id'])
icon('password', 'security', [R(3, 7, 18, 10), D(7.5, 12, 1.15), D(12, 12, 1.15), D(16.5, 12, 1.15)], 'pin code passcode login', ['pin-code', 'passcode'])
icon('scan-face', 'security', [PL((3.5, 8), (3.5, 3.5, 'm'), (8, 3.5)), PL((16, 3.5), (20.5, 3.5, 'm'), (20.5, 8)), PL((20.5, 16), (20.5, 20.5, 'm'), (16, 20.5)), PL((8, 20.5), (3.5, 20.5, 'm'), (3.5, 16)),
                               D(9, 10), D(15, 10), A(12, 12, 4, 30, 150)], 'face id recognition biometric', ['face-id'])
icon('cctv', 'security', [PG((3.5, 8.5, 'm'), (14, 4.5, 'm'), (16, 9.5, 'm'), (5.5, 13.5, 'm')), PL((10.5, 11.6), (12, 15.5, 'm'), (20.5, 15.5)), L(20.5, 11.5, 20.5, 19.5)], 'surveillance camera monitoring', ['surveillance'])
icon('firewall', 'security', [R(3, 4, 18, 16), L(3, 9.33, 21, 9.33), L(3, 14.67, 21, 14.67), L(12, 4, 12, 9.33), L(7.5, 9.33, 7.5, 14.67), L(16.5, 9.33, 16.5, 14.67), L(12, 14.67, 12, 20)],
     'wall bricks network protection', ['brick-wall'])
icon('keyhole', 'security', [C(12, 12, 9), C(12, 10, 2.25, fill=True), PL((11, 12), (10.5, 16.25, 'm'), (13.5, 16.25, 'm'), (13, 12))], 'access lock secure entry', ['access'])


# =====================================================================================================
SET_ORDER = ['ui', 'core'] + [k for k in SETS if k not in ('ui', 'core')]


def library():
    names = set(); out = []
    for ic in ICONS:
        if ic['name'] in names: raise SystemExit('duplicate icon name: ' + ic['name'])
        if ic['set'] not in SETS: raise SystemExit('unknown set %s for %s' % (ic['set'], ic['name']))
        names.add(ic['name']); out.append(ic)
    return out


if __name__ == '__main__':
    lib = library()
    from collections import Counter
    c = Counter(ic['set'] for ic in lib)
    print(len(lib), 'icons'); print(dict(c))
