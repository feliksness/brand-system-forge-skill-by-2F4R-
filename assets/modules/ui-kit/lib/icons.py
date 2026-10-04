"""
icons.py — the UI kit's built-in fallback icons (used only when SOURCE/JS/<p>-icons.js is absent or
does not know a name). Drawn on a 24px grid with the DNA stroke (width / cap / join); frames follow the
DNA family: angular brands get chamfered / octagonal frames, round and organic brands get circles.
"""


def icons(R):
    ang = R['family'] == 'angular'
    org = R['family'] == 'organic'
    # frames
    if ang:
        sq = 'M8 3h13v13l-5 5H3V8z'                       # chamfered square (two opposite cuts)
        circ = sq
        octa = 'M8 3h8l5 5v8l-5 5H8l-5-5V8z'
    elif org:
        circ = 'M12 3c5.2 0 9 3.6 9 8.8 0 5.3-3.9 9.2-9.1 9.2C6.7 21 3 17.3 3 12.1 3 6.9 6.8 3 12 3z'   # hand-soft circle
        octa = circ
        sq = 'M8 3h8a5 5 0 0 1 5 5v8a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5V8a5 5 0 0 1 5-5z'
    else:
        circ = 'M12 3a9 9 0 1 1 0 18a9 9 0 1 1 0-18z'
        octa = circ
        sq = 'M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4z'
    P = lambda d: f'<path d="{d}"/>'
    return {
        'chevron': P('M6 9l6 6 6-6'),
        'chevron-down': P('M6 9l6 6 6-6'),
        'chevron-right': P('M9 6l6 6-6 6'),
        'chevron-left': P('M15 6l-6 6 6 6'),
        'close': P('M6 6l12 12M18 6L6 18'),
        'check': P('M4.5 12.5l4.5 4.5L19.5 6.5'),
        'info': P(circ) + P('M12 11v6') + P('M12 7.5v.5'),
        'warning': P('M12 3.5L22 20H2z') + P('M12 10v4.5') + P('M12 17.2v.3'),
        'error': P(octa) + P('M9 9l6 6M15 9l-6 6'),
        'search': (P('M10.5 4a6.5 6.5 0 1 1 0 13a6.5 6.5 0 1 1 0-13z') if not ang else P('M7 4h7l3 3v7l-3 3H7l-3-3V7z')) + P('M15.5 15.5L20 20'),
        'menu': P('M4 7h16M4 12h16M4 17h16') if not org else P('M4 7h16M4 12h12M4 17h16'),
        'plus': P('M12 5v14M5 12h14'),
        'minus': P('M5 12h14'),
        'arrow': P('M4 12h15') + P('M13 6l6 6-6 6'),
        'arrow-right': P('M4 12h15') + P('M13 6l6 6-6 6'),
        'arrow-left': P('M20 12H5') + P('M11 6l-6 6 6 6'),
        'external': P('M14 4h6v6') + P('M20 4l-9 9') + P('M18 14v6H4V6h6'),
        'calendar': P('M4 6h16v14H4z' if ang else 'M6 5h12a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z') + P('M4 10h16M8 3v4M16 3v4'),
        'pin': P('M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z') + P('M12 7.5a2 2 0 1 1 0 4a2 2 0 1 1 0-4z'),
        'clock': P(circ) + P('M12 7.5V12l3 2'),
        'upload': P('M12 16V4') + P('M7 9l5-5 5 5') + P('M4 16v4h16v-4'),
        'user': P('M12 4a4 4 0 1 1 0 8a4 4 0 1 1 0-8z') + P('M4 21c1-4.2 4.2-6 8-6s7 1.8 8 6'),
        'sun': P('M12 8a4 4 0 1 1 0 8a4 4 0 1 1 0-8z') + P('M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4'),
        'moon': P('M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z'),
        'contrast': P(circ) + '<path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none"/>' if not ang else P(circ) + '<path d="M12 3h4l5 5v8l-5 5h-4z" fill="currentColor" stroke="none"/>',
        'auto': P(sq) + P('M8 16l4-9 4 9M9.5 13h5'),
        'settings': P('M12 8.5a3.5 3.5 0 1 1 0 7a3.5 3.5 0 1 1 0-7z') + P('M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1'),
        'copy': P('M9 9h11v11H9z') + P('M5 15H4V4h11v1'),
        'mail': P('M3 6h18v12H3z') + P('M3 7l9 6 9-6'),
        'phone': P('M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z'),
        'dot': P(circ),
        'star': P('M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z'),
        'heart': P('M12 20s-8-4.9-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6.1-8 11-8 11z'),
        'filter': P('M4 5h16l-6 7.5V19l-4 2v-8.5z'),
        'grid': P('M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z'),
    }


# names the brand icon set may use for the same idea (tried in order before falling back)
ALIASES = {
    'chevron': ['chevron-down', 'caret-down', 'chevron'],
    'chevron-down': ['chevron-down', 'caret-down'],
    'arrow-right': ['arrow-right', 'arrow'],
    'settings': ['settings', 'gear', 'cog'],
    'chevron-right': ['chevron-right', 'caret-right'],
    'chevron-left': ['chevron-left', 'caret-left'],
    'close': ['close', 'x', 'cross'],
    'check': ['check', 'tick', 'done'],
    'info': ['info', 'info-circle'],
    'warning': ['warning', 'alert-triangle', 'alert'],
    'error': ['error', 'alert-circle', 'x-circle', 'stop'],
    'search': ['search', 'magnifier'],
    'menu': ['menu', 'hamburger'],
    'plus': ['plus', 'add'],
    'minus': ['minus', 'remove'],
    'arrow': ['arrow-right', 'arrow'],
    'arrow-left': ['arrow-left'],
    'external': ['external', 'external-link', 'arrow-up-right'],
    'calendar': ['calendar', 'date'],
    'pin': ['pin', 'location', 'map-pin', 'place'],
    'clock': ['clock', 'time'],
    'upload': ['upload'],
    'user': ['user', 'person'],
    'sun': ['sun', 'light'],
    'moon': ['moon', 'dark'],
    'contrast': ['contrast'],
    'copy': ['copy'],
    'mail': ['mail', 'email', 'envelope'],
    'phone': ['phone', 'call'],
    'star': ['star'], 'heart': ['heart'], 'filter': ['filter'], 'grid': ['grid'],
}
