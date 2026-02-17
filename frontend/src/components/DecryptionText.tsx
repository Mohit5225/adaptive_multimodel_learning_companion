'use client';

import { useEffect, useState, useRef } from 'react';

const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;:,.<>?";

type DecryptionTextProps = {
  text: string;
  speed?: number;
  maxIterations?: number;
  className?: string;
  animateOnHover?: boolean;
  revealDirection?: 'start' | 'end' | 'center' | 'random';
  useOriginalCharsOnly?: boolean; 
};

export const DecryptionText = ({ 
  text, 
  speed = 30, 
  maxIterations = 10, 
  className = "",
  animateOnHover = false,
  revealDirection = 'start',
  useOriginalCharsOnly = false
}: DecryptionTextProps) => {
  const [displayText, setDisplayText] = useState(text);
  const [isHovering, setIsHovering] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (animateOnHover && !isHovering) {
        setDisplayText(text);
        return;
    }

    let iteration = 0;

    const runEffect = () => {
        if (intervalRef.current) clearInterval(intervalRef.current);

        intervalRef.current = setInterval(() => {
            setDisplayText(prev => 
                text
                .split("")
                .map((char, index) => {
                    if (index < iteration) {
                        return text[index];
                    }
                    return CHARS[Math.floor(Math.random() * CHARS.length)];
                })
                .join("")
            );

            if (iteration >= text.length) {
                if (intervalRef.current) clearInterval(intervalRef.current);
            }

            iteration += 1 / 3; 
        }, speed);
    };

    runEffect();

    return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [text, speed, isHovering, animateOnHover]);

  return (
    <span 
      className={`font-mono-tech ${className}`}
      onMouseEnter={() => animateOnHover && setIsHovering(true)}
      onMouseLeave={() => animateOnHover && setIsHovering(false)}
    >
      {displayText}
    </span>
  );
};
