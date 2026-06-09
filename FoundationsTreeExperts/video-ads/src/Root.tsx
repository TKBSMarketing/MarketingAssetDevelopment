import "./index.css";
import { Composition } from "remotion";
import { TestimonialReel, testimonialReelDefaults } from "./TestimonialReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* B1 — Testimonial Reel · Foundations Tree Experts · 9:16 Stories/Reels */}
      <Composition
        id="B1-TestimonialReel"
        component={TestimonialReel}
        durationInFrames={420}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={testimonialReelDefaults}
      />

      {/* Same composition, 4:5 Feed crop — render with --props to reuse one template */}
      <Composition
        id="B1-TestimonialReel-Feed"
        component={TestimonialReel}
        durationInFrames={420}
        fps={30}
        width={1080}
        height={1350}
        defaultProps={testimonialReelDefaults}
      />
    </>
  );
};
