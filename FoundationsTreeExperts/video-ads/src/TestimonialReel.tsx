import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import { loadFont as loadSerif } from "@remotion/google-fonts/SourceSerif4";
import { loadFont as loadSans } from "@remotion/google-fonts/DMSans";
import { brand, defaultTestimonials, type Testimonial } from "./brand";

const { fontFamily: serif } = loadSerif();
const { fontFamily: sans } = loadSans();

export type TestimonialReelProps = {
  testimonials: Testimonial[];
  phone: string;
  website: string;
  /** Optional file in public/ — e.g. "music.mp3". Leave empty to render silent. */
  musicSrc: string;
};

export const testimonialReelDefaults: TestimonialReelProps = {
  testimonials: defaultTestimonials,
  phone: brand.phone,
  website: brand.website,
  musicSrc: "music.mp3",
};

const EASE = Easing.bezier(0.16, 1, 0.3, 1);

// ---------- Background: slow forest drift (motion in the first 2 seconds) ----------
const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1.08, 1.18]);
  const drift = interpolate(frame, [0, durationInFrames], [-20, 20]);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(120% 90% at 50% 18%, ${brand.bgLight} 0%, ${brand.bg} 45%, ${brand.bgDeep} 100%)`,
      }}
    >
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translateY(${drift}px)`,
          background: `radial-gradient(40% 30% at 78% 12%, ${brand.bgLight}55 0%, transparent 60%)`,
        }}
      />
    </AbsoluteFill>
  );
};

const GoogleG: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 48 48">
    <path
      fill="#EA4335"
      d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
    />
    <path
      fill="#4285F4"
      d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
    />
    <path
      fill="#FBBC05"
      d="M10.53 28.59A14.5 14.5 0 019.5 24c0-1.59.28-3.14.76-4.59l-7.98-6.19A23.99 23.99 0 000 24c0 3.77.9 7.35 2.56 10.78l7.97-6.19z"
    />
    <path
      fill="#34A853"
      d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
    />
  </svg>
);

const Star: React.FC<{ delay: number }> = ({ delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - delay, fps, config: { damping: 12, mass: 0.5 } });
  return (
    <svg
      width={64}
      height={64}
      viewBox="0 0 24 24"
      style={{ transform: `scale(${pop})`, filter: "drop-shadow(0 2px 8px #00000040)" }}
    >
      <path
        fill={brand.star}
        d="M12 2l2.9 6.2 6.8.9-5 4.7 1.3 6.8L12 17.8 5.9 20.6l1.3-6.8-5-4.7 6.8-.9z"
      />
    </svg>
  );
};

const Stars: React.FC<{ count: number; baseDelay: number }> = ({ count, baseDelay }) => (
  <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
    {Array.from({ length: count }).map((_, i) => (
      <Star key={i} delay={baseDelay + i * 4} />
    ))}
  </div>
);

// ---------- Intro hook ----------
const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logoIn = spring({ frame, fps, config: { damping: 14 } });
  const lineOpacity = interpolate(frame, [12, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const lineY = interpolate(frame, [12, 36], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 80 }}>
      <Img
        src={staticFile("logo.png")}
        style={{ width: 360, transform: `scale(${logoIn})`, marginBottom: 56 }}
      />
      <div
        style={{
          fontFamily: sans,
          fontSize: 38,
          letterSpacing: 6,
          textTransform: "uppercase",
          color: brand.bark,
          opacity: lineOpacity,
          transform: `translateY(${lineY}px)`,
          fontWeight: 600,
        }}
      >
        Ann Arbor, Michigan
      </div>
      <div
        style={{
          fontFamily: serif,
          fontSize: 92,
          lineHeight: 1.05,
          textAlign: "center",
          color: brand.cream,
          marginTop: 28,
          opacity: lineOpacity,
          transform: `translateY(${lineY}px)`,
          fontWeight: 600,
        }}
      >
        26 years.
        <br />
        Hundreds of
        <br />
        five-star reviews.
      </div>
    </AbsoluteFill>
  );
};

// ---------- One testimonial card ----------
const Card: React.FC<{ t: Testimonial; durationInFrames: number }> = ({ t, durationInFrames }) => {
  const frame = useCurrentFrame();
  const fadeIn = interpolate(frame, [0, 14], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const fadeOut = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const quoteY = interpolate(frame, [6, 28], [50, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const opacity = Math.min(fadeIn, fadeOut);

  return (
    <AbsoluteFill
      style={{ alignItems: "center", justifyContent: "center", padding: "0 110px", opacity }}
    >
      <Stars count={t.stars} baseDelay={8} />
      <div
        style={{
          fontFamily: serif,
          fontSize: 70,
          lineHeight: 1.28,
          textAlign: "center",
          color: brand.cream,
          marginTop: 56,
          transform: `translateY(${quoteY}px)`,
          fontWeight: 500,
        }}
      >
        <span style={{ color: brand.bark }}>“</span>
        {t.quote}
        <span style={{ color: brand.bark }}>”</span>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginTop: 56,
        }}
      >
        <GoogleG size={40} />
        <span
          style={{
            fontFamily: sans,
            fontSize: 40,
            color: brand.creamDim,
            fontWeight: 600,
          }}
        >
          {t.name}
        </span>
        <span
          style={{
            fontFamily: sans,
            fontSize: 28,
            letterSpacing: 2,
            textTransform: "uppercase",
            color: brand.bark,
            fontWeight: 600,
          }}
        >
          · Verified review
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ---------- End card (website-forward CTA) ----------
const EndCard: React.FC<{ phone: string; website: string }> = ({ phone, website }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const logoIn = spring({ frame, fps, config: { damping: 14 } });
  const ctaOpacity = interpolate(frame, [10, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  const ctaY = interpolate(frame, [10, 32], [40, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE,
  });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: 80 }}>
      <Img src={staticFile("logo.png")} style={{ width: 320, transform: `scale(${logoIn})` }} />
      <div
        style={{
          fontFamily: serif,
          fontSize: 82,
          color: brand.cream,
          marginTop: 48,
          textAlign: "center",
          opacity: ctaOpacity,
          transform: `translateY(${ctaY}px)`,
          fontWeight: 600,
        }}
      >
        Book your free estimate
      </div>
      <div
        style={{
          fontFamily: sans,
          fontSize: 56,
          color: brand.star,
          marginTop: 40,
          fontWeight: 700,
          opacity: ctaOpacity,
          transform: `translateY(${ctaY}px)`,
        }}
      >
        {website}
      </div>
      <div
        style={{
          fontFamily: sans,
          fontSize: 38,
          letterSpacing: 2,
          color: brand.creamDim,
          marginTop: 20,
          opacity: ctaOpacity,
          transform: `translateY(${ctaY}px)`,
        }}
      >
        or call {phone} · ISA Certified Arborist
      </div>
    </AbsoluteFill>
  );
};

export const TestimonialReel: React.FC<TestimonialReelProps> = ({
  testimonials,
  phone,
  website,
  musicSrc,
}) => {
  const { durationInFrames } = useVideoConfig();
  const introLen = 66;
  const endLen = 84;
  const cardsTotal = durationInFrames - introLen - endLen;
  const cardLen = Math.floor(cardsTotal / testimonials.length);

  return (
    <AbsoluteFill>
      <Background />

      <Sequence durationInFrames={introLen} layout="none">
        <Intro />
      </Sequence>

      {testimonials.map((t, i) => (
        <Sequence
          key={i}
          from={introLen + i * cardLen}
          durationInFrames={cardLen}
          layout="none"
        >
          <Card t={t} durationInFrames={cardLen} />
        </Sequence>
      ))}

      <Sequence from={durationInFrames - endLen} durationInFrames={endLen} layout="none">
        <EndCard phone={phone} website={website} />
      </Sequence>

      {musicSrc ? <Audio src={staticFile(musicSrc)} volume={0.6} /> : null}
    </AbsoluteFill>
  );
};
