# Typography Guidelines: AI Agent Collaboration Platform

## Font Family System

### Primary Font: Inter
**Usage**: Headings, body text, UI elements
**Rationale**: Modern, highly legible, excellent for digital interfaces
**Fallbacks**: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

### Monospace Font: JetBrains Mono
**Usage**: Code snippets, technical documentation, terminal output
**Rationale**: Developer-friendly, excellent readability for code
**Fallbacks**: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace

### Display Font: Cal Sans
**Usage**: Hero headlines, brand statements, large displays
**Rationale**: Modern, distinctive, maintains readability at scale
**Fallbacks**: Inter, -apple-system, BlinkMacSystemFont, sans-serif

## Type Scale

### Heading Scale (1.250 ratio)
```css
/* Display */
.display-1: 4.5rem (72px) / 1.1 / 700
.display-2: 3.75rem (60px) / 1.1 / 700
.display-3: 3rem (48px) / 1.1 / 700

/* Headings */
.h1: 2.25rem (36px) / 1.2 / 700
.h2: 1.875rem (30px) / 1.2 / 600
.h3: 1.5rem (24px) / 1.3 / 600
.h4: 1.25rem (20px) / 1.4 / 600
.h5: 1.125rem (18px) / 1.4 / 600
.h6: 1rem (16px) / 1.4 / 600
```

### Body Scale (1.125 ratio)
```css
/* Body Text */
.body-xl: 1.25rem (20px) / 1.6 / 400
.body-lg: 1.125rem (18px) / 1.6 / 400
.body: 1rem (16px) / 1.6 / 400
.body-sm: 0.875rem (14px) / 1.6 / 400
.body-xs: 0.75rem (12px) / 1.6 / 400

/* Caption */
.caption: 0.75rem (12px) / 1.4 / 500
.caption-sm: 0.625rem (10px) / 1.4 / 500
```

### Code Scale
```css
/* Code Text */
.code-lg: 1.125rem (18px) / 1.4 / 400
.code: 1rem (16px) / 1.4 / 400
.code-sm: 0.875rem (14px) / 1.4 / 400
.code-xs: 0.75rem (12px) / 1.4 / 400
```

## Font Weights

### Available Weights
- **100**: Thin (Ultra Light)
- **200**: Extra Light
- **300**: Light
- **400**: Regular (Normal)
- **500**: Medium
- **600**: Semi Bold
- **700**: Bold
- **800**: Extra Bold
- **900**: Black (Ultra Bold)

### Usage Guidelines
- **400**: Body text, paragraphs, general content
- **500**: Emphasis, captions, secondary information
- **600**: Subheadings, form labels, navigation
- **700**: Main headings, call-to-action buttons
- **800**: Hero headlines, display text
- **900**: Reserved for special emphasis only

## Line Heights & Spacing

### Line Height Guidelines
- **Headings**: 1.1 - 1.3 (tight, impactful)
- **Body Text**: 1.5 - 1.7 (comfortable reading)
- **Code**: 1.4 - 1.5 (compact but readable)
- **Captions**: 1.4 (tight but legible)

### Letter Spacing
- **Headings**: -0.025em (tight, modern)
- **Body Text**: 0 (normal)
- **Code**: 0 (normal)
- **All Caps**: 0.1em (improved readability)

### Paragraph Spacing
- **Tight**: 1rem (16px) between paragraphs
- **Normal**: 1.5rem (24px) between paragraphs
- **Loose**: 2rem (32px) between paragraphs

## Accessibility Standards

### WCAG AA Compliance
- **Minimum contrast ratio**: 4.5:1 for normal text
- **Large text contrast ratio**: 3:1 for text 18px+ or 14px+ bold
- **All our color combinations meet AA standards**

### Readability Guidelines
- **Minimum body text size**: 16px (1rem)
- **Maximum line length**: 65-75 characters
- **Minimum line height**: 1.5 for body text
- **Avoid all caps for long text blocks**

### Screen Reader Support
- **Semantic HTML**: Use proper heading hierarchy (h1-h6)
- **Alt text**: Provide descriptive alt text for images
- **Focus indicators**: Clear focus states for keyboard navigation
- **Skip links**: Provide skip navigation for main content

## Implementation Examples

### CSS Variables
```css
:root {
  /* Font Families */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', monospace;
  --font-display: 'Cal Sans', 'Inter', sans-serif;
  
  /* Font Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;
  
  /* Line Heights */
  --leading-tight: 1.1;
  --leading-snug: 1.3;
  --leading-normal: 1.5;
  --leading-relaxed: 1.7;
  
  /* Font Weights */
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
}
```

### Component Examples
```css
/* Hero Heading */
.hero-heading {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.025em;
}

/* Body Text */
.body-text {
  font-family: var(--font-primary);
  font-size: var(--text-lg);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
  max-width: 65ch;
}

/* Code Block */
.code-block {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-snug);
  background: var(--color-gray-100);
  padding: 1rem;
  border-radius: 0.5rem;
}
```

## Responsive Typography

### Mobile-First Approach
```css
/* Base (mobile) */
.hero-heading {
  font-size: 2rem; /* 32px */
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .hero-heading {
    font-size: 2.5rem; /* 40px */
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .hero-heading {
    font-size: 3rem; /* 48px */
  }
}

/* Large Desktop (1280px+) */
@media (min-width: 1280px) {
  .hero-heading {
    font-size: 3.75rem; /* 60px */
  }
}
```

### Fluid Typography (Alternative)
```css
.hero-heading {
  font-size: clamp(2rem, 5vw, 3.75rem);
  line-height: 1.1;
}
```

## Brand Voice Typography

### Confident & Intelligent
- **Bold headings** for authority
- **Clean, modern fonts** for professionalism
- **Generous spacing** for readability

### Collaborative & Human
- **Warm, approachable weights** (400-600 for body)
- **Comfortable line heights** for extended reading
- **Consistent hierarchy** for clear communication

### Technical Excellence
- **Monospace fonts** for code and technical content
- **Precise sizing** for UI elements
- **Accessibility-first** approach

## Testing & Validation

### Contrast Testing
- Use WebAIM contrast checker
- Test with colorblind simulation tools
- Verify against WCAG AA standards

### Readability Testing
- Test on various screen sizes
- Validate with screen readers
- Check font rendering across platforms

### Performance Testing
- Optimize font loading
- Use font-display: swap
- Implement font preloading for critical fonts

## Font Loading Strategy

### Critical Fonts
```html
<link rel="preload" href="/fonts/Inter-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/Inter-Bold.woff2" as="font" type="font/woff2" crossorigin>
```

### Font Display
```css
@font-face {
  font-family: 'Inter';
  font-display: swap;
  src: url('/fonts/Inter-Regular.woff2') format('woff2');
}
```

### Fallback Strategy
```css
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

## Maintenance & Updates

### Version Control
- Document font version changes
- Test new fonts thoroughly
- Maintain fallback compatibility

### Performance Monitoring
- Track font loading times
- Monitor Core Web Vitals
- Optimize based on user data

### Accessibility Audits
- Regular contrast testing
- Screen reader compatibility
- Keyboard navigation support