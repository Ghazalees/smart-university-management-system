import Hero from "./Hero";
import Features from "./Features";
import HowItWorks from "./HowItWorks";
import RoleViews from "./RoleViews";
import FinalCTA from "./FinalCTA";

export default function Landing() {
  return (
    <div className="bg-background">
      <Hero />
      <Features />
      <HowItWorks />
      <RoleViews />
      <FinalCTA />
    </div>
  );
}
