import { Card, CardBody, Button, Chip } from "@nextui-org/react";
import {
  BookOpen,
  Users,
  ChevronRight,
  GraduationCap,
  ClipboardList,
  TrendingUp,
} from "lucide-react";

export const ProfessorDashboard = () => {
  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      {/* Page Header */}
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Faculty Dashboard</h1>
        <p className="text-default-500">
          Welcome back, Professor. Here is your current course overview and
          action items.
        </p>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard
          label="Active Courses"
          value="4"
          icon={<BookOpen size={20} />}
          colorClass="text-primary"
        />
        <StatCard
          label="Pending Grades"
          value="12"
          icon={<ClipboardList size={20} />}
          colorClass="text-warning"
        />
        <StatCard
          label="Total Students"
          value="142"
          icon={<GraduationCap size={20} />}
          colorClass="text-secondary"
        />
      </div>

      {/* Course List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-default-700">
          Your Current Courses
        </h2>
        <div className="grid grid-cols-1 gap-4">
          <CourseCard
            title="CS101: Intro to Computer Science"
            students={30}
            status="Active"
          />
          <CourseCard
            title="CS202: Data Structures"
            students={45}
            status="Active"
          />
        </div>
      </div>
    </div>
  );
};

// Enhanced Stat Component
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
}) => (
  <Card className="border border-divider shadow-sm">
    <CardBody className="flex flex-row items-center justify-between p-5">
      <div>
        <p className="text-sm text-default-500">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
      <div className={`rounded-xl bg-default-100 p-3 ${colorClass}`}>
        {icon}
      </div>
    </CardBody>
  </Card>
);

const CourseCard = ({
  title,
  students,
  status,
}: {
  title: string;
  students: number;
  status: string;
}) => (
  <Card className="border border-divider shadow-sm transition-all hover:border-primary/50">
    <CardBody className="flex flex-row items-center justify-between p-6">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <TrendingUp size={24} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          <div className="flex items-center gap-3 mt-1">
            <span className="flex items-center gap-1.5 text-sm text-default-500">
              <Users size={14} /> {students} Enrolled
            </span>
            <Chip
              size="sm"
              color="success"
              variant="flat"
              className="text-[11px] font-medium"
            >
              {status}
            </Chip>
          </div>
        </div>
      </div>
      <Button
        color="primary"
        variant="flat"
        endContent={<ChevronRight size={16} />}
      >
        Manage Course
      </Button>
    </CardBody>
  </Card>
);
