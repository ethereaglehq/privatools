import type { ReactNode } from "react";
import { KeyRound, SlidersHorizontal } from "lucide-react";
import "./account-workspace.css";

interface AccountWorkspaceHeaderProps {
    active: "settings" | "api";
    email: string;
    title: string;
    description?: string;
    actions?: ReactNode;
    embedded?: boolean;
}

/** The same two destinations stay visible across the signed-in account workspace. */
export default function AccountWorkspaceHeader({ active, email, title, description, actions, embedded = false }: AccountWorkspaceHeaderProps) {
    const Heading = embedded ? "h2" : "h1";
    return <header className="pt-account-workspace-header">
        <div className="pt-account-workspace-heading">
            <div className="pt-account-workspace-title">
                <p className="pt-workspace-caption">Your account</p>
                <Heading>{title}</Heading>
                {description && <p className="pt-account-workspace-description">{description}</p>}
            </div>
            <div className="pt-account-workspace-identity">
                <span className="pt-account-workspace-avatar" aria-hidden="true">{email.slice(0, 1).toUpperCase()}</span>
                <p><span>Signed in as</span><strong>{email}</strong></p>
            </div>
        </div>
        <div className="pt-account-workspace-toolbar">
            <nav className="pt-account-workspace-nav" aria-label="Account sections">
                <a href="/account/settings" aria-current={active === "settings" ? "page" : undefined}><SlidersHorizontal size={17} aria-hidden="true" /><span>Settings &amp; security</span></a>
                <a href="/account/keys" aria-current={active === "api" ? "page" : undefined}><KeyRound size={17} aria-hidden="true" /><span>API keys &amp; usage</span></a>
            </nav>
            {actions && <div className="pt-account-workspace-actions pt-inline-actions">{actions}</div>}
        </div>
    </header>;
}
