import { act } from "@testing-library/react";

const observers = new Set<FakeIntersectionObserver>();

/**
 * jsdom has no layout, so nothing ever scrolls into view by itself. A test moves an element in
 * or out of view with `scrollIntoViewport()` and `scrollOutOfViewport()`.
 */
class FakeIntersectionObserver implements IntersectionObserver {
  readonly root = null;
  readonly rootMargin: string;
  readonly thresholds: readonly number[] = [0];
  readonly scrollMargin = "0px";
  readonly elements = new Set<Element>();

  constructor(
    private readonly callback: IntersectionObserverCallback,
    options: IntersectionObserverInit = {},
  ) {
    this.rootMargin = options.rootMargin ?? "0px";
    observers.add(this);
  }

  observe(element: Element): void {
    this.elements.add(element);
  }

  unobserve(element: Element): void {
    this.elements.delete(element);
  }

  disconnect(): void {
    this.elements.clear();
    observers.delete(this);
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  report(element: Element, isIntersecting: boolean): void {
    const entry = { target: element, isIntersecting } as IntersectionObserverEntry;
    this.callback([entry], this);
  }
}

function report(element: Element, isIntersecting: boolean): void {
  act(() => {
    for (const observer of observers) {
      if (observer.elements.has(element)) {
        observer.report(element, isIntersecting);
      }
    }
  });
}

export function scrollIntoViewport(element: Element): void {
  report(element, true);
}

export function scrollOutOfViewport(element: Element): void {
  report(element, false);
}

export function installIntersectionObserver(): void {
  globalThis.IntersectionObserver = FakeIntersectionObserver;
}
