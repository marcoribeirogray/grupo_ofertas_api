from __future__ import annotations

import random

CATEGORY_RULES = [
    ("beleza", ["desodorante", "antitranspirante", "higiene"], ["🧴", "🧼", "💦"], [
        "Suor? Só se for de alegria com esse preço.",
        "Proteção no sovaco e no bolso — blindagem dupla.",
        "Adeus cheiro ruim, olá desconto bonito."
    ]),
    ("suplementos", ["creatina", "whey", "suplemento"], ["🏋️", "⚡", "💪"], [
        "PR no treino e PB no bolso.",
        "Energia pra levantar peso e derrubar valor.",
        "Ganho seco no bíceps e no carrinho."
    ]),
    ("tv", ["smart tv", "4k", "thinq", "webos", "uhd"], ["📺", "✨", "🎬"], [
        "Cinema na sala, preço sem drama.",
        "Resolução 4K com promoção igualmente nítida.",
        "Maratona de série e de desconto."
    ]),
    ("cozinha", ["fritadeira", "air fryer", "cozinha"], ["🍟", "🍔", "👩‍🍳"], [
        "Crocância garantida, preço em dieta.",
        "Frita a batata, derrete o valor.",
        "Chef feliz, carteira sorrindo."
    ]),
]

GENERIC_EMOJIS = ["✨", "🔥", "🛒"]
GENERIC_LINES = [
    "Economia tão boa que até o algoritmo sorriu.",
    "Desconto desses até carrinho abandonado volta.",
    "Promoção piscou, piscou de volta e levou."
]


def headline_for(title: str | None) -> tuple[str, str]:
    lower = (title or "").lower()
    for _, keywords, emojis, lines in CATEGORY_RULES:
        if any(keyword in lower for keyword in keywords):
            return random.choice(emojis), random.choice(lines)
    return random.choice(GENERIC_EMOJIS), random.choice(GENERIC_LINES)
