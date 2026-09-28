// Phone-only behavior. Layout changes live in styles.css; this covers what CSS can't do.

export const PHONE = "(max-width: 700px)"; // keep in step with the @media block in styles.css

export const isPhone = () => window.matchMedia(PHONE).matches;

/** On phones, scroll the page so `el`'s top sits just under the viewport top, unless it is already
 * fully visible. Used after a list tap so the panel it updates comes into view. */
export function revealOnPhone(el: HTMLElement | null) {
  if (!el || !isPhone()) return;
  const box = el.getBoundingClientRect();
  if (box.top >= 0 && box.bottom <= window.innerHeight) return;
  window.scrollTo({ top: box.top + window.scrollY - 8, behavior: "smooth" });
}

/** Scroll a horizontal strip so `item` is in view, without touching the page's vertical scroll
 * (unlike scrollIntoView). No-op when the strip doesn't overflow, e.g. on desktop. */
export function revealInStrip(strip: HTMLElement | null, item: HTMLElement | null) {
  if (!strip || !item || strip.scrollWidth <= strip.clientWidth) return;
  const left = item.getBoundingClientRect().left - strip.getBoundingClientRect().left + strip.scrollLeft;
  const right = left + item.offsetWidth;
  if (left >= strip.scrollLeft && right <= strip.scrollLeft + strip.clientWidth) return;
  strip.scrollTo({ left: left - (strip.clientWidth - item.offsetWidth) / 2, behavior: "smooth" });
}
