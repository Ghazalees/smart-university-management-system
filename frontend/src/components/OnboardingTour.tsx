/** Provides the reusable OnboardingTour interface component and accessibility behavior. */

import { useState } from "react";
import { Bot, Command, LayoutDashboard, Sparkles } from "lucide-react";
import { useExperiencePreferencesQuery, useUpdateExperiencePreferencesMutation } from "../services/api";
import { Button } from "./ui";

const steps = [
  { icon: LayoutDashboard, title: "A dashboard built for your role", copy: "Your priorities, classes, requests and insights are arranged around the permissions assigned to you." },
  { icon: Command, title: "Find anything with Ctrl + K", copy: "Global search respects object-level authorization while finding people, documents, classes and requests." },
  { icon: Bot, title: "Grounded AI with visible sources", copy: "AI responses expose citations, confidence and document freshness, and escalate when evidence is insufficient." },
];

export function OnboardingTour() {
  const { data, isLoading } = useExperiencePreferencesQuery();
  const [update] = useUpdateExperiencePreferencesMutation();
  const [step, setStep] = useState(0);
  if (isLoading || !data || data.data.onboarding_completed) return null;
  const current = steps[step]; const Icon = current.icon;
  async function complete() { await update({ onboarding_completed: true }).unwrap(); }
  return <div className="onboarding-backdrop"><section className="onboarding-card" role="dialog" aria-modal="true" aria-label="Welcome tour"><div className="onboarding-art"><span><Sparkles /></span><Icon /></div><div className="onboarding-content"><p className="eyebrow">Welcome to UniFlow</p><h2>{current.title}</h2><p>{current.copy}</p><div className="onboarding-dots" aria-label={`Step ${step + 1} of ${steps.length}`}>{steps.map((_, index) => <span key={index} className={index === step ? "active" : ""} />)}</div><footer><Button variant="ghost" onClick={() => void complete()}>Skip tour</Button>{step < steps.length - 1 ? <Button onClick={() => setStep((value) => value + 1)}>Continue</Button> : <Button onClick={() => void complete()}>Enter workspace</Button>}</footer></div></section></div>;
}
