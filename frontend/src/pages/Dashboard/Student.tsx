import {
  Card,
  CardBody,
  Chip,
  Progress,
  Button,
  Avatar,
  Divider,
} from "@nextui-org/react";

export const StudentDashboard = () => {
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between p-6  rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-3xl font-extrabold ">Dashboard</h1>
          <p className="text-slate-500">Track your academic success.</p>
        </div>
        <Avatar name="Alex" className="bg-indigo-500 text-white" />
      </div>

      {/* Manual Color Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="GPA"
          value="3.8"
          gradient="from-indigo-500 to-violet-600"
        />
        <StatCard
          title="Credits"
          value="84"
          gradient="from-emerald-500 to-teal-600"
        />
        <StatCard
          title="Upcoming"
          value="3"
          gradient="from-amber-500 to-orange-600"
        />
      </div>

      {/* Course List */}
      <Card className="p-2">
        <CardBody className="gap-6">
          <CourseRow name="Data Structures" progress={75} color="indigo" />
          <CourseRow name="Web Development" progress={90} color="emerald" />
          <CourseRow name="Database Systems" progress={45} color="amber" />
        </CardBody>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button className="bg-indigo-600 rounded-md">View Grades</Button>
        <Button className="bg-emerald-600 ">Register</Button>
        <Button className="bg-slate-800 text-white">Library</Button>
      </div>
    </div>
  );
};

const StatCard = ({
  title,
  value,
  gradient,
}: {
  title: string;
  value: string;
  gradient: string;
}) => (
  <Card className={`bg-gradient-to-br ${gradient} text-white rounded-md`}>
    <CardBody className="p-6">
      <p className="text-white/80 font-medium">{title}</p>
      <h3 className="text-4xl font-black mt-1">{value}</h3>
    </CardBody>
  </Card>
);

const CourseRow = ({
  name,
  progress,
  color,
}: {
  name: string;
  progress: number;
  color: "indigo" | "emerald" | "amber";
}) => {
  // Define the map of Tailwind classes
  const colorMap = {
    indigo: {
      chip: "bg-indigo-100 text-indigo-700",
      bar: "bg-indigo-500",
    },
    emerald: {
      chip: "bg-emerald-100 text-emerald-700",
      bar: "bg-emerald-500",
    },
    amber: {
      chip: "bg-amber-100 text-amber-700",
      bar: "bg-amber-500",
    },
  };

  const colors = colorMap[color];

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="font-semibold text-slate-700">{name}</span>
        {/* Now these classes exist in the build */}
        <Chip className={`font-bold`}>{progress}%</Chip>
      </div>
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${colors.bar} rounded-full`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
