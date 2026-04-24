import { useState, useCallback, useEffect, useRef, type RefObject } from "react";

/**
 * Auto-scroll the given scrollable element to its bottom whenever
 * `scrollTrigger` changes, but only while the user is already near
 * the bottom (within 100px). If the user has scrolled up past the
 * threshold, the hook stops force-scrolling so it does not yank the
 * viewport away from whatever the user is reading.
 *
 * `forceFollowBottom()` re-latches the state to "follow" — used when
 * the user submits a new message, where we always want to reveal the
 * incoming turn regardless of prior scroll position.
 */
export function useFollowBottom(ref: RefObject<HTMLElement | null>, scrollTrigger: unknown) {
  const [shouldFollowBottom, setShouldFollow] = useState(true);

  const handleScroll = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShouldFollow(distance < 100);
  }, [ref]);

  const forceFollowBottom = useCallback(() => setShouldFollow(true), []);

  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    if (!shouldFollowBottom) return;
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [ref, shouldFollowBottom, scrollTrigger]);

  return { shouldFollowBottom, handleScroll, forceFollowBottom };
}
