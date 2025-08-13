<<<<<<< HEAD
"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
  blurDataURL?: string;
  priority?: boolean;
  onLoad?: () => void;
  onError?: () => void;
=======
'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

interface LazyImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  blurDataURL?: string
  priority?: boolean
  onLoad?: () => void
  onError?: () => void
>>>>>>> main
}

export default function LazyImage({
  src,
  alt,
<<<<<<< HEAD
  className = "",
=======
  className = '',
>>>>>>> main
  width,
  height,
  blurDataURL,
  priority = false,
  onLoad,
<<<<<<< HEAD
  onError,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (priority) return;
=======
  onError
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(priority)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  useEffect(() => {
    if (priority) return
>>>>>>> main

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
<<<<<<< HEAD
          setIsInView(true);
          observer.disconnect();
=======
          setIsInView(true)
          observer.disconnect()
>>>>>>> main
        }
      },
      {
        threshold: 0.1,
<<<<<<< HEAD
        rootMargin: "50px",
      },
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [priority]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  return (
    <div
=======
        rootMargin: '50px'
      }
    )

    if (imgRef.current) {
      observer.observe(imgRef.current)
    }

    return () => observer.disconnect()
  }, [priority])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  return (
    <div 
>>>>>>> main
      className={`relative overflow-hidden ${className}`}
      style={{ width, height }}
    >
      {/* Placeholder/Loading State */}
      <motion.div
        className="absolute inset-0 bg-slate-800 animate-pulse"
        initial={{ opacity: 1 }}
        animate={{ opacity: isLoaded ? 0 : 1 }}
        transition={{ duration: 0.3 }}
        style={{
          backgroundImage: blurDataURL ? `url(${blurDataURL})` : undefined,
<<<<<<< HEAD
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(5px)",
          transform: "scale(1.1)",
=======
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          filter: 'blur(5px)',
          transform: 'scale(1.1)'
>>>>>>> main
        }}
      />

      {/* Actual Image */}
      {(isInView || priority) && !hasError && (
        <motion.img
          ref={imgRef}
          src={src}
          alt={alt}
          className="absolute inset-0 w-full h-full object-cover"
          onLoad={handleLoad}
          onError={handleError}
          initial={{ opacity: 0 }}
          animate={{ opacity: isLoaded ? 1 : 0 }}
          transition={{ duration: 0.3 }}
<<<<<<< HEAD
          loading={priority ? "eager" : "lazy"}
=======
          loading={priority ? 'eager' : 'lazy'}
>>>>>>> main
          decoding="async"
        />
      )}

      {/* Error State */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-800 text-slate-400">
          <div className="text-center">
            <div className="text-2xl mb-2">📷</div>
            <div className="text-sm">Failed to load image</div>
          </div>
        </div>
      )}
    </div>
<<<<<<< HEAD
  );
}
=======
  )
}
>>>>>>> main
