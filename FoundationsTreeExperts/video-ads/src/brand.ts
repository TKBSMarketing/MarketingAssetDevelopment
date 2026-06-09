// Foundations Tree Experts — brand tokens (pulled from the live website's global.css)
// Palette: deep forest / cream / charcoal / warm bark. Type: Source Serif 4 + DM Sans.

export const brand = {
  // Backgrounds (forest scale)
  bgDeep: "oklch(0.18 0.05 230)",
  bg: "oklch(0.22 0.06 230)",
  bgLight: "oklch(0.30 0.08 230)",

  // Text
  cream: "oklch(0.985 0.012 85)",
  creamDim: "oklch(0.9 0.028 80)",

  // Accents
  bark: "oklch(0.62 0.11 52)",
  ember: "oklch(0.62 0.18 35)",
  star: "#F2B541",

  // Contact / CTA
  phone: "(734) 474-3336",
  website: "foundationstreeexperts.com",
} as const;

export type Testimonial = {
  quote: string;
  name: string;
  stars: number;
};

// Real, verified 5-star Google reviews (from the website's testimonials.json).
// The 3 punchiest, trimmed to read in ~3 seconds each on screen.
export const defaultTestimonials: Testimonial[] = [
  {
    quote:
      "Professional, fast and polite. I will never use any other company. I just wish all companies were as good as these guys.",
    name: "Eddie K.",
    stars: 5,
  },
  {
    quote:
      "The cleanup exceeded expectations. They were always on time, very friendly, and worked hard.",
    name: "James B.",
    stars: 5,
  },
  {
    quote: "They were perfect. Cleaned everything up. I love these guys!",
    name: "Dominique B.",
    stars: 5,
  },
];
