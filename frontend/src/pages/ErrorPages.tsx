/** Renders the ErrorPages workspace and coordinates its API-driven interactions. */

import { ArrowLeft, Home, LockKeyhole, Map, Search, ShieldCheck } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

function ErrorSurface({ code, eyebrow, title, description, kind }: { code: string; eyebrow: string; title: string; description: string; kind: "forbidden" | "missing" }) {
  const navigate = useNavigate();
  return <main className={`error-page error-${kind}`}>
    <div className="error-orb error-orb-one" /><div className="error-orb error-orb-two" />
    <section className="error-panel">
      <div className="error-illustration"><span>{kind === "forbidden" ? <LockKeyhole /> : <Map />}</span><b>{code}</b><i>{kind === "forbidden" ? <ShieldCheck /> : <Search />}</i></div>
      <p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p>
      <div className="error-actions"><button className="button button-secondary" onClick={() => navigate(-1)}><ArrowLeft />Go back</button><Link className="button button-primary" to="/dashboard"><Home />Return to dashboard</Link></div>
      <small>UniFlow keeps navigation and API authorization aligned, so inaccessible resources are never exposed.</small>
    </section>
  </main>;
}

export function ForbiddenPage() { return <ErrorSurface code="403" eyebrow="Permission required" title="This workspace is protected." description="Your current university role does not grant access to this resource. Return to your dashboard or contact an administrator if your responsibilities have changed." kind="forbidden" />; }
export function NotFoundPage() { return <ErrorSurface code="404" eyebrow="Page not found" title="This campus path has moved." description="The address may be outdated, the resource may have been archived, or the link may contain a typo. Use global search or return to your workspace." kind="missing" />; }
