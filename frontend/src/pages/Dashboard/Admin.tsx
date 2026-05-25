import {
  Button,
  Card,
  CardBody,
  Chip,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@nextui-org/react";
import {
  Megaphone,
  FileText,
  Settings,
  PlusCircle,
  AlertCircle,
  Clock,
  CheckCircle2,
  Loader2,
} from "lucide-react";

export const AdminDashboard = () => {
  const workflows = [
    {
      id: 1,
      task: "Student Registration",
      status: "Pending",
      priority: "High",
    },
    { id: 2, task: "Course Approval", status: "Approved", priority: "Medium" },
    { id: 3, task: "Grade Submission", status: "In Progress", priority: "Low" },
    { id: 4, task: "Transcript Request", status: "Pending", priority: "High" },
  ];

  const statusColor = (status: string) => {
    switch (status) {
      case "Approved":
        return "success";
      case "In Progress":
        return "primary";
      case "Pending":
        return "warning";
      default:
        return "default";
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case "High":
        return "danger";
      case "Medium":
        return "warning";
      case "Low":
        return "success";
      default:
        return "default";
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      {/* Header */}
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Admin Operations
        </h1>
        <p className="max-w-2xl text-default-500">
          Centralized control for system workflows, approvals, and institutional
          documentation.
        </p>
      </header>

      {/* Top stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Pending Requests"
          value="18"
          icon={<AlertCircle size={18} />}
          colorClass="bg-warning/10 text-warning"
        />
        <StatCard
          label="In Progress"
          value="07"
          icon={<Loader2 size={18} />}
          colorClass="bg-primary/10 text-primary"
        />
        <StatCard
          label="Completed Today"
          value="24"
          icon={<CheckCircle2 size={18} />}
          colorClass="bg-success/10 text-success"
        />
        <StatCard
          label="Average Response"
          value="2h 14m"
          icon={<Clock size={18} />}
          colorClass="bg-secondary/10 text-secondary"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Workflow Section */}
        <div className="lg:col-span-2">
          <Card className="border border-divider shadow-sm">
            <CardBody className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">Active Workflows</h2>
                  <p className="text-sm text-default-500">
                    Track approvals, registrations, and official processing
                    tasks.
                  </p>
                </div>

                <Button
                  size="sm"
                  variant="flat"
                  color="primary"
                  startContent={<Settings size={16} />}
                >
                  Configure
                </Button>
              </div>

              <Table
                removeWrapper
                aria-label="Workflows table"
                classNames={{
                  wrapper: "bg-transparent shadow-none p-0",
                  thead: "bg-default-100/70",
                  th: "text-default-600 font-semibold uppercase text-xs tracking-wider",
                  td: "py-4",
                }}
              >
                <TableHeader>
                  <TableColumn>TASK</TableColumn>
                  <TableColumn>STATUS</TableColumn>
                  <TableColumn>PRIORITY</TableColumn>
                </TableHeader>

                <TableBody>
                  {workflows.map((wf) => (
                    <TableRow key={wf.id}>
                      <TableCell className="font-medium text-foreground">
                        {wf.task}
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="sm"
                          variant="flat"
                          color={statusColor(wf.status) as any}
                          className="font-medium"
                        >
                          {wf.status}
                        </Chip>
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="sm"
                          variant="flat"
                          color={priorityColor(wf.priority) as any}
                          className="font-medium"
                        >
                          {wf.priority}
                        </Chip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardBody>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card className="border border-divider bg-gradient-to-br from-primary/10 via-content1 to-secondary/10 shadow-sm">
            <CardBody className="gap-4 p-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-default-500">
                Quick Actions
              </h3>

              <Button
                color="primary"
                variant="solid"
                fullWidth
                startContent={<Megaphone size={18} />}
                className="justify-start font-medium"
              >
                Publish Notice
              </Button>

              <Button
                variant="flat"
                color="secondary"
                fullWidth
                startContent={<PlusCircle size={18} />}
                className="justify-start font-medium"
              >
                New Workflow
              </Button>
            </CardBody>
          </Card>

          <Card className="border border-divider shadow-sm">
            <CardBody className="gap-4 p-5">
              <h3 className="text-sm font-bold uppercase tracking-wider text-default-500">
                Documentation
              </h3>

              <div className="rounded-xl bg-default-100/70 p-3 transition-colors hover:bg-default-100">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2 text-primary">
                    <FileText size={18} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-foreground">
                      Policy Manual v2.4
                    </p>
                    <p className="text-xs text-default-400">
                      Last updated 2 days ago
                    </p>
                  </div>
                </div>
              </div>

              <Button
                variant="bordered"
                fullWidth
                className="border-default-200"
              >
                Manage All Documents
              </Button>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({
  label,
  value,
  icon,
  colorClass,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  colorClass: string;
}) => {
  return (
    <Card className="border border-divider shadow-sm">
      <CardBody className="flex flex-row items-center justify-between p-5">
        <div>
          <p className="text-sm text-default-500">{label}</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{value}</p>
        </div>
        <div className={`rounded-xl p-3 ${colorClass}`}>{icon}</div>
      </CardBody>
    </Card>
  );
};
