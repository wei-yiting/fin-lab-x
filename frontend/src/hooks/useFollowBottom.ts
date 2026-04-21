import { useState, useCallback, type RefObject } from "react";

export function useFollowBottom(ref: RefObject<HTMLElement | null>) {
  const [shouldFollowBottom, setShouldFollow] = useState(true);
  const handleScroll = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShouldFollow(distance < 100);
  }, [ref]);
  const forceFollowBottom = useCallback(() => setShouldFollow(true), []);
  return { shouldFollowBottom, handleScroll, forceFollowBottom };
}
