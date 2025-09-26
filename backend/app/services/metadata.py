from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .stores import detect_store

PRICE_RE = re.compile(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


def _normalize_price(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.lower().startswith("r$"):
        prefix, rest = cleaned[:2], cleaned[2:]
        rest = rest.strip()
        cleaned = f"{prefix} {rest}" if rest else prefix
    return cleaned


def _find_price_candidates(text: str) -> list[str]:
    return list(dict.fromkeys(PRICE_RE.findall(text)))


def _extract_title(soup: BeautifulSoup) -> str | None:
    primary = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
    if primary and primary.get("content"):
        return primary["content"].strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.select_one("h1")
    if h1 and h1.text:
        return h1.text.strip()
    return None


def _extract_image(soup: BeautifulSoup) -> str | None:
    meta = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    img = soup.find("img")
    if img and img.get("src"):
        return img["src"].strip()
    return None


def _extract_amazon_prices(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    selectors = [
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "span.apexPriceToPay span.a-offscreen",
        "span.a-price[data-a-size=\"l\"] span.a-offscreen",
        "span.a-price[data-a-size=\"xl\"] span.a-offscreen",
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if el and el.text.strip():
            sale = _normalize_price(el.text)
            break
    else:
        sale = None

    strike_selectors = [
        "#priceblock_strikeprice",
        "span.a-price.a-text-price span.a-offscreen",
        "span[data-a-color=\"secondary\"] span.a-offscreen",
    ]
    for selector in strike_selectors:
        el = soup.select_one(selector)
        if el and el.text.strip():
            original = _normalize_price(el.text)
            break
    else:
        original = None

    return sale, original


def _extract_ml_prices(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    price_el = soup.select_one("meta[name='twitter:data1']")
    price = _normalize_price(price_el.get("content")) if price_el else None
    installment = soup.select_one("meta[name='twitter:data2']")
    if installment and installment.get("content"):
        price = _normalize_price(installment.get("content")) or price
    strike_el = soup.find("span", attrs={"class": re.compile("price-tag-strike")})
    strike = _normalize_price(strike_el.text) if strike_el else None
    return price, strike


def _extract_generic_prices(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    text = soup.get_text(" ", strip=True)
    candidates = _find_price_candidates(text)
    if candidates:
        return _normalize_price(candidates[0]), _normalize_price(candidates[1]) if len(candidates) > 1 else None
    return None, None


def _extract_benefits(soup: BeautifulSoup) -> list[str]:
    benefits: list[str] = []
    bullets = soup.select("ul li")
    for li in bullets[:5]:
        text = li.get_text(" ", strip=True)
        if text and len(text) <= 140:
            benefits.append(f"• {text}")
    return benefits


def _extract_installment(text: str) -> str | None:
    match = re.search(r"(\d{1,2})x\s+de\s+(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})", text)
    if match:
        qty, value = match.groups()
        return f"💳 {qty}x de {value} sem juros"
    return None


async def fetch_metadata(url: str, store: str | None = None) -> dict[str, Any]:
    store = store or detect_store(url)
    async with httpx.AsyncClient(timeout=12.0, headers=HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")
    title = _extract_title(soup) or "Produto"
    image = _extract_image(soup)

    if store == "amazon":
        price_current, price_original = _extract_amazon_prices(soup)
    elif store == "mercadolivre":
        price_current, price_original = _extract_ml_prices(soup)
    else:
        price_current, price_original = _extract_generic_prices(soup)

    text = soup.get_text(" ", strip=True)
    installment = _extract_installment(text)

    benefits = _extract_benefits(soup)
    if installment and installment not in benefits:
        benefits.append(installment)

    candidates = _find_price_candidates(text)

    return {
        "store": store,
        "title": title,
        "image": image,
        "price": price_current,
        "price_original": price_original,
        "benefits": benefits,
        "raw_prices": candidates,
        "raw_text_excerpt": text[:1000],
    }
