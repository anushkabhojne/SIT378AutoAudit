//hooks/useAccessibilityPreferences.ts

/**
 * useAccessibilityPreferences.ts
 * 
 * Custom React hook to detect and manage user accessibility preferences.
 * Supports preferences such as reduced motion, high contrast mode, and font size scaling.
 * Provides reactive updates when preferences change.
 * 
 * @author Senior Lead, AutoAudit
 */

import { useState, useEffect, useCallback } from 'react';

export interface AccessibilityPreferences {
  
  prefersReducedMotion: boolean;
  prefersHighContrast: boolean;

  //e.g., 1.0 = normal, 1.2 = 20% larger
  fontSizeScale: number; 
}

/**
 * useAccessibilityPreferences hook implementation
 * 
 * Detecting the user accessibility preferences and updating reactively.
 */

export function useAccessibilityPreferences(): AccessibilityPreferences {
  
  //Detecting prefers-reduced-motion media query
  const getPrefersReducedMotion = () =>
    window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  //Detecting prefers-contrast media query (high contrast)
  //Note: 'prefers-contrast' is experimental; fallback to false if unsupported
  const getPrefersHighContrast = () =>
    window.matchMedia && window.matchMedia('(prefers-contrast: more)').matches;

  //Detecting font size scaling from browser zoom or user settings
  //Approximate by comparing window.devicePixelRatio or computed font size
  const getFontSizeScale = () => {
    
    //Default scale 1.0
    //Use computed font size of body relative to 16px base
    const baseFontSize = 16;
    
    const bodyFontSize = parseFloat(
      window.getComputedStyle(document.body).fontSize || `${baseFontSize}px`
    );

    return bodyFontSize / baseFontSize;
  };

  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    prefersReducedMotion: getPrefersReducedMotion(),
    prefersHighContrast: getPrefersHighContrast(),
    fontSizeScale: getFontSizeScale(),
  });

  useEffect(() => {
    //Media query lists
    const reducedMotionMQ = window.matchMedia('(prefers-reduced-motion: reduce)');
    const highContrastMQ = window.matchMedia('(prefers-contrast: more)');

    //Handlers to update state on media query changes
    const handleReducedMotionChange = (event: MediaQueryListEvent) => {
      setPreferences((prev) => ({ ...prev, prefersReducedMotion: event.matches }));
    };
    const handleHighContrastChange = (event: MediaQueryListEvent) => {
      setPreferences((prev) => ({ ...prev, prefersHighContrast: event.matches }));
    };

    //Adding listeners
    if (reducedMotionMQ.addEventListener) {
      reducedMotionMQ.addEventListener('change', handleReducedMotionChange);
    } 
    
    else {
      //Safari fallback
      reducedMotionMQ.addListener(handleReducedMotionChange);
    }


    if (highContrastMQ.addEventListener) {
      highContrastMQ.addEventListener('change', handleHighContrastChange);
    } 
    
    else {
      highContrastMQ.addListener(handleHighContrastChange);
    }

    //Resizing the listener to detect font size changes (zoom or user scaling)
    const handleResize = () => {
      setPreferences((prev) => ({ ...prev, fontSizeScale: getFontSizeScale() }));
    };

    window.addEventListener('resize', handleResize);

    //Cleaning up the listeners on unmount
    return () => {
      
      if (reducedMotionMQ.removeEventListener) {
        reducedMotionMQ.removeEventListener('change', handleReducedMotionChange);
      } 
      
      else {
        reducedMotionMQ.removeListener(handleReducedMotionChange);
      }


      if (highContrastMQ.removeEventListener) {
        highContrastMQ.removeEventListener('change', handleHighContrastChange);
      } 
      
      else {
        highContrastMQ.removeListener(handleHighContrastChange);
      }
      window.removeEventListener('resize', handleResize);
      
    };
  }, []);

  return preferences;
}
