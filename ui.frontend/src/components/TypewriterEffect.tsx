import React, { useState, useEffect, useRef } from 'react';

interface TypewriterEffectProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

export const TypewriterEffect: React.FC<TypewriterEffectProps> = ({ text, speed = 50, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('');
  const onCompleteRef = useRef(onComplete);

  // Update ref when prop changes, but don't restart effect
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    console.log('[Typewriter] Starting effect for text length:', text.length);
    let i = 0;
    setDisplayedText('');
    
    if (!text) {
      console.log('[Typewriter] Empty text, completing immediately');
      if (onCompleteRef.current) onCompleteRef.current();
      return;
    }

    const timer = setInterval(() => {
      if (i < text.length) {
        const char = text.charAt(i);
        setDisplayedText((prev) => prev + char);
        i++;
      } else {
        console.log('[Typewriter] Finished typing');
        clearInterval(timer);
        if (onCompleteRef.current) onCompleteRef.current();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed]); // Removed onComplete from dependency

  return <>{displayedText}</>;
};
