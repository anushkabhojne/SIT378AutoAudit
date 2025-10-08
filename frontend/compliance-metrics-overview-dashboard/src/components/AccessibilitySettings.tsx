//components/AccessibilitySettings.tsx

/**
 * AccessibilitySettings.tsx
 * 
 * React component to allow users to configure accessibility preferences,
 * including reduced motion, high contrast mode, and font size scaling.
 * Preferences are persisted in localStorage and applied globally.
 * 
 * @author Senior Lead, AutoAudit
 */

import React, { useEffect, useState } from 'react';

interface AccessibilityPreferences {
  prefersReducedMotion: boolean;
  prefersHighContrast: boolean;

  //1.0 = normal, 1.2 = 20% larger, etc.
  fontSizeScale: number; 
}

const STORAGE_KEY = 'autoAuditAccessibilityPreferences';

const defaultPreferences: AccessibilityPreferences = {
  prefersReducedMotion: false,
  prefersHighContrast: false,
  fontSizeScale: 1.0,
};

/**
 * AccessibilitySettings component
 * 
 * @returns JSX.Element
 */

export const AccessibilitySettings: React.FC = () => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(defaultPreferences);

  //Loading the preferences from localStorage on mount
  useEffect(() => {
    
    try {
      
      const stored = localStorage.getItem(STORAGE_KEY);
      
      if (stored) {
        setPreferences(JSON.parse(stored));
      }
    } 
    
    catch {
      //Ignore JSON parse errors
    }

  }, []);

  //Applying the preferences to document body and persist to localStorage
  useEffect(() => {
    const { prefersReducedMotion, prefersHighContrast, fontSizeScale } = preferences;

    //Reduced motion
    if (prefersReducedMotion) {
      document.body.classList.add('reduced-motion');
    } 
    
    else {
      document.body.classList.remove('reduced-motion');
    }

    //High contrast
    if (prefersHighContrast) {
      document.body.classList.add('high-contrast');
    } 
    
    else {
      document.body.classList.remove('high-contrast');
    }

    //Font size scaling
    document.documentElement.style.fontSize = `${fontSizeScale * 100}%`;

    //Persist preferences
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    } 
    
    catch {
      //Ignore localStorage errors
    }

  }, [preferences]);

  //Handlers for preference changes
  const handleReducedMotionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPreferences((prev) => ({ ...prev, prefersReducedMotion: e.target.checked }));
  };

  const handleHighContrastChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPreferences((prev) => ({ ...prev, prefersHighContrast: e.target.checked }));
  };

  const handleFontSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const scale = Math.min(Math.max(Number(e.target.value), 0.5), 2.0);
    setPreferences((prev) => ({ ...prev, fontSizeScale: scale }));
  };

  return (
    <section aria-label = "Accessibility Settings" className = "accessibility-settings">
      <h2>Accessibility Settings</h2>
      <form>
        <div>
          <input
            type = "checkbox"
            id = "reducedMotion"
            checked = {preferences.prefersReducedMotion}
            onChange = {handleReducedMotionChange}
          />
          <label htmlFor = "reducedMotion">Reduce Motion</label>
        </div>
        <div>
          <input
            type = "checkbox"
            id = "highContrast"
            checked = {preferences.prefersHighContrast}
            onChange = {handleHighContrastChange}
          />
          <label htmlFor = "highContrast">High Contrast Mode</label>
        </div>
        <div>
          <label htmlFor = "fontSizeScale">Font Size: {Math.round(preferences.fontSizeScale * 100)}%</label>
          <input
            type = "range"
            id = "fontSizeScale"
            min = {0.5}
            max = {2.0}
            step = {0.1}
            value = {preferences.fontSizeScale}
            onChange = {handleFontSizeChange}
            aria-valuemin = {0.5}
            aria-valuemax = {2.0}
            aria-valuenow = {preferences.fontSizeScale}
            aria-valuetext = {`${Math.round(preferences.fontSizeScale * 100)} percent`}
          />
        </div>
      </form>
    </section>
  );
};
