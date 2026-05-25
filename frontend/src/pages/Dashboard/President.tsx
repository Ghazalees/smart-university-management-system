import { Card, CardBody, Switch, Divider } from "@nextui-org/react";
import {
  Users,
  AlertCircle,
  Cpu,
  Activity,
  ShieldCheck,
  Zap,
} from "lucide-react";

export const PresidentDashboard = () => {
  const metrics = [
    {
      label: "Total Users",
      value: "12,480",
      icon: <Users size={20} />,
      color: "text-primary",
    },
    {
      label: "Pending Requests",
      value: "342",
      icon: <AlertCircle size={20} />,
      color: "text-warning",
    },
    {
      label: "AI Accuracy",
      value: "98.2%",
      icon: <Cpu size={20} />,
      color: "text-secondary",
    },
    {
      label: "System Load",
      value: "42%",
      icon: <Activity size={20} />,
      color: "text-success",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-3xl font-bold tracking-tight">
          Executive Oversight
        </h1>
        <p className="text-default-500">
          Strategic monitoring of university performance, AI integration, and
          governance controls.
        </p>
      </header>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.label} className="border border-divider shadow-sm">
            <CardBody className="flex flex-row items-center gap-4 p-5">
              <div className={`rounded-xl bg-default-100 p-3 ${metric.color}`}>
                {metric.icon}
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-default-500">
                  {metric.label}
                </p>
                <h4 className="text-2xl font-bold text-foreground">
                  {metric.value}
                </h4>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Policy & Governance */}
      <Card className="border border-divider shadow-sm">
        <CardBody className="p-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2 text-primary">
              <ShieldCheck size={20} />
            </div>
            <h3 className="text-lg font-semibold text-foreground">
              Governance Controls
            </h3>
          </div>

          <div className="space-y-4">
            <GovernanceRow
              title="AI Auto-Approval for Workflow"
              description="Enable automated processing for low-risk administrative tasks."
              icon={<Zap size={18} className="text-primary" />}
            />
            <Divider />
            <GovernanceRow
              title="Restrict Access to Sensitive Data"
              description="Enforce strict role-based access control for institutional records."
              icon={<ShieldCheck size={18} className="text-secondary" />}
              defaultSelected
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

const GovernanceRow = ({
  title,
  description,
  icon,
  defaultSelected = false,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  defaultSelected?: boolean;
}) => (
  <div className="flex items-center justify-between gap-6">
    <div className="flex items-center gap-4">
      <div className="hidden rounded-lg bg-default-100 p-2 sm:block">
        {icon}
      </div>
      <div>
        <p className="font-medium text-foreground">{title}</p>
        <p className="text-sm text-default-500">{description}</p>
      </div>
    </div>
    <Switch color="primary" defaultSelected={defaultSelected} />
  </div>
);
