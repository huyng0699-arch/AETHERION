import { useCallback, useEffect, useRef } from 'react';
// Results from older requests, superseded searches, or an unmounted screen are ignored.
export function useRequestGate() {
  const version = useRef(0);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; version.current += 1; }; }, []);
  return useCallback(() => { const id = ++version.current; return () => mounted.current && version.current === id; }, []);
}
