import { useGetMeQuery } from "../states/api/authApi";

export const Dashboard = () => {
  const { data, error, isLoading } = useGetMeQuery();

  if (isLoading) {
    return <div>Loading user data...</div>;
  }

  if (error) {
    return <div>Failed to load user info. You may not be authenticated.</div>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {data?.data.username}</p>
      <p>Email: {data?.data.email}</p>
      <p>Role: {data?.data.role}</p>
    </div>
  );
};
